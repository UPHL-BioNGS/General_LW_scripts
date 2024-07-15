#!/usr/bin/env python3

'''
Author: Erin Young

Description:

This script will collect needed files to get results from Grandeur for 
1. The 'Finished' tab (will be discontinued in the future)
2. As a lookup table for the 'ARLN' tab

It's really meant to be copied and pasted into corresponding google sheets.

EXAMPLE:
python3 grandeur_to_sheets.py -g <path to grandeur results> -s <input sample sheet>
'''

# ignore line too long warnings
# pylint: disable=C0301

# trying to keep dependencies really low
import argparse
import os
import sys
import logging
import glob

import pandas as pd

# local files
from read_miseq_sample_sheet import read_miseq_sample_sheet


def amrfinder_results(df, args):
    """

    Parses amrfinder output
    
    Args:
        df (pd.Dataframe): dataframe for results thus far.
        args (argparse.Namespace): Parsed command-line arguments.
    
    Returns:
        df (pd.Dataframe): Pandas dataframe of the parsed output.

    """

    amrfinder_df = results_to_df(f"{args.grandeur}/ncbi-AMRFinderplus/", "\t", "_amrfinder_plus.txt")

    if not amrfinder_df.empty:
        amrfinder_df              = amrfinder_df.sort_values('Gene symbol')

        # amr results
        amr_df                    = amrfinder_df[amrfinder_df['Element type'] == 'AMR'].copy()
        amr_df                    = amr_df.groupby('Name', as_index=False).agg({'Gene symbol': lambda x: ', '.join(list(x))})
        amr_df['amr genes']       = amr_df['Gene symbol']
        df                        = pd.merge(df,amr_df[['Name','amr genes']],left_on='Sample_Name', right_on='Name', how='left')
        df                        = df.drop('Name', axis=1)

        # virulence results
        vir_df                    = amrfinder_df[amrfinder_df['Element type'] == 'VIRULENCE'].copy()
        vir_df                    = vir_df.groupby('Name', as_index=False).agg({'Gene symbol': lambda x: ', '.join(list(x))})
        vir_df['virulence genes'] = vir_df['Gene symbol']
        df                        = pd.merge(df,vir_df[['Name','virulence genes']],left_on='Sample_Name', right_on='Name', how='left')
        df                        = df.drop('Name', axis=1)

    return df


def blobtools_results(df, summary_df):
    """

    Parses blobtools output
    
    Args:
        df (pd.Dataframe): dataframe for results thus far.
        summary_df (pd.Dataframe): dataframe of grandeur results.
    
    Returns:
        df (pd.Dataframe): Pandas dataframe of the parsed output.

    """

    logging.info("Getting blobtools results")
    df = pd.merge(df,summary_df[['sample','blobtools_organism_(per_mapped_reads)']],left_on='Sample_Name', right_on='sample', how='left')
    df = df.drop('sample', axis=1)

    return df


def create_files(df):
    """

    Creates final files.
    
    Args:
        df (pd.Dataframe): dataframe for results to print to file(s).
    
    Creates:
        file (file): Results files. A lot of them.

    """

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
    """

    Parses emmtyper output
    
    Args:
        df (pd.Dataframe): dataframe for results thus far.
        args (argparse.Namespace): Parsed command-line arguments.
    
    Returns:
        df (pd.Dataframe): Pandas dataframe of the parsed output.

    """

    emmtyper_df = results_to_df(f"{args.grandeur}/emmtyper/", "\t", "_emmtyper.txt")

    if not emmtyper_df.empty:
        emmtyper_df['emm type'] = emmtyper_df['Predicted emm-type']
        df = pd.merge(df,emmtyper_df[['sample','emm type']],left_on='Sample_Name', right_on='sample', how='left')
        df = df.drop('sample', axis=1)

    return df





def fastani_results(df, args):
    """

    Parses fastani output
    
    Args:
        df (pd.Dataframe): dataframe for results thus far.
        args (argparse.Namespace): Parsed command-line arguments.
    
    Returns:
        df (pd.Dataframe): Pandas dataframe of the parsed output.

    """

    fastani_df = results_to_df(f"{args.grandeur}/fastani/", ',', '_fastani.csv')

    # Getting the WGS organism from fastani or mash
    if not fastani_df.empty:
        fastani_df             = fastani_df[fastani_df['ANI estimate'] >= 0.9]
        fastani_df             = fastani_df.sort_values(by=['ANI estimate'], ascending = False)
        fastani_df             = fastani_df.drop_duplicates(subset=['sample'], keep = 'first')
        fastani_df['organism'] = fastani_df['reference'].str.replace('_GC.*', '', regex = True)

        df = pd.merge(df,fastani_df[['sample','organism']],left_on='Sample_Name', right_on='sample', how='left')
        df = df.drop('sample', axis=1)

    return df



def fix_escherichia(row, directory):
    """

    Checking for ipaH.
    
    Args:
        row (pd.Dataframe): dataframe row
    
    Returns:
        organism (str): Predicted organism.

    """
    sample = row['Sample_Name']
    organism = row['organism']
    shiga_hit = row['shigatyper_hit']

    if pd.notna(row['ecoli_O_H']) and pd.notna(row['shigatyper_hit']):
        if 'IpaH' in shiga_hit:
            org_check = 'Shigella'
        else:
            org_check = 'Escherichia'

        fastani_file = f"{directory}/fastani/{sample}_fastani.csv"
        if os.path.exists(fastani_file):
            with open(fastani_file) as file:
                for line in file:
                    line = line.strip()
                    if org_check in line:
                        ref = line.split(',')[2].split('_')
                        organism = f"{ref[0]} {ref[1]}"
                        break

    return organism


def grandeur_summary(df, args):
    """

    Parses grandeur summary
    
    Args:
        df (pd.Dataframe): dataframe for results thus far.
        args (argparse.Namespace): Parsed command-line arguments.
    
    Returns:
        df (pd.Dataframe): Pandas dataframe of the parsed output.

    """
    summary = f"{args.grandeur}/grandeur_summary.tsv"
    logging.info(f"Extracting information from {summary}")

    # using results in summary file instead of the "original"
    # blobtools      = f"{args.grandeur}/blobtools/blobtools_summary.txt"
    # kraken2        = f"{args.grandeur}/kraken2/kraken2_summary.csv"
    # serotypefinder = f"{args.grandeur}/serotypefinder/serotypefinder_results.txt"
    # shigatyper     = f"{args.grandeur}/shigatyper/shigatyper_results.txt"

    # getting coverage
    summary_df     = pd.read_table(summary)
    df             = pd.merge(df,summary_df[['sample','coverage','warnings']],left_on='Sample_Name', right_on='sample', how='left')
    df             = df.drop('sample', axis=1)
    df['coverage'] = df['coverage'].fillna(0)
    df['coverage'] = df['coverage'].round(2)

    if 'shigatyper_hit' in summary_df.columns and 'serotypefinder_Serotype_O' in summary_df.columns and 'serotypefinder_Serotype_H'  in summary_df.columns:
        df = serotypefinder_results(df, summary_df)

    if 'kraken2_organism_(per_fragment)' in summary_df.columns:
        df = kraken2_results(df, summary_df)

    if 'blobtools_organism_(per_mapped_reads)' in summary_df.columns:
        df = blobtools_results(df, summary_df)

    return df


def kraken2_results(df, summary_df):
    """

    Parses kraken2 output
    
    Args:
        df (pd.Dataframe): dataframe for results thus far.
        args (argparse.Namespace): Parsed command-line arguments.
    
    Returns:
        df (pd.Dataframe): Pandas dataframe of the parsed output.

    """
    logging.info("Getting kraken2 results")
    df = pd.merge(df,summary_df[['sample','kraken2_organism_(per_fragment)']],left_on='Sample_Name', right_on='sample', how='left')
    df = df.drop('sample', axis=1)

    return df


def mash_results(df, args):
    """

    Parses mash output
    
    Args:
        df (pd.Dataframe): dataframe for results thus far.
        args (argparse.Namespace): Parsed command-line arguments.
    
    Returns:
        df (pd.Dataframe): Pandas dataframe of the parsed output.

    """
    mash_df = results_to_df(f"{args.grandeur}/mash/", ",", "summary.mash.csv")

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
    """

    Parses mlst output
    
    Args:
        df (pd.Dataframe): dataframe for results thus far.
        args (argparse.Namespace): Parsed command-line arguments.
    
    Returns:
        df (pd.Dataframe): Pandas dataframe of the parsed output.
    """

    mlst_df = results_to_df(f"{args.grandeur}/mlst/", "\t", "mlst.tsv")

    if not mlst_df.empty:
        mlst_df['mlst'] = mlst_df['matching PubMLST scheme'] + ':' + mlst_df['ST'].astype('str')
        df              = pd.merge(df,mlst_df[['sample','mlst']],left_on='Sample_Name', right_on='sample', how='left')
        df              = df.drop('sample', axis=1)

    return df


def pass_fail(df, args):
    """

    Uses coverage to set some basic pass/fail conditions.
    
    Args:
        df (pd.Dataframe): results thus far.

    Returns:
        df (pd.Dataframe): Pandas dataframe with 'Pass' column.

    """

    # in general conditions
    df['Pass'] = 'TBD'
    df.loc[df['coverage'] >= 40, 'Pass'] = 'Y'
    df.loc[df['coverage'] < 20,  'Pass'] = 'X'

    # organism specific conditions
    organisms = [
        'Acinetobacter',
        'Citrobacter',
        'Elizabethkingia',
        'Enterobacter',
        'Escherichia',
        'Klebsiella',
        'Listeria',
        'Neisseria',
        'Providencia',
        'Pseudomonas',
        'Ralstonia',
        'Serratia',
        'Shigella', 
        'Streptococcus' ]

    for organism in organisms:
        df.loc[(df['organism'].str.contains(organism, na=False))    & (df['coverage'] >= 40), 'Pass'] = 'Y'
        df.loc[(df['organism'].str.contains(organism, na=False))    & (df['coverage'] <  40), 'Pass'] = 'X'

    df.loc[(df['organism'].str.contains('Salmonella', na=False))    & (df['coverage'] >= 30), 'Pass'] = 'Y'
    df.loc[(df['organism'].str.contains('Salmonella', na=False))    & (df['coverage'] <  30), 'Pass'] = 'X'
    df.loc[(df['organism'].str.contains('Campylobacter', na=False)) & (df['coverage'] >= 20), 'Pass'] = 'Y'
    df.loc[(df['organism'].str.contains('Campylobacter', na=False)) & (df['coverage'] <  20), 'Pass'] = 'X'

    df             = df.sort_values('wgs_id')
    df['organism'] = df['organism'].str.replace('_',' ',regex=False)


    # fix shigella/ecoli mixups
    if 'ecoli_O_H' in df.columns and 'shigatyper_hit' in df.columns and 'mash_organism' in df.columns:
        df['organism'] = df.apply(fix_escherichia, axis=1, directory = args.grandeur)

        df['SerotypeFinder (E. coli)'] = None
        df['SerotypeFinder (E. coli)'] = df.apply(lambda row: f"{row['organism']} {row['ecoli_O_H']}" if pd.notna(row['ecoli_O_H']) else row['SerotypeFinder (E. coli)'], axis=1)

    return df


def results_to_df(path, delim, end):
    """

    Combines results for files into a dataframe
    
    Args:
        path (str): directory with results stored.
        delim (str): delimiter used in file ("," or "/t" are the most common).
        end (str): The last characters of a filename.
    
    Returns:
        df (pd.Dataframe): Pandas dataframe of the parsed output.

    """

    if not os.path.isdir(path):
        return pd.DataFrame()

    logging.info(f"Getting information from {path}")

    dfs = []
    for filename in os.listdir(path):
        if filename.endswith(end):
            filepath = os.path.join(path, filename)
            ind_df = pd.read_table(filepath, sep=delim)
            if not ind_df.empty:
                dfs.append(ind_df)

    if dfs:
        return pd.concat(dfs, ignore_index=True)
    else:
        return pd.DataFrame()


def sample_sheet_to_df(samplesheet):
    """

    Creates pandas dataframe from MiSeq sample sheet.
    
    Args:
        samplesheet (str): path to sample sheet.
    
    Returns:
        df (pd.Dataframe): Pandas dataframe of the parsed output.

    """

    logging.info(f"Getting samples from {samplesheet}")

    if os.path.exists(samplesheet):
        # get all the samples from the sample sheet into a pandas dataframe
        df            = read_miseq_sample_sheet(samplesheet, "sample_id")
        df['lims_id'] = df['Sample_ID'].str.replace(  '-UT.*','', regex=True)
        df['wgs_id']  = df['Sample_Name'].str.replace('-UT.*','', regex=True)

        return df

    else:
        logging.fatal('Sample sheet could not be located! (Specify with -s)')
        sys.exit(1)


def seqsero2_results(df, args):
    """

    Parses seqsero2 output
    
    Args:
        df (pd.Dataframe): dataframe for results thus far.
        args (argparse.Namespace): Parsed command-line arguments.
    
    Returns:
        df (pd.Dataframe): Pandas dataframe of the parsed output.

    """

    seqsero2_dir = f"{args.grandeur}/seqsero2/"

    if not os.path.isdir(seqsero2_dir):
        return df

    logging.info(f"Getting salmonella serotype information from {seqsero2_dir}")

    # does not use results_to_df because of file structure
    dfs = []
    files = glob.glob(f"{args.grandeur}/seqsero2/*/SeqSero_result.tsv")
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


def serotypefinder_results(df, summary_df):
    """

    Parses serotypefinder output
    
    Args:
        df (pd.Dataframe): dataframe for results thus far.
        summary_df (pd.Dataframe): dataframe of grandeur results.
        args (argparse.Namespace): Parsed command-line arguments.
    
    Returns:
        df (pd.Dataframe): Pandas dataframe of the parsed output.

    """
    logging.info('Double checking Escherichia organism with shigatyper results')

    if 'shigatyper_hit' in summary_df.columns and 'serotypefinder_Serotype_O' in summary_df.columns and 'serotypefinder_Serotype_H'  in summary_df.columns:
        # creating a copy of the summary_df to just the Escherichia samples
        ecoli_df                              = summary_df[summary_df['mash_organism'].str.contains('Shigella', na=False) | summary_df['mash_organism'].str.contains('Escherichia', na=False) ].copy()
        ecoli_df['serotypefinder_Serotype_O'] = ecoli_df['serotypefinder_Serotype_O'].fillna("none")
        ecoli_df['serotypefinder_Serotype_H'] = ecoli_df['serotypefinder_Serotype_H'].fillna("none")
        ecoli_df['ecoli_O_H']                       = ecoli_df['serotypefinder_Serotype_O'].astype(str) + ':' + ecoli_df['serotypefinder_Serotype_H'].astype(str)

        df = pd.merge(df, ecoli_df[['sample','ecoli_O_H', 'shigatyper_hit', 'mash_organism']],left_on='Sample_Name', right_on='sample', how='left')
        df = df.drop('sample', axis=1)

    return df


def main():
    """

    Parses output from Grandeur version 3.
    
    Args:
        args (argparse.Namespace): Parsed command-line arguments.
    
    Prints:
        files (str): Files for Results tab and ARLN Regional tab.
    
    """

    logging.basicConfig(format='%(asctime)s - %(message)s', datefmt = '%y-%b-%d %H:%M:%S', level=logging.INFO)

    version = '0.1.24191'

    parser = argparse.ArgumentParser()
    parser.add_argument('-g', '--grandeur',    type=str, help='directory where Grandeur has output results', required=True)
    parser.add_argument('-s', '--samplesheet', type=str, help='sample sheet for run',                        required=True)
    parser.add_argument('-v', '--version',               help='print version and exit', action='version', version='%(prog)s ' + version)
    args   = parser.parse_args()

    df = sample_sheet_to_df(args.samplesheet)

    df = grandeur_summary(      df, args)

    df = fastani_results(       df, args)

    df = mash_results(          df, args)

    df = seqsero2_results(      df, args)

    df = mlst_results(          df, args)

    df = emmtyper_results(      df, args)

    df = amrfinder_results(     df, args)

    df = pass_fail(df, args)

    create_files(df)


if __name__ == "__main__":
    main()
