#!/usr/bin/env python3

'''
Author: Erin Young

Description:

This script will collect needed files to get results from Grandeur for Labware 8 (LW8).

Each sample will get its own file to be placed for LW8 incorporation.

EXAMPLE:
python3 grandeur_arln_lw8.py -g <path to grandeur results> -s <input sample sheet>
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
from samplesheet_to_df import read_miseq_sample_sheet

def amrfinder_results(sample, df, args):
    """

    Parses amrfinder output
    
    Args:
        sample (str): sample results are
        df (pd.Dataframe): dataframe for results thus far.
        args (argparse.Namespace): Parsed command-line arguments.
    
    Returns:
        df (pd.Dataframe): Pandas dataframe of the parsed output.

    """

    genes = {
        'IMP Gene': {'search_term' : ["imp"]},
        'KPC Gene': {'search_term' : ["kpc"]},
        'NDM Gene': {'search_term' : ["ndm"]},
        'VIM Gene': {'search_term' : ["vim"]},
        'MCR 1 Gene': {'search_term' : ["mcr-1"]},
        'MCR 2 Gene': {'search_term' : ["mcr-2"]},
        'MCR 3 4 5 Gene': {'search_term' : ["mcr-3", "mcr-4", "mcr-5"]},
        'CMY 2 Gene': {'search_term' : ["cmy-2"]},
        'CTX M 14 Gene': {'search_term' : ["ctx-m-14"]},
        'CTX M 15 Gene': {'search_term' : ["ctx-m-15"]},
        'DHA Gene': {'search_term' : ["dha"]},
        'SPM Gene': {'search_term' : ["spm"]},
        'SIM Gene': {'search_term' : ["sim"]},
        'IMI Gene': {'search_term' : ["imi"]},
        'GES Gene': {'search_term' : ["ges"]},
        'GIM Gene': {'search_term' : ["gim"]}
    }

    specific_genes = {
        'OXA 24 40 Gene': {'search_term' : ["oxa-24", "oxa-40"]},
        'OXA 48 Like Gene': {'search_term' : ["oxa-48"]},
        'OXA 58 Gene': {'search_term' : ["oxa-58"]},
        'OXA 23 Gene': {'search_term' : ["oxa-23"]},
        'OXA 235 Gene': {'search_term' : ["oxa-235"]},
        'OXA 51 Gene': {'search_term' : ["oxa-51"]},
        'OXA 143 Gene': {'search_term' : ["oxa-143"]}
    }

    file = glob.glob(f"{args.grandeur}/*/{sample}-UT*amr*.txt")
    logging.info(f"Getting amr results from {file[0]}")
    amrfinder_df = pd.read_table(file[0], sep="\t")

    for key in genes.keys():
        df[key] = "Not Detected"
        df[key + "s Identified"] = ""
    df['amr_genes'] = ''

    if not amrfinder_df.empty:
        amrfinder_df = amrfinder_df.sort_values('Gene symbol')
        df['Other Gene Result Identified'] = ', '.join(amrfinder_df['Gene symbol'])

        for key in genes.keys():

            for gene in genes[key]['search_term']:
                if gene:
                    #  search through amrfinder_df for search term in 'Sequence name' column
                    subset = amrfinder_df[amrfinder_df["Sequence name"].str.contains(gene, case=False)]
                    if not subset.empty:
                        df.loc[0, key] = "Detected"
                        df[key + "s Identified"] = df[key + "s Identified"] + subset["Gene symbol"]

        for key in specific_genes.keys():

            for gene in specific_genes[key]['search_term']:
                if gene:
                    #  search through amrfinder_df for search term in 'Sequence name' column
                    subset = amrfinder_df[amrfinder_df["Sequence name"].str.contains(f"[\b]{gene}[\b]", case=False)]
                    if not subset.empty:
                        df.loc[0, key] = "Detected"
                        df[key + "s Identified"] = df[key + "s Identified"] + subset["Gene symbol"]


    return df

def create_columns(df, column_names):
    """

    Adds all columns to dataframe
    
    Args:
        df (pd.Dataframe): Pandas dataframe from sample sheet
        column_names: List of column names
    
    Returns:
        df (pd.Dataframe): Pandas dataframe of the parsed output.

    """

    for col in column_names:
        if col not in df.columns:
            df[col] = ""

    return df


def create_files(df, columns, args):
    """

    Creates final files.
    
    Args:
        df (pd.Dataframe): dataframe for results to print to file(s).
    
    Creates:
        file (file): Results files. A lot of them.

    """

    logging.info('Writing file for ARLN bacterial isolates')    
    for idx, row in df.iterrows():
        filename = f"{args.outdir}/{row['ARLN WGS ID']}_arln.csv"
        row_df = pd.DataFrame([row])
        row_df.to_csv(filename, columns=columns, index=False, sep= ',')


def grandeur_summary(df, args):
    """

    Parses grandeur summary for coverage
    
    Args:
        df (pd.Dataframe): dataframe for results thus far.
        args (argparse.Namespace): Parsed command-line arguments.
    
    Returns:
        df (pd.Dataframe): Pandas dataframe of the parsed output.

    """
    summary = f"{args.grandeur}/grandeur_summary.tsv"
    logging.info(f"Extracting information from {summary}")

    # getting coverage
    summary_df             = pd.read_table(summary)
    df                     = pd.merge(df,summary_df[['sample','coverage','warnings']],left_on='Sample_Name', right_on='sample', how='left')
    df                     = df.drop('sample', axis=1)
    df['Genomic Coverage'] = df['coverage'].fillna(0)
    df['Genomic Coverage'] = df['coverage'].round(2)

    return df


def mlst_results(sample, args):
    """

    Parses mlst output
    
    Args:
        sample (str): sample for results
        args (argparse.Namespace): Parsed command-line arguments.
    
    Returns:
        mlst (str): mlst value.
    """

    mlst_file = glob.glob(f"{args.grandeur}/mlst/{sample}-UT*mlst.tsv")
    logging.info(f"Getting mlst results from {mlst_file[0]}")
    df   = pd.read_table(mlst_file[0], sep="\t")

    if not df.empty:
        mlst = df.iloc[0]['matching PubMLST scheme'] + ':' + str(df.iloc[0]['ST'])
    return mlst

def organism_results(sample, df, args):
    """

    Gets predicted organism from WGS results
    
    Args:
        sample (str): sample id
        df (pd.Dataframe): results thus far
        args (argparse.Namespace): Parsed command-line arguments.
    
    Returns:
        df (pd.Dataframe): Pandas dataframe of the parsed output.

    """

    organism = 'unknown'
    org_check = ""
    if "ipaH" in df.loc[0, 'amr_genes']:
        org_check = 'Shigella'
    else:
        org_check = 'Escherichia'

    # first choice is fastani
    fastani_file = glob.glob(f"{args.grandeur}/fastani/{sample}-UT*fastani.csv")
    fastani_df = pd.DataFrame()
    if fastani_file:
        logging.info(f"Getting organism from fastani in {fastani_file[0]}")
        fastani_df   = pd.read_table(fastani_file[0], sep=",")
        if not fastani_df.empty:
            # filter fastani dataframe
            fastani_df = fastani_df[fastani_df['ANI estimate'] >= 0.9]
            fastani_df = fastani_df.sort_values(by=['ANI estimate'], ascending = False)
            fastani_df = fastani_df.drop_duplicates(subset=['sample'], keep = 'first')
            if not fastani_df.empty:
                fastani_df['organism'] = fastani_df['reference'].str.replace('_GC.*', '', regex = True)
                organism = fastani_df.iloc[0]['organism']

                # fix Excherichia/Shigella mixups
                if 'Shigella' in organism or 'Escherichia' in organism:
                    fastani_df = fastani_df[fastani_df['organism'].str.contains(org_check, case= False)]
                    if not fastani_df.empty:
                        organism = fastani_df.iloc[0]['organism']
                    else:
                        organism = 'unknown'

    # second choice is blobtools
    if organism == 'unknown':
        blobtools_file = glob.glob(f"{args.grandeur}/blobtools/{sample}-UT*blobtools.txt")
        if blobtools_file:
            logging.info(f"Getting organism from blobtools in {blobtools_file[0]}")
            blobtools_df   = pd.read_table(blobtools_file[0], sep="\t")
            if not blobtools_df.empty:
                # filtering the blobtools results
                values_to_drop = ['undef', 'all', 'missing']
                blobtools_df = blobtools_df[~blobtools_df.isin(values_to_drop).any(axis=1)]
                blobtools_df = blobtools_df[blobtools_df['bam0_read_map_p'] >= 70]
                if not blobtools_df.empty:
                    blobtools_df = blobtools_df.sort_values('bam0_read_map_p', ascending=False)
                    organism = blobtools_df.iloc[0]['name']
                    
                    # fix Excherichia/Shigella mixups
                    if 'Shigella' in organism or 'Escherichia' in organism:
                        blobtools_df = blobtools_df[blobtools_df['name'].str.contains(org_check, case=False)]
                        if not blobtools_df.empty:
                            organism = blobtools_df.iloc[0]['name']
                        else:
                            organism = 'unknown'

    # checking mash next
    if organism == 'unknown':
        mash_file = glob.glob(f"{args.grandeur}/mash/{sample}-UT*summary.mash.csv")
        logging.info(f"Getting organism from mash in {mash_file[0]}")
        if mash_file:
            mash_df   = pd.read_table(mash_file[0], sep=",")
            if not mash_df.empty:
                # filtering the mash dataframe
                mash_df = mash_df[mash_df['P-value'] <= 0.1]
                mash_df = mash_df[mash_df['mash-distance'] <= 0.25]
                if not mash_df.empty:
                    mash_df = mash_df.sort_values(by=['P-value', 'mash-distance'])
                    organism = mash_df.iloc[0]['organism']

                    # fix Excherichia/Shigella mixups
                    if 'Shigella' in organism or 'Escherichia' in organism:
                        mash_df = mash_df[mash_df['organism'].str.contains(org_check, case=False)]
                        if not mash_df.empty:
                            organism = mash_df.iloc[0]['organism']
                        else:
                            organism = 'unknown'

    # last ditch effort
    if organism == 'unknown':    
        kraken2_file = glob.glob(f"{args.grandeur}/kraken2/{sample}-UT*summary_kraken2.csv")
        if kraken2_file:
            logging.info(f"Getting organism from kraken2 in {kraken2_file[0]}")
            kraken2_df   = pd.read_table(kraken2_file[0], sep=",")
            if not kraken2_df.empty:
                # filtering the kraken2 file
                kraken2_df = kraken2_df[kraken2_df["Percentage of fragments"] >= 0.6]
                if not kraken2_df.empty:
                    kraken2_df = kraken2_df.sort_values("Percentage of fragments", ascending=False)
                    organism = kraken2_df.iloc[0]['Scientific name']

                    # fix Excherichia/Shigella mixups
                    if 'Shigella' in organism or 'Escherichia' in organism:
                        kraken2_df = kraken2_df[kraken2_df['Scientific name'].str.contains(org_check, case=False)]
                        if not kraken2_df.empty:
                            organism = kraken2_df.iloc[0]['Scientific name']
                        else:
                            organism = 'unknown'

def pass_fail(df, args):
    """

    Uses coverage to set some basic pass/fail conditions.
    
    Args:
        df (pd.Dataframe): results thus far.
        args (argparse.Namespace): Parsed command-line arguments.

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

    return df


def results_for_sample(sample, args):
    """

    Creates pandas dataframe from Grandeur results.
    
    Args:
        sample (str): sample id
        args (argparse.Namespace): Parsed command-line arguments.
    
    Returns:
        df (pd.Dataframe): Pandas dataframe of the parsed output.

    """

    df = pd.DataFrame(columns=['ARLN WGS ID', 'WGS MLST'])
    df.loc[0, 'ARLN WGS ID'] = sample
    df.loc[0, 'WGS MLST'] = mlst_results(sample, args)
    df = amrfinder_results(sample, df, args)
    df.loc[0, 'WGS Organism'] = organism_results(sample, df, args)
    return df


def sample_sheet_to_df(args):
    """

    Creates pandas dataframe from MiSeq sample sheet.
    
    Args:
        args (argparse.Namespace): Parsed command-line arguments.
    
    Returns:
        df (pd.Dataframe): Pandas dataframe of the parsed output.

    """

    logging.info(f"Getting samples from {args.samplesheet}")

    if os.path.exists(args.samplesheet):
        # get all the samples from the sample sheet into a pandas dataframe
        df = read_miseq_sample_sheet(args.samplesheet, "sample_id")
        df['LIMS_TEST_ID'] = df['Sample_ID'].str.replace(  '-UT.*','', regex=True)
        df['ARLN WGS ID']  = df['Sample_Name'].str.replace('-UT.*','', regex=True)
        if args.run:
            df['Run Name'] = args.run
        else:
            df['Run Name'] = df['Sample_Project']

        return df

    else:
        logging.fatal('Sample sheet could not be located! (Specify with -s)')
        sys.exit(1)

def main():
    """

    Parses output from Grandeur version 3.
    
    Args:
        args (argparse.Namespace): Parsed command-line arguments.
    
    Prints:
        files (str): Files for Results tab and ARLN Regional tab.
    
    """

    logging.basicConfig(format='%(asctime)s - %(message)s', datefmt = '%y-%b-%d %H:%M:%S', level=logging.INFO)

    version = '0.4.24348'

    parser = argparse.ArgumentParser()
    parser.add_argument('-g', '--grandeur',    type=str, help='directory where Grandeur has output results', required=True)
    parser.add_argument('-s', '--samplesheet', type=str, help='sample sheet for run',                        required=True)
    parser.add_argument('-o', '--outdir',      type=str, help='location for final files', default='lw8_files')
    parser.add_argument('-r', '--run',         type=str, help='run name (i.e. \'UT-M70330-241118\'', required=False)
    parser.add_argument('-v', '--version',               help='print version and exit', action='version', version='%(prog)s ' + version)
    args   = parser.parse_args()

    column_names = [
        "LIMS_TEST_ID",
        "ARLN WGS ID",
        "WGS Organism",
        "WGS MLST",
        "Run Name",
        "Genomic Coverage",
        "AMR Genes Identified",
        "Virulence Genes Identified",
        "SRA Accession",
        "BioSample Accession",
        "GenBank Accession",
        "Passed QC",
        "GC WGS ID",
        "GC Percent",
        "Avg PHRED",
        "Clade",
        "IMP Gene",
        "IMP Genes Identified",
        "KPC Gene",
        "KPC Genes Identified",
        "MCR 1 Gene",
        "MCR 1 Genes Identified",
        "NDM Gene",
        "NDM Genes Identified",
        "OXA 48 Like Gene",
        "OXA 48 Like Genes Identified",
        "VIM Gene",
        "VIM Genes Identified",
        "MCR 2 Gene",
        "MCR 2 Genes Identified",
        "MCR 3 4 5 Gene",
        "MCR 3 4 5 Genes Identified",
        "OXA 24 40 Gene",
        "OXA 24 40 Genes Identified",
        "OXA 58 Gene",
        "OXA 58 Genes Identified",
        "OXA 23 Gene",
        "OXA 23 Genes Identified",
        "OXA 235 Gene",
        "OXA 235 Genes Identified",
        "OXA 51 Gene",
        "OXA 51 Genes Identified",
        "OXA 143 Gene",
        "OXA 143 Genes Identified",
        "CMY 2 Gene",
        "CMY 2 Genes Identified",
        "CTX M 14 Gene",
        "CTX M 14 Genes Identified",
        "CTX M 15 Gene",
        "CTX M 15 Genes Identified",
        "DHA Gene",
        "DHA Genes Identified",
        "SPM Gene",
        "SPM Genes Identified",
        "SIM Gene",
        "SIM Genes Identified",
        "IMI Gene",
        "IMI Genes Identified",
        "GES Gene",
        "GES Genes Identified",
        "GIM Gene",
        "GIM Genes Identified",
        "Other Gene Result",
        "Other Gene Result Identified"
    ]


    df = sample_sheet_to_df(args)

    df = grandeur_summary(df, args)

    df = create_columns(df, column_names)

    for sample in df['ARLN WGS ID']:
        sample_df = results_for_sample(sample, args)
        for col in sample_df.columns:
            df.loc[df['ARLN WGS ID'] == sample, col] = sample_df.iloc[0][col]

    create_files(df, column_names, args)


if __name__ == "__main__":
    main()