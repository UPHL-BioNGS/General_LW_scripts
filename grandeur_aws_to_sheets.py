#!/usr/bin/env python3

'''
Author: Erin Young

Description:

This script will collect needed files to get results from Grandeur for 
1. The 'Finished' tab (will be discontinued in the future)
2. As a lookup table for the 'ARLN' tab

EXAMPLE:
python3 grandeur_aws_to_sheets.py -g <path to grandeur results> -s <input sample sheet>
'''

# trying to keep dependencies really low
import argparse
import pandas as pd
import os
import logging
import glob

# local files
from read_miseq_sample_sheet import read_miseq_sample_sheet

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt = '%y-%b-%d %H:%M:%S')

def sample_sheet_to_df(samplesheet):
    logging.info(f"Getting samples from {samplesheet}")

    if os.path.exists(samplesheet):
        # get all the samples from the sample sheet into a pandas dataframe
        df            = read_miseq_sample_sheet(samplesheet, "sample_id")
        df['lims_id'] = df['Sample_ID'].str.replace(  '-UT.*','', regex=True)
        df['wgs_id']  = df['Sample_Name'].str.replace('-UT.*','', regex=True)

        return df
    
    else:
        logging.fatal('Sample sheet could not be located! (Specify with -s)')
        exit(1)

def amrfinder_results(df, args):
    amrfinder_dir = args.grandeur + '/ncbi-AMRFinderplus/'
    
    if not os.path.isdir(amrfinder_dir):
        return df
    
    logging.info('Getting virulence and AMR genes from ' + amrfinder_dir)
    dfs = []
    for filename in os.listdir(amrfinder_dir):
        if filename.endswith("_amrfinder_plus.txt"):
            filepath = os.path.join(amrfinder_dir, filename)
            ind_df = pd.read_csv(filepath)
            if not ind_df.empty:
                dfs.append(ind_df)

    if dfs:
        amrfinder_df = pd.concat(dfs, ignore_index=True)
    else:
        return df

    if not amrfinder_df.empty:
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
    
    return df

def create_files(df):
    # columns for final files
    # For the results tab : top organism, serotypefinder/shigellatyper, seqsero2, coverage, warnings, blobtools, and kraken2
    finished_cols = ['wgs_id', 'Description', 'organism', 'SerotypeFinder (E. coli)', 'SeqSero Organism (Salmonella)', 'Sample_Project', 'coverage', 'Pass', 'warnings', 'blobtools_organism_(per_mapped_reads)']
    # ARLN needs 'WGS MLST', 'AMR genes', 'Virulence genes'
    arln_cols     = ['wgs_id', 'Description', 'organism', 'coverage', 'mlst', 'emm type', 'Sample_Project', 'amr genes', 'virulence genes', 'kraken2_organism_(per_fragment)', 'blobtools_organism_(per_mapped_reads)']

    for col in finished_cols + arln_cols:
        if col not in df.columns:
            df[col] = None


    df = df.fillna('')
    df = df.sort_values('wgs_id')

    logging.info('Writing file for Finished tab')
    df.to_csv('finished_tab.tsv', columns = finished_cols, index=False, sep = '\t' )
    df.to_csv('finished_tab.txt', columns = finished_cols, index=False, sep = ';' )
    logging.info('Created finished_tab.{txt,tsv}')

    logging.info('Writing file for ARLN tab')
    df.to_csv('arln_tab.tsv', columns = arln_cols, index=False, sep = '\t' )
    df.to_csv('arln_tab.txt', columns = arln_cols, index=False, sep = ';' )
    logging.info('Created arln_tab.{txt,tsv}')


def emmtyper_results(df, args):
    emmtyper_dir      = args.grandeur + '/emmtyper/'

    if not os.path.isdir(emmtyper_dir):
        return df

    logging.info('Getting emmtyper information from ' + emmtyper_dir)

    dfs = []

    for filename in os.listdir(emmtyper_dir):
        if filename.endswith("mlst.tsv"):
            filepath = os.path.join(emmtyper_dir, filename)
            ind_df = pd.read_table(filepath, sep="\t")
            if not ind_df.empty:
                dfs.append(ind_df)

    if dfs:
        emmtyper_df = pd.concat(dfs, ignore_index=True)
    else:
        return df

    if not emmtyper_df.empty:
        emmtyper_df['mlst'] = mlst_df['matching PubMLST scheme'] + ':' + mlst_df['ST'].astype('str')
        df              = pd.merge(df,emmtyper_df[['sample','mlst']],left_on='Sample_Name', right_on='sample', how='left')
        df              = df.drop('sample', axis=1)

    return df


def fastani_results(df, args):
    fastani_dir   = args.grandeur + '/fastani/'
    
    if not os.path.isdir(fastani_dir):
        return df
    
    logging.info('Getting the top organism from fastani at ' + fastani_dir)
    dfs = []
    for filename in os.listdir(fastani_dir):
        if filename.endswith("_fastani.csv"):
            filepath = os.path.join(fastani_dir, filename)
            ind_df = pd.read_csv(filepath)
            if not ind_df.empty:
                dfs.append(ind_df)

    if dfs:
        fastani_df = pd.concat(dfs, ignore_index=True)
    else:
        return df

    # Getting the WGS organism from fastani or mash
    if not fastani_df.empty:
        fastani_df             = fastani_df[fastani_df['ANI estimate'] >= 0.9]
        fastani_df             = fastani_df.sort_values(by=['ANI estimate'], ascending = False)
        fastani_df             = fastani_df.drop_duplicates(subset=['sample'], keep = 'first')
        fastani_df['organism'] = fastani_df['reference'].str.replace('_GC.*', '', regex = True)

        df = pd.merge(df,fastani_df[['sample','organism']],left_on='Sample_Name', right_on='sample', how='left')
        df = df.drop('sample', axis=1)

    return df


def grandeur_summary(df, args):
    summary       = args.grandeur + '/grandeur_summary.tsv'
    logging.info('Extracting information from ' + summary)

    # using results in summary file instead of the "original"
    # blobtools      = args.grandeur + '/blobtools/blobtools_summary.txt'
    # kraken2        = args.grandeur + '/kraken2/kraken2_summary.csv'
    # serotypefinder = args.grandeur + '/serotypefinder/serotypefinder_results.txt'
    # shigatyper     = args.grandeur + '/shigatyper/shigatyper_results.txt'

    # getting coverage
    summary_df     = pd.read_table(summary)
    df             = pd.merge(df,summary_df[['sample','coverage','warnings']],left_on='Sample_Name', right_on='sample', how='left')
    df             = df.drop('sample', axis=1)
    df['coverage'] = df['coverage'].fillna(0)
    df['coverage'] = df['coverage'].round(2)

    # getting O and H groups
    if 'serotypefinder_Serotype_O' in summary_df.columns:
        if 'shigatyper_Hit' in summary_df.columns and 'mash_organism' in summary_df.columns:
            logging.info('Double checking E. coli organism with shigatyper results')
            ecoli_df = summary_df[summary_df['mash_organism'].str.contains('Shigella', na=False) | summary_df['mash_organism'].str.contains('Escherichia', na=False) ].copy()
            ecoli_df['serotypefinder_Serotype_O'] = ecoli_df['serotypefinder_Serotype_O'].fillna("none")
            ecoli_df['serotypefinder_Serotype_H'] = ecoli_df['serotypefinder_Serotype_H'].fillna("none")
            ecoli_df['ecoli_organism'] = "Escherichia coli"
            ecoli_df.loc[ecoli_df['shigatyper_Hit'].str.contains('ipaH', na=False), 'ecoli_organism'] = 'Shigella'
            ecoli_df['SerotypeFinder (E. coli)'] = ecoli_df['ecoli_organism'] + " " + ecoli_df['serotypefinder_Serotype_O'] + ":" + ecoli_df['serotypefinder_Serotype_H']

            df = pd.merge(df,ecoli_df[['sample','SerotypeFinder (E. coli)']],left_on='Sample_Name', right_on='sample', how='left')
            df = df.drop('sample', axis=1)
        else:
            summary_df['SerotypeFinder (E. coli)'] = summary_df['serotypefinder_Serotype_O'].apply(str) + ':' + summary_df['serotypefinder_Serotype_H'].apply(str)
            
            df = pd.merge(df,summary_df[['sample','SerotypeFinder (E. coli)']],left_on='Sample_Name', right_on='sample', how='left')
            df = df.drop('sample', axis=1)
    else:
        df['SerotypeFinder (E. coli)'] = ''

    if 'kraken2_organism_(per_fragment)' in summary_df.columns:
        df = kraken2_results(df, summary_df)

    if 'blobtools_organism_(per_mapped_reads)' in summary_df.columns:
        df = blobtools_results(df, summary_df)

    return df

def mash_results(df, args):
    mash_dir      = args.grandeur + '/mash/'
        
    if not os.path.isdir(mash_dir):
        return df
    
    logging.info('Getting the top organism from mash at ' + mash_dir)

    dfs = []
    for filename in os.listdir(mash_dir):
        if filename.endswith("summary.mash.csv"):
            filepath = os.path.join(mash_dir, filename)
            ind_df = pd.read_csv(filepath)
            if not ind_df.empty:
                dfs.append(ind_df)

    if dfs:
        mash_df = pd.concat(dfs, ignore_index=True)
    else:
        return df

    if not mash_df.empty:
        mash_df = mash_df.sort_values(by=['P-value', 'mash-distance'])
        mash_df = mash_df.drop_duplicates(subset=['sample'], keep = 'first')
        
        df = pd.merge(df,mash_df[['sample','organism']],left_on='Sample_Name', right_on='sample', how='left')
        df = df.drop('sample', axis=1)

        if 'organism_x' in df.keys():
            df['organism'] = None
            df['organism'] = df ['organism_x'].combine_first(df['organism'])
            df['organism'] = df ['organism'].combine_first(df['organism_y'])
            df = df.drop('organism_x', axis=1)
            df = df.drop('organism_y', axis=1)

    return df

def mlst_results(df, args):
    mlst_dir      = args.grandeur + '/mlst/'
        
    if not os.path.isdir(mlst_dir):
        return df
    
    logging.info('Getting MLST information from ' + mlst_dir)

    dfs = []
    for filename in os.listdir(mlst_dir):
        if filename.endswith("mlst.tsv"):
            filepath = os.path.join(mlst_dir, filename)
            ind_df = pd.read_table(filepath, sep="\t")
            if not ind_df.empty:
                dfs.append(ind_df)

    if dfs:
        mlst_df = pd.concat(dfs, ignore_index=True)
    else:
        return df

    if not mlst_df.empty:
        mlst_df['mlst'] = mlst_df['matching PubMLST scheme'] + ':' + mlst_df['ST'].astype('str')
        df              = pd.merge(df,mlst_df[['sample','mlst']],left_on='Sample_Name', right_on='sample', how='left')
        df              = df.drop('sample', axis=1)

    return df


def seqsero2_results(df, args):
    seqsero2_dir  = args.grandeur + '/seqsero2/'
        
    if not os.path.isdir(seqsero2_dir):
        return df
    
    logging.info('Getting salmonella serotype information from ' + seqsero2_dir)

    dfs = []
    files = glob.glob(args.grandeur + '/seqsero2/*/SeqSero_result.tsv')
    for file in files:
        ind_df = pd.read_table(file, sep='\t')
        if not ind_df.empty:
                dfs.append(ind_df)

    if dfs:
        seqsero2_df = pd.concat(dfs, ignore_index=True)
    else:
        return df

    if not seqsero2_df.empty:
        seqsero2_df['SeqSero Organism (Salmonella)'] = 'Salmonella enterica serovar ' + seqsero2_df['Predicted serotype'] + ':' + seqsero2_df['Predicted antigenic profile']

        df = pd.merge(df,seqsero2_df[['sample','SeqSero Organism (Salmonella)']],left_on='Sample_Name', right_on='sample', how='left')
        df = df.drop('sample', axis=1)
    else:
        df['SeqSero Organism (Salmonella)'] = ''

    return df

def kraken2_results(df, summary_df):
    logging.info("Getting kraken2 results")
    df = pd.merge(df,summary_df[['sample','kraken2_organism_(per_fragment)']],left_on='Sample_Name', right_on='sample', how='left')
    df = df.drop('sample', axis=1)

    return df

def blobtools_results(df, summary_df):
    logging.info("Getting blobtools results")
    df = pd.merge(df,summary_df[['sample','blobtools_organism_(per_mapped_reads)']],left_on='Sample_Name', right_on='sample', how='left')
    df = df.drop('sample', axis=1)

    return df

def pass_fail(df):
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

    return df

def main():
    version = '0.1.24191'

    parser = argparse.ArgumentParser()
    parser.add_argument('-g', '--grandeur',    type=str, help='directory where Grandeur has output results', required=True)
    parser.add_argument('-s', '--samplesheet', type=str, help='sample sheet for run',                        required=True)
    parser.add_argument('-v', '--version',               help='print version and exit', action='version', version='%(prog)s ' + version)
    args   = parser.parse_args()

    df = sample_sheet_to_df(args.samplesheet)

    df = grandeur_summary(df, args)

    df = fastani_results(df, args)

    df = mash_results(df, args)

    df = seqsero2_results(df, args)

    df = mlst_results(df, args)

    df = emmtyper_results(df, args)

    df = pass_fail(df)

    create_files(df)


if __name__ == "__main__":
    main()