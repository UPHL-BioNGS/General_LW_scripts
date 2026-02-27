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
import traceback

import pandas as pd

# local files
from miseq_samplesheet_to_df    import read_miseq_sample_sheet
from clarity_query_function     import query_clarity_for_ids

def amrfinder_results(df, args):
    """

    Parses amrfinder output
    
    Args:
        df (pd.Dataframe): dataframe for results thus far.
        args (argparse.Namespace): Parsed command-line arguments.
    
    Returns:
        df (pd.Dataframe): Pandas dataframe of the parsed output.

    """

    logging.info("Getting amrfinder results")

    amrfinder_df = pd.DataFrame()

    if os.path.exists(f"{args.grandeur}/amrfinder/amrfinderplus.txt"):
        amrfinder_df = pd.read_table(f"{args.grandeur}/amrfinder/amrfinderplus.txt")
    else:
        amrfinder_df = results_to_df(f"{args.grandeur}/ncbi-AMRFinderplus/", "\t", "_amrfinder_plus.txt")

    if "Element symbol" in amrfinder_df.columns:
        element_or_gene = "Element"
        element_or_gene_type = "Type"
    elif "Gene symbol" in amrfinder_df.columns:
        element_or_gene = "Gene"
        element_or_gene_type = "Element type"
    else:
        logging.warning("Could not determined element or gene")

    if not amrfinder_df.empty:
        amrfinder_df              = amrfinder_df.sort_values(f"{element_or_gene} symbol")
        amrfinder_df['Name']      = amrfinder_df['Name'].astype('str')

        # amr results
        amr_df                    = amrfinder_df[amrfinder_df[f"{element_or_gene_type}"] == 'AMR'].copy()
        amr_df                    = amr_df.groupby('Name', as_index=False).agg({f'{element_or_gene} symbol': lambda x: ', '.join(list(x))})
        amr_df['amr genes']       = amr_df[f'{element_or_gene} symbol']
        df                        = pd.merge(df,amr_df[['Name','amr genes']],left_on='sample_name', right_on='Name', how='left')
        df                        = df.drop('Name', axis=1)

        # virulence results
        vir_df                    = amrfinder_df[amrfinder_df[f'{element_or_gene_type}'] == 'VIRULENCE'].copy()
        vir_df                    = vir_df.groupby('Name', as_index=False).agg({f'{element_or_gene} symbol': lambda x: ', '.join(list(x))})
        vir_df['virulence genes'] = vir_df[f'{element_or_gene} symbol']
        df                        = pd.merge(df,vir_df[['Name','virulence genes']],left_on='sample_name', right_on='Name', how='left')
        df                        = df.drop('Name', axis=1)

    return df


def blobtools_results(df, summary_df):
    """

    Parses blobtools output
    
    Args:
        df (pd.Dataframe): dataframe for results thus far.
        args (argparse.Namespace): Parsed command-line arguments.
    
    Returns:
        df (pd.Dataframe): Pandas dataframe of the parsed output.

    """

    logging.info("Getting blobtools organism results")
    df = pd.merge(df,summary_df[['sample','blobtools_organism_(per_mapped_reads)']],left_on='sample_name', right_on='sample', how='left')
    df = df.drop('sample', axis=1)

    return df


def circulocov_results(df, args):
    """
    Parses circulocov output
    
    Args:
        df (pd.Dataframe): dataframe for results thus far.
        summary_df (pd.Dataframe): dataframe of grandeur results.
    
    Returns:
        df (pd.Dataframe): Pandas dataframe of the parsed output.
    """

    logging.info("Getting circulocov results")
    circulocov_df = pd.read_table(f"{args.grandeur}/circulocov/circulocov_summary.tsv")
    circulocov_df['sample'] = circulocov_df['sample'].astype('str')
    circulocov_df = circulocov_df[circulocov_df["contigs"].str.strip() == "all"]
    circulocov_df['coverage'] = circulocov_df['illumina_meandepth']

    df = pd.merge(df,circulocov_df[['sample','coverage']],left_on='sample_name', right_on='sample', how='left')
    df['coverage'] = df['coverage'].fillna(0)
    df['coverage'] = df['coverage'].round(2)
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

    logging.info("Creating final files")
    # columns for final files
    # For the results tab : top organism, serotypefinder/shigellatyper, seqsero2, coverage, warnings, blobtools, and kraken2
    finished_cols = [
        'sample_id', 
        'Description', 
        'organism', 
        'SerotypeFinder (E. coli)', 
        'SeqSero Organism (Salmonella)', 
        'Sample_Project', 
        'coverage', 
        'Pass', 
        'warnings', 
        'blobtools_organism_(per_mapped_reads)'
        ]
    
    # ARLN needs 'WGS MLST', 'AMR genes', 'Virulence genes'
    arln_cols = [
        'sample_id', 
        'Description', 
        'organism', 
        'coverage', 
        'mlst', 
        'emm type', 
        'Sample_Project', 
        'amr genes', 
        'virulence genes', 
        'kraken2_organism_(per_fragment)', 
        'blobtools_organism_(per_mapped_reads)'
        ]

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

    logging.info("Getting emmtyper results")
    emmtyper_df = results_to_df(f"{args.grandeur}/emmtyper/", "\t", "_emmtyper.txt")

    if not emmtyper_df.empty:
        emmtyper_df['sample'] = emmtyper_df['sample'].astype('str')
        emmtyper_df['emm type'] = emmtyper_df['Predicted emm-type']
        df = pd.merge(df,emmtyper_df[['sample','emm type']],left_on='sample_name', right_on='sample', how='left')
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
    logging.info("Getting fastani organism results")
    fastani_df = pd.DataFrame()

    if os.path.exists(f"{args.grandeur}/fastani/fastani_summary.csv"):
        fastani_df = pd.read_csv(f"{args.grandeur}/fastani/fastani_summary.csv")
    else:
        fastani_df = results_to_df(f"{args.grandeur}/fastani/", ',', '_fastani.csv')

    # Getting the WGS organism from fastani or mash
    if not fastani_df.empty:
        fastani_df             = fastani_df[fastani_df['ANI estimate'] >= 0.9]
        fastani_df             = fastani_df.sort_values(by=['ANI estimate'], ascending = False)
        fastani_df['organism'] = fastani_df['reference'].str.replace('_GC.*', '', regex = True)
        fastani_df['sample']   = fastani_df['sample'].astype('str')

        fastani_df_depulicated = fastani_df.drop_duplicates(subset=['sample'], keep = 'first').copy()

        df = pd.merge(df,fastani_df_depulicated[['sample','organism']],left_on='sample_name', right_on='sample', how='left')
        df = df.drop('sample', axis=1)

    else:
        df['organism'] = pd.NA

    return df, fastani_df



def fix_escherichia(row, fastani_df):
    """

    Checking for ipaH.
    
    Args:
        row (pd.Dataframe): dataframe row
        fastani_df: fastani_df
    
    Returns:
        organism (str): Predicted organism.

    """
    organism = str(row['organism']) if pd.notna(row['organism']) else ""
    amr = str(row['amr genes']) if pd.notna(row['amr genes']) else ""
    virulence = str(row['virulence genes']) if pd.notna(row['virulence genes']) else ""
    sample_id = row['sample_id']

    if "Shigella" not in organism and "Escherichia" not in organism:
        return organism

    matches = fastani_df[fastani_df['sample'] == sample_id]
    if 'ipaH' in amr or 'ipaH' in virulence:
        genus_matches = matches[matches['organism'].str.contains('Shigella', case=False, na=False)]
        try:
            organism = f"{genus_matches.sort_values(by='ANI estimate', ascending=False).iloc[0]['organism']} (ipaH+)"
        except:
            organism = "Unknown (ipaH+)"
    else:
        genus_matches = matches[matches['organism'].str.contains('Escherichia', case=False, na=False)]
        try:
            organism = f"{genus_matches.sort_values(by='ANI estimate', ascending=False).iloc[0]['organism']} (ipaH-)"
        except:
            organism = "Unknown (ipaH-)"

    return organism

def fix_ecoli(df, fastani_df):
    """

    Checking for ipaH. 
    ipaH+ means Shigella
    ipaH- means Escherichia
    Fixes the 'organism' column for these species.
    
    Args:
        df (pd.Dataframe): dataframe for results thus far.
        fastani_df: fastani_df
    
    Returns:
        df (pd.Dataframe): Pandas dataframe of the parsed output.

    """
    logging.info("Checking Escherichia species")

    if 'ecoli_O_H' in df.columns:
        df['organism'] = df.apply(lambda row: fix_escherichia(row, fastani_df), axis=1)
        df.loc[
            df['organism'].str.contains('Shigella|Escherichia', na=False),
            'SerotypeFinder (E. coli)'
        ] = df['organism'].str.split(" ").str[0].str.replace("_", " ", regex=False) + ' ' + df['ecoli_O_H']
    return df


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
    summary_df = pd.read_table(summary)
    summary_df['sample'] = summary_df['sample'].astype('str')

    required_cols = {'sample', 'coverage', 'warnings'}
    available_cols = required_cols.intersection(summary_df.columns)

    df = pd.merge(df,summary_df[list(available_cols)],left_on='sample_name', right_on='sample', how='left')
    df = df.drop('sample', axis=1)

    if 'coverage' in df.columns:
        df['coverage'] = df['coverage'].fillna(0)
        df['coverage'] = df['coverage'].round(2)
    else:
        df['coverage'] = 0

    if 'shigatyper_hit' in summary_df.columns.str.lower() and 'serotypefinder_serotype_o' in summary_df.columns.str.lower() and 'serotypefinder_serotype_h' in summary_df.columns.str.lower():
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
    df = pd.merge(df,summary_df[['sample','kraken2_organism_(per_fragment)']],left_on='sample_name', right_on='sample', how='left')
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
    logging.info("Getting mash organism results")
    mash_df = pd.DataFrame()

    if os.path.exists(f"{args.grandeur}/mash/mash_summary.csv"):
        mash_df = pd.read_csv(f"{args.grandeur}/mash/mash_summary.csv", sep = ',')
    else:
        mash_df = results_to_df(f"{args.grandeur}/mash/", ",", "summary.mash.csv")

    if not mash_df.empty:
        mash_df['sample'] = mash_df['sample'].astype('str')
        mash_df = mash_df.sort_values(by=['P-value', 'mash-distance'])
        mash_df = mash_df.drop_duplicates(subset=['sample'], keep = 'first')

        df_with_org = df[df['organism'].notna()].copy()
        df_missing_org = df[df['organism'].isna()].copy()
        if not df_missing_org.empty:
            df_missing_org = df_missing_org.drop(columns=['organism'])
            df_missing_org = pd.merge(df_missing_org, mash_df[['sample','organism']],left_on='sample_name', right_on='sample', how='left')
            df_missing_org['organism'] = df_missing_org['organism'].combine_first(df_missing_org['organism'])
            df_missing_org = df_missing_org.drop(columns=['sample'])
            df = pd.concat([df_with_org, df_missing_org], ignore_index=True)
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

    logging.info("Getting mlst results")
    mlst_df = results_to_df(f"{args.grandeur}/mlst/", "\t", "mlst.tsv")

    if not mlst_df.empty:
        mlst_df['sample'] = mlst_df['sample'].astype('str')
        mlst_df['mlst'] = mlst_df['matching PubMLST scheme'] + ':' + mlst_df['ST'].astype('str')
        df              = pd.merge(df,mlst_df[['sample','mlst']],left_on='sample_name', right_on='sample', how='left')
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
    logging.info("Pass/Fail results")
    # in general conditions
    df['Pass'] = 'TBD'
    df.loc[df['coverage'] >= 40, 'Pass'] = 'Y'
    df.loc[df['coverage'] < 20,  'Pass'] = 'X'

    # organism specific conditions
    df.loc[(df['organism'].str.contains('Salmonella', na=False))    & (df['coverage'] >= 30), 'Pass'] = 'Y'
    df.loc[(df['organism'].str.contains('Salmonella', na=False))    & (df['coverage'] <  30), 'Pass'] = 'X'
    df.loc[(df['organism'].str.contains('Campylobacter', na=False)) & (df['coverage'] >= 20), 'Pass'] = 'Y'
    df.loc[(df['organism'].str.contains('Campylobacter', na=False)) & (df['coverage'] <  20), 'Pass'] = 'X'

    df             = df.sort_values('wgs_id')
    df['organism'] = df['organism'].str.replace('_',' ',regex=False)

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
        df         = read_miseq_sample_sheet(samplesheet, "sample_id")
        df.columns = df.columns.str.lower()

        clarity_string = ""
        with open('/Volumes/NGS_2/Bioinformatics/eriny/query.txt', 'r') as file:
            line = file.readline()
            clarity_string = line.strip()


        df['lims_id'] = df['sample_id'].str.replace(  '-UT.*','', regex=True)
        df['lims_id'] = df['lims_id'].astype('str')

        clarity_keys = [
            'Required Coverage (X)', 
            'Test Requested', 
            'Test Selected', 
            'Species', 
            'ARLN ID', 
            'Genome Size (Mb)', 
            'GCWGS ID'
        ] 

        logging.info(f"Getting information from clarity")
        try:
            clarity_dict = query_clarity_for_ids(df['lims_id'], clarity_keys, 'queryuser', clarity_string)

            clarity_info = []
            for lims_id, info in clarity_dict.items():
                record = {'lims_id': lims_id}
                for key, value in info.items():
                    record[key] = next(iter(value)) if isinstance(value, set) else value
                clarity_info.append(record)

            clarity_df = pd.DataFrame(clarity_info)
            clarity_df['lims_id'] = clarity_df['lims_id'].astype(str)
            clarity_df['Description'] = clarity_df['Species'].astype(str)

            df = pd.merge(df, clarity_df, on='lims_id', how='left')
            if 'ARLN ID' not in df.columns:
                df['ARLN ID'] = None

        except Exception as e:
            logging.warning(f"Something happened with clarity: {e}")
            logging.debug(traceback.format_exc())

        df['wgs_id'] = df['ARLN ID'].fillna(df['sample_name'].str.replace('-UT.*','', regex=True))
        df[['sample_id', 'sample_name', 'wgs_id']] = df[['sample_id', 'sample_name', 'wgs_id']].astype('str')

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
        seqsero2_df['sample'] = seqsero2_df['sample'].astype('str')
        seqsero2_df['SeqSero Organism (Salmonella)'] = 'Salmonella enterica serovar ' + seqsero2_df['Predicted serotype'] + ':' + seqsero2_df['Predicted antigenic profile']

        df = pd.merge(df,seqsero2_df[['sample','SeqSero Organism (Salmonella)']],left_on='sample_name', right_on='sample', how='left')
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

    if 'shigatyper_hit' in summary_df.columns.str.lower() and 'serotypefinder_serotype_o' in summary_df.columns.str.lower() and 'serotypefinder_serotype_h'  in summary_df.columns.str.lower():
        # creating a copy of the summary_df to just the Escherichia samples
        ecoli_df  = summary_df[summary_df['mash_organism'].str.contains('Shigella', na=False) | summary_df['mash_organism'].str.contains('Escherichia', na=False) ].copy()

        if ecoli_df.empty:
            ecoli_df = summary_df[summary_df['fastani_top_organism'].str.contains('Shigella', na=False) | summary_df['fastani_top_organism'].str.contains('Escherichia', na=False) ].copy()
        
        ecoli_df.columns = ecoli_df.columns.str.lower()
        ecoli_df['serotypefinder_Serotype_O'] = ecoli_df['serotypefinder_serotype_o'].fillna("none")
        ecoli_df['serotypefinder_Serotype_H'] = ecoli_df['serotypefinder_serotype_h'].fillna("none")
        ecoli_df['ecoli_O_H']                 = ecoli_df['serotypefinder_Serotype_O'].astype(str) + ':' + ecoli_df['serotypefinder_Serotype_H'].astype(str)
        ecoli_df['sample']                    = ecoli_df['sample'].astype('str')

        df = pd.merge(df, ecoli_df[['sample','ecoli_O_H', 'shigatyper_hit']],left_on='sample_name', right_on='sample', how='left')
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
    parser.add_argument('-r', '--run',         type=str, help='run name',                                    required=False, default = False)
    parser.add_argument('-v', '--version',               help='print version and exit', action='version', version='%(prog)s ' + version)
    args   = parser.parse_args()

    df = sample_sheet_to_df(args.samplesheet)

    if args.run:
        df['Sample_Project'] = args.run

    df = grandeur_summary(df, args)

    if 'coverage' not in df.columns:
        df = circulocov_results(df, args)

    df, fastani_df = fastani_results(df, args)

    df = mash_results(df, args)

    df = seqsero2_results(df, args)

    df = mlst_results(df, args)

    df = emmtyper_results(df, args)

    df = amrfinder_results(df, args)

    df = fix_ecoli(df, fastani_df)

    df = pass_fail(df, args)

    create_files(df)


if __name__ == "__main__":
    main()