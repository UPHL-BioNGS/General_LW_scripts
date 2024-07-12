#!/usr/bin/env python3

"""
Author: Erin Young
Released: 2024-07-11
Version: 0.0.1
Description:
    This script isn't intended to be used alone, but it contains the functions
    for downloading fastq files given a run name from basespace.

EXAMPLE:
    python3 bssh_reads_by_run.py -r UT-M70330-240131 -o  /Volumes/IDGenomics_NAS/pulsenet_and_arln/UT-M70330-240131/reads
"""


import argparse
import logging
import subprocess
import re
import concurrent.futures
import pandas as pd


def bs_out(bash_command):
    """
    Parses output from basespace (bs)

    Args:
        bash_command (str): bs cli command

    Returns:
        df (pd.Dataframe): Pandas dataframe of the parsed output.
    """
    process = subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    stdout = output.decode('utf-8')
    stdout = stdout.split('\n')
    stdout.pop(0)
    stdout.pop(1)
    stdout.pop(-1)
    stdout.pop(-1)
    stdout = [x.replace('|', '') for x in stdout]
    stdout = [re.sub(r"\s+", ' ', x) for x in stdout]
    df = pd.DataFrame(columns = stdout[0].split(), 
                      data = [row.split()[0:4] for row in stdout[1:]])
    logging.debug(f"bs stdout {df}")
    return df


def download_from_bs(sample_id, out):
    """
    Uses a string to search for the first line where the dataframe should begin.

    Args:
        sample_id (str): sample id for fastq file
        out (str): directory reads are downloaded to
    """

    bash_command = f"bs download dataset --config=bioinfo --id={sample_id} --output={out}/ --retry"
    process = subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    
    logging.info(f"Fastq files for {sample_id} downloaded to {out}")


def download_reads(run, out):
    """
    Downloads reads from run into out directory.

    Args:
        run_name (str): run name
        out (str): destination directory for fastq files
    """

    idd  = get_run_id(run)
    idds = get_sample_ids(idd)

    # will run this in parallel to speed things up
    futures = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for id in idds: 
            futures.append(executor.submit(download_from_bs, id, out))
        
        for future in futures:
            logging.debug(future.result())


def get_run_id(run_name):
    """
    Uses a string to search for the first line where the dataframe should begin.

    Args:
        run_name (str): run name

    Returns:
        idd (str): The basespace id for that run
    """

    bash_command = 'bs list --config=bioinfo runs'
    df  = bs_out(bash_command)
    idd = df.loc[df['ExperimentName'] == run_name,'Id'].iloc[0]
    logging.info(f"Run id is {idd}")
    return idd


def get_sample_ids(idd):
    """
    Gets the sample ids for a sequencing run.

    Args:
        idd (str): id for sequencing run

    Returns:
        idds (list): basespace ids for each sample
    """

    bash_command = f"bs list dataset --config=bioinfo --input-run={idd} "
    df = bs_out(bash_command)

    # removing undetermined and None values
    df = df[df['Name'] != 'Undetermined']
    df = df[df['Id'].str.contains('None') == False]
    idds=list(df['Id'])
    logging.info(f"Reads ids are {idds}")
    return idds


def main():
    """
    Downloads fastq files from basespace by specifying run name. 

    Args:
        args (argparse.Namespace): Parsed command-line arguments.

    """
    
    logging.basicConfig(level=logging.INFO) 

    parser = argparse.ArgumentParser(description='Downloads reads from basespace')
    
    # Define your arguments here
    parser.add_argument('-r', '--run', type=str, required=True, help='Run name')
    parser.add_argument('-o', '--out', type=str, required=False, default='reads', help='Directory where fastq files are downloaded')
    
    # Parse the arguments
    args = parser.parse_args()
    
    download_reads(args.run, args.out)


if __name__ == '__main__':
    main()
