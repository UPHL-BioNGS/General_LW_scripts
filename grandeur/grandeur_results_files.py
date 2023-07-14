#!/usr/bin/env python3

'''
Author: Erin Young

Description:

This script will collect needed files to get results from Grandeur for 
1. The 'Finished' tab (will be discontinued in the future)
2. As a lookup table for the 'ARLN' tab
3. As input for Labware 8 for 
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
# ARLN needs 'WGS MLST', 'AMR genes', 'Virulence genes'
arln_cols     = ['wgs_id', 'organism', 'coverage', 'mlst', 'Sample_Project', 'amr genes', 'virulence genes']

print('Getting samples from ' + args.samplesheet)
if os.path.exists(args.samplesheet):
    # get all the samples from the sample sheet into a pandas dataframe
    df            = pd.read_csv(args.samplesheet, skiprows=18)
    df['lims_id'] = df['Sample_ID'].str.replace(  '-UT.*','', regex=True)
    df['wgs_id']  = df['Sample_Name'].str.replace('-UT.*','', regex=True)
else:
    print('Sample sheet could not be located! (Specify with -s)')
    exit(1)

# Getting the WGS organism from fastani or mash
if os.path.exists(fastani):
    print('Getting the top organism from fastani at ' + fastani)
    fastani_df             = pd.read_csv(fastani)
    fastani_df             = fastani_df.sort_values(by=['ANI estimate'], ascending = False)
    fastani_df             = fastani_df.drop_duplicates(subset=['sample'], keep = 'first')
    fastani_df['organism'] = fastani_df['reference'].str.replace('_GC.*', '', regex = True)

    df = pd.merge(df,fastani_df[['sample','organism']],left_on='Sample_Name', right_on='sample', how='left')
    df = df.drop('sample', axis=1)
elif os.path.exists(mash):
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
if os.path.exists(seqsero2):
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


df['Pass'] = 'TBD'
df.loc[df['coverage'] >= 40, 'Pass'] = 'Y'
df.loc[df['coverage'] < 20,  'Pass'] = 'X'
df.loc[(df['organism'].str.contains('Shigella', na=False))      & (df['coverage'] >= 40), 'Pass'] = 'Y'
df.loc[(df['organism'].str.contains('Shigella', na=False))      & (df['coverage'] <  40), 'Pass'] = 'X'
df.loc[(df['organism'].str.contains('Escherichia', na=False))   & (df['coverage'] >= 40), 'Pass'] = 'Y'
df.loc[(df['organism'].str.contains('Escherichia', na=False))   & (df['coverage'] <  40), 'Pass'] = 'X'
df.loc[(df['organism'].str.contains('Salmonella', na=False))    & (df['coverage'] >= 30), 'Pass'] = 'Y'
df.loc[(df['organism'].str.contains('Salmonella', na=False))    & (df['coverage'] <  30), 'Pass'] = 'X'
df.loc[(df['organism'].str.contains('Campylobacter', na=False)) & (df['coverage'] >= 20), 'Pass'] = 'Y'
df.loc[(df['organism'].str.contains('Campylobacter', na=False)) & (df['coverage'] <  20), 'Pass'] = 'X'

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

# LIMS_TEST_ID, Run Name, Genomic Coverage, AMR Gene symbol, AMR Name of closest sequence, AMR % Coverage of reference sequence, AMR % Identity to reference sequence,Virulence Gene symbol	Virulence Name of closest sequence, Virulence % Coverage of reference sequence, Virulence % Identity to reference sequence, SerotypeFInder (E. coli), SeqSero Organism (Salmonella), Run Name, Genomic Coverage, Passed QC, Shiga toxin genes identified, Allelle Code, Rep Code, PNUSA Accession, BioSample Accession, Date Uploaded to CDC, Date Uploaded to NCBI/SRA, Passed PulseNet QC
pulsenet_labware_cols = ['LIMS_TEST_ID', 'Passed QC', 'PNUSA Accession', 'Run Name', 'Genomic Coverage', 'AMR Gene symbol', 'AMR Name of closest sequence', 'AMR % Coverage of reference sequence', 'AMR % Identity to reference sequence','Virulence Gene symbol',	'Virulence Name of closest sequence', 'Virulence % Coverage of reference sequence', 'Virulence % Identity to reference sequence', 'SerotypeFInder (E. coli)', 'SeqSero Organism (Salmonella)', 'Shiga toxin genes identified', 'Allelle Code', 'Rep Code', 'BioSample Accession', 'Date Uploaded to CDC', 'Date Uploaded to NCBI/SRA', 'Passed PulseNet QC']

# LIMS_TEST_ID, Passed QC, ARLN WGS ID, WGS Organism, WGS MLST, Run Name, Genomic Coverage, AMR Gene symbol, AMR Name of closest sequence,AMR % Coverage of reference sequence,AMR % Identity to reference sequence,Virulence Gene symbol,Virulence Name of closest sequence,Virulence % Coverage of reference sequence, Virulence % Identity to reference sequence, SRA Accession, BioSample Accession, Genbank Accession, GC WGS ID, GC Percent, Avg PHRED, Clade
arln_labware_cols  = ['LIMS_TEST_ID', 'Passed QC', 'ARLN WGS ID', 'GC WGS ID', 'WGS Organism', 'WGS MLST', 'Run Name', 'Genomic Coverage', 'AMR Gene symbol', 'AMR Name of closest sequence', 'AMR % Coverage of reference sequence', 'AMR % Identity to reference sequence', 'Virulence Gene symbol', 'Virulence Name of closest sequence', 'Virulence % Coverage of reference sequence', 'Virulence % Identity to reference sequence', 'SRA Accession', 'BioSample Accession', 'Genbank Accession', 'GC Percent', 'Avg PHRED', 'Clade']

# LIMS_TEST_ID,WGS Organism,Passed QC,Run Name,Subtype
alt_labware_cols = ['LIMS_TEST_ID', 'WGS Organism', 'Passed QC', 'Run Name', 'Subtype']

# creating columns for unused values 'SRA Accession', 'BioSample Accession', 'Genbank Accession', 'GC WGS ID', 'GC Percent', 'Avg PHRED', 'Clade'
optional_columns = [
    'ARLN WGS ID', 
    'SRA Accession', 
    'BioSample Accession', 
    'Genbank Accession', 
    'GC WGS ID', 
    'GC Percent', 
    'Avg PHRED', 
    'Clade', 
    'AMR Gene symbol', 
    'AMR Name of closest sequence', 
    'AMR % Coverage of reference sequence', 
    'AMR % Identity to reference sequence', 
    'Virulence Gene symbol',
    'Virulence Name of closest sequence',
    'Virulence % Coverage of reference sequence', 
    'Virulence % Identity to reference sequence', 
    'SerotypeFInder (E. coli)', 
    'SeqSero Organism (Salmonella)', 
    'Shiga toxin genes identified',
    'PNUSA Accession', 
    'Allelle Code', 
    'Rep Code', 
    'Date Uploaded to CDC', 
    'Date Uploaded to NCBI/SRA', 
    'Passed PulseNet QC',
    'Subtype' ]

for unused in optional_columns:
    if unused not in df.columns:
        df[unused] = ''

# getting final columns 'LIMS_TEST_ID', 'Passed QC', 'ARLN WGS ID', 'WGS Organism', 'WGS MLST', 'Run Name', 'Genomic Coverage', GC WGS ID
df['LIMS_TEST_ID']                  = df['lims_id']
df['Passed QC']                     = df['Pass']
df['WGS Organism']                  = df['organism']
df['WGS MLST']                      = df['mlst']
df['Run Name']                      = df['Sample_Project']
df['Genomic Coverage']              = df['coverage']

sample_list = []

if args.list and os.path.exists(args.list) :
    print("Creating files for subset of samples")
    with open(args.list) as f:
        sample_list = f.read().splitlines()
else:
    print("Creating Labware 8 files for each sample")
    sample_list = df['LIMS_TEST_ID'].to_list()

if not os.path.exists("labware8"):
    os.mkdir("labware8")

for sample in sample_list:
    sample_df       = df[df['LIMS_TEST_ID'] == sample ].copy()
    sample_name     = sample_df['wgs_id'].values[0]
    sample_organism = sample_df['WGS Organism'].values[0]
    print("Getting results for " + sample + " / " + sample_name + " (" + sample_organism + ")" )
    if 'GC' in sample_name:
        sample_df['GC WGS ID'] = sample_df['wgs_id']
    elif 'CK' in sample_name:
        sample_df['ARLN WGS ID'] = sample_df['wgs_id']
    #elif 'PNUSA' in sample_name:
    #    sample_df['PNUSA Accession'] = sample_df['wgs_id']

    #  'AMR Gene symbol', 'AMR Name of closest sequence', 'AMR % Coverage of reference sequence', 'AMR % Identity to reference sequence'
    sample_amr_df = amrfinder_df[amrfinder_df['Element type'] == 'AMR'].copy()
    sample_amr_df = sample_amr_df[sample_amr_df['Name'] == sample_name]
    sample_amr_df['AMR Gene symbol'] = sample_amr_df['Gene symbol']
    sample_amr_df['AMR Name of closest sequence'] = sample_amr_df['Name of closest sequence']
    sample_amr_df['AMR % Coverage of reference sequence'] = sample_amr_df['% Coverage of reference sequence']
    sample_amr_df['AMR % Identity to reference sequence'] = sample_amr_df['% Identity to reference sequence']
    sample_amr_df['LIMS_TEST_ID'] = sample
    sample_amr_df = sample_amr_df[['LIMS_TEST_ID', 'AMR Gene symbol','AMR Name of closest sequence','AMR % Coverage of reference sequence', 'AMR % Identity to reference sequence']]

    #  Virulence Gene symbol,Virulence Name of closest sequence,Virulence % Coverage of reference sequence, Virulence % Identity to reference sequence
    sample_vir_df = amrfinder_df[amrfinder_df['Element type'] == 'VIRULENCE'].copy()
    sample_vir_df = sample_vir_df[sample_vir_df['Name'] == sample_name]
    sample_vir_df['Virulence Gene symbol']                      = sample_vir_df['Gene symbol']
    sample_vir_df['Virulence Name of closest sequence']         = sample_vir_df['Name of closest sequence']
    sample_vir_df['Virulence % Coverage of reference sequence'] = sample_vir_df['% Coverage of reference sequence']
    sample_vir_df['Virulence % Identity to reference sequence'] = sample_vir_df['% Identity to reference sequence']
    sample_vir_df['LIMS_TEST_ID']                               = sample
    sample_vir_df                                               = sample_vir_df[['LIMS_TEST_ID', 'Virulence Gene symbol','Virulence Name of closest sequence','Virulence % Coverage of reference sequence', 'Virulence % Identity to reference sequence']]

    # shiga toxin genes
    sample_stx_df = amrfinder_df[amrfinder_df['Gene symbol'].str.contains("(?i)stx|eae")]
    sample_stx_df = sample_stx_df[sample_stx_df['Name'] == sample_name]
    sample_stx_df['LIMS_TEST_ID']                 = sample
    sample_stx_df['Shiga toxin genes identified'] = sample_stx_df['Gene symbol']
    sample_stx_df                                 = sample_stx_df[['LIMS_TEST_ID', 'Shiga toxin genes identified']]

    # for known alt-ngs projects
    if "Legionella" in sample_organism:
        sample_df['Subtype'] = sample_df['mlst']
    elif "pyogenes" in sample_organism:
        sample_df['Subtype'] = sample_df['emmtyper_Predicted_emm-type']

    # writing the files
    result = pd.concat([sample_df, sample_amr_df, sample_vir_df, sample_stx_df])
    result.to_csv('labware8/arln_'     + sample + '_results.tsv', columns = arln_labware_cols ,    index=False, sep = '\t' )
    result.to_csv('labware8/pulsenet_' + sample + '_results.tsv', columns = pulsenet_labware_cols, index=False, sep = '\t' )
    result.to_csv('labware8/altngs_'   + sample + '_results.tsv', columns = alt_labware_cols,      index=False, sep = '\t' )