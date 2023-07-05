#!/usr/bin/env python3

'''
Author: Erin Young

Description:

This script will collect needed files to get results from Grandeur for 
1. The 'Finished' tab (will be discontinued in the future)
2. As a lookup table for the 'ARLN' tab
3. As a lookup table for the 'GC' tab - currently not needed
4. As input for Labware 8 for 
  a. ALT-NGS
  b. ARLN samples
  c. GC samples
  d. pulsenet samples

(Yes, that is potentially seven files)

EXAMPLE:
python3 grandeur_results_files.py -g <path to grandeur results> -s <input sample sheet>
'''

# trying to keep dependencies really low
import argparse
import pandas as pd
import os
from os.path import exists

version = '0.0.20230710'

parser = argparse.ArgumentParser()
parser.add_argument('-g', '--grandeur',    type=str, help='directory where Grandeur has output results', default='grandeur')
parser.add_argument('-s', '--samplesheet', type=str, help='sample sheet for run',                        default='SampleSheet.csv')
parser.add_argument('-l', '--list',        type=str, help='list of samples for LabWare 8 upload',        default='')
parser.add_argument('-v', '--version',               help='print version and exit', action='version', version='%(prog)s ' + version)
args   = parser.parse_args()

# the files in the grandeur output directory
amrfinder  = args.grandeur + '/ncbi-AMRFinderplus/amrfinderplus.txt'
fastani    = args.grandeur + '/fastani/fastani_summary.csv'
mash       = args.grandeur + '/mash/mash_summary.csv'
mlst       = args.grandeur + '/mlst/mlst_summary.tsv'
seqsero2   = args.grandeur + '/seqsero2/seqsero2_results.txt'
summary    = args.grandeur + '/grandeur_summary.tsv'

# using results in summary file instead of the "original"
# blobtools      = args.grandeur + '/blobtools/blobtools_summary.txt'
# kraken2        = args.grandeur + '/kraken2/kraken2_summary.csv'
# serotypefinder = args.grandeur + '/serotypefinder/serotypefinder_results.txt'
# shigatyper     = args.grandeur + '/shigatyper/shigatyper_results.txt'

# columns for final files
# For the results tab : top organism, serotypefinder/shigellatyper, seqsero2, coverage, warnings, blobtools, and kraken2
finished_cols = ['wgs_id', 'organism', 'SerotypeFinder (E. coli)', 'SeqSero Organism (Salmonella)', 'Sample_Project', 'coverage', 'Pass', 'warnings']
# needs 'WGS MLST', 'AMR genes', 'Virulence genes'
arln_cols     = ['wgs_id', 'organism', 'coverage', 'mlst', 'Sample_Project', 'amr genes', 'virulence genes']

print('Getting samples from ' + args.samplesheet)
if exists(args.samplesheet):
    # get all the samples from the sample sheet into a pandas dataframe
    df            = pd.read_csv(args.samplesheet, skiprows=18)
    df['lims_id'] = df['Sample_ID'].str.replace(  '-UT.*','', regex=True)
    df['wgs_id']  = df['Sample_Name'].str.replace('-UT.*','', regex=True)
else:
    print('Sample sheet could not be located! (Specify with -s)')
    exit(1)

# Getting the WGS organism from fastani or mash
if exists(fastani):
    print('Getting the top organism from fastani at ' + fastani)
    fastani_df             = pd.read_csv(fastani)
    fastani_df             = fastani_df.sort_values(by=['ANI estimate'], ascending = False)
    fastani_df             = fastani_df.drop_duplicates(subset=['sample'], keep = 'first')
    fastani_df['organism'] = fastani_df['reference'].str.replace('_GC.*', '', regex = True)

    df = pd.merge(df,fastani_df[['sample','organism']],left_on='Sample_Name', right_on='sample', how='left')
    df = df.drop('sample', axis=1)
elif exists(mash):
    print("fastani results could not be found!")
    print("Getting the top organism from mash at " + mash)
    mash_df = pd.read_csv(mash)
    mash_df = mash_df.sort_values(by=['P-value', 'mash-distance'])
    mash_df = mash_df.drop_duplicates(subset=['sample'], keep = 'first')
    
    df = pd.merge(df,mash_df[['sample','organism']],left_on='Sample_Name', right_on='sample', how='left')
    df = df.drop('sample', axis=1)
else:
    print('FATAL: fastani and mash results could not be found in the subdirectory of ' + args.grandeur )
    print('Please specify grandeur output with -g')
    exit(1)

# Getting Salmonella seroptying information from seqsero2
if exists(seqsero2):
    print('Getting salmonella serotype information from ' + seqsero2)
    seqsero2_df = pd.read_table(seqsero2)
    seqsero2_df['SeqSero Organism (Salmonella)'] = 'Salmonella enterica serovar ' + seqsero2_df['Predicted serotype'] + ':' + seqsero2_df['Predicted antigenic profile']

    df = pd.merge(df,seqsero2_df[['sample','SeqSero Organism (Salmonella)']],left_on='Sample_Name', right_on='sample', how='left')
    df = df.drop('sample', axis=1)
else:
    df['SeqSero Organism (Salmonella)'] = ''

print('Extracting information from ' + summary)
# getting coverage
summary_df     = pd.read_table(summary)
df             = pd.merge(df,summary_df[['sample','coverage','warnings']],left_on='Sample_Name', right_on='sample', how='left')
df             = df.drop('sample', axis=1)
df['coverage'] = df['coverage'].fillna(0)
df['coverage'] = df['coverage'].round(2)

# getting O and H groups
if 'serotypefinder_Serotype_O' in summary_df.columns:
    if 'shigatyper_Hit' and 'mash_organism' in summary_df.columns:
        print('Double checking E. coli organism with shigatyper results')
        ecoli_df = summary_df[summary_df['mash_organism'].str.contains('Shigella', na=False) | summary_df['mash_organism'].str.contains('Escherichia', na=False) ].copy()
        ecoli_df['serotypefinder_Serotype_O'] = ecoli_df['serotypefinder_Serotype_O'].fillna("none")
        ecoli_df['serotypefinder_Serotype_H'] = ecoli_df['serotypefinder_Serotype_H'].fillna("none")
        ecoli_df['ecoli_organism'] = "Escherichia coli"
        ecoli_df.loc[ecoli_df['shigatyper_Hit'].str.contains('ipaH'), 'ecoli_organism'] = 'Shigella'
        ecoli_df['SerotypeFinder (E. coli)'] = ecoli_df['ecoli_organism'] + " " + ecoli_df['serotypefinder_Serotype_O'] + ":" + ecoli_df['serotypefinder_Serotype_H']

        df = pd.merge(df,ecoli_df[['sample','SerotypeFinder (E. coli)']],left_on='Sample_Name', right_on='sample', how='left')
        df = df.drop('sample', axis=1)
    else:
        summary_df['SerotypeFinder (E. coli)'] = summary_df['serotypefinder_Serotype_O'] + ":" + summary_df['serotypefinder_Serotype_H']
        
        df = pd.merge(df,summary_df[['sample','SerotypeFinder (E. coli)']],left_on='Sample_Name', right_on='sample', how='left')
        df = df.drop('sample', axis=1)
else:
    df['SerotypeFinder (E. coli)'] = ''

# getting kraken2 results
if 'kraken2_organism_(per_fragment)' in summary_df.columns:
    df = pd.merge(df,summary_df[['sample','kraken2_organism_(per_fragment)']],left_on='Sample_Name', right_on='sample', how='left')
    df = df.drop('sample', axis=1)
    finished_cols = finished_cols + ['kraken2_organism_(per_fragment)']
    arln_cols     = arln_cols     + ['kraken2_organism_(per_fragment)']

if 'blobtools_organism_(per_mapped_reads)' in summary_df.columns:
    df = pd.merge(df,summary_df[['sample','blobtools_organism_(per_mapped_reads)']],left_on='Sample_Name', right_on='sample', how='left')
    df = df.drop('sample', axis=1)
    finished_cols = finished_cols + ['blobtools_organism_(per_mapped_reads)']
    arln_cols     = arln_cols     + ['blobtools_organism_(per_mapped_reads)']

def pass_fail(df):
    if (df['coverage'] < 20 ):
        return 'X'
    elif (df['coverage'] >= 40):
        return 'Y'
    elif (df['coverage'] >=20 ) and ('Campy' in df['organism']):
        return 'Y'
    elif (df['coverage'] < 40) and ('Shigella' in df['organism']):
        return 'X'
    elif (df['coverage'] < 40) and ('Escherichia' in df['organism']):
        return 'X'
    elif (df['coverage'] < 30) and (df['organism'] == 'Salmonella_enterica'):
        return 'X'
    else:
        return 'TBD'
    
df['Pass']     = df.apply(pass_fail, axis = 1)
df             = df.sort_values('wgs_id')
df['organism'] = df['organism'].str.replace('_',' ',regex=False)

if not args.list:
    print('Writing file for Finished tab')
    df.to_csv('finished_tab.tsv', columns = finished_cols, index=False, sep = '\t' )
    df.to_csv('finished_tab.txt', columns = finished_cols, index=False, sep = ';' )
    print('Created finished_tab.{txt,tsv}')

print('Getting additional information for ARLN tab')

print('Getting MLST information from ' + mlst)
mlst_df         = pd.read_table(mlst)
mlst_df['mlst'] = mlst_df['matching PubMLST scheme'] + ':' + mlst_df['ST']
df              = pd.merge(df,mlst_df[['sample','mlst']],left_on='Sample_Name', right_on='sample', how='left')
df              = df.drop('sample', axis=1)

print('Getting virulence and AMR genes from ' + amrfinder)
amrfinder_df              = pd.read_table(amrfinder)
amrfinder_df              = amrfinder_df.sort_values('Gene symbol')

amr_df                    = amrfinder_df[amrfinder_df['Element type'] == 'AMR'].copy()
amr_df                    = amr_df.groupby('Name', as_index=False).agg({'Gene symbol': lambda x: list(x)})
amr_df['amr genes']       = amr_df['Gene symbol']
df                        = pd.merge(df,amr_df[['Name','amr genes']],left_on='Sample_Name', right_on='Name', how='left')
df                        = df.drop('Name', axis=1)

vir_df                    = amrfinder_df[amrfinder_df['Element type'] == 'VIRULENCE'].copy()
vir_df                    = vir_df.groupby('Name', as_index=False).agg({'Gene symbol': lambda x: list(x)})
vir_df['virulence genes'] = vir_df['Gene symbol']
df                        = pd.merge(df,vir_df[['Name','virulence genes']],left_on='Sample_Name', right_on='Name', how='left')
df                        = df.drop('Name', axis=1)

if not args.list:
    print('Writing file for ARLN tab')
    df.to_csv('arln_tab.tsv', columns = arln_cols, index=False, sep = '\t' )
    df.to_csv('arln_tab.txt', columns = arln_cols, index=False, sep = ';' )
    print('Created arln_tab.{txt,tsv}')

# now for the labware 8

# columns for pulsenet
# LIMS_TEST_ID, Run Name, Genomic Coverage, AMR Gene symbol, AMR Name of closest sequence, AMR % Coverage of reference sequence, AMR % Identity to reference sequence,Virulence Gene symbol	Virulence Name of closest sequence, Virulence % Coverage of reference sequence, Virulence % Identity to reference sequence, SerotypeFInder (E. coli), SeqSero Organism (Salmonella), Run Name, Genomic Coverage, Passed QC, Shiga toxin genes identified, Allelle Code, Rep Code, PNUSA Accession, BioSample Accession, Date Uploaded to CDC, Date Uploaded to NCBI/SRA, Passed PulseNet QC

# columns for arln:
# LIMS_TEST_ID, Passed QC, ARLN WGS ID, WGS Organism, WGS MLST, Run Name, Genomic Coverage, AMR Gene symbol, AMR Name of closest sequence,AMR % Coverage of reference sequence,AMR % Identity to reference sequence,Virulence Gene symbol,Virulence Name of closest sequence,Virulence % Coverage of reference sequence, Virulence % Identity to reference sequence, SRA Accession, BioSample Accession, Genbank Accession, GC WGS ID, GC Percent, Avg PHRED, Clade
arln_labware_cols  = ['LIMS_TEST_ID', 'Passed QC', 'ARLN WGS ID', 'WGS Organism', 'WGS MLST', 'Run Name', 'Genomic Coverage', 'AMR Gene symbol', 'AMR Name of closest sequence', 'AMR % Coverage of reference sequence', 'AMR % Identity to reference sequence', 'Virulence Gene symbol', 'Virulence Name of closest sequence', 'Virulence % Coverage of reference sequence', 'Virulence % Identity to reference sequence', 'SRA Accession', 'BioSample Accession', 'Genbank Accession', 'GC WGS ID', 'GC Percent', 'Avg PHRED', 'Clade']
df['LIMS_TEST_ID'] = df['lims_id']

# GC samples

# columns for alt-ngs
# LIMS_TEST_ID, WGS Organism, Passed QC, Run Name, Subtype


if args.list:
    print("creating one file for passing samples")
else:
    if not exists("labware8"):
        os.mkdir("labware8", exist_ok = True)
    print("Creating Labware 8 files for each sample in labware 8")
