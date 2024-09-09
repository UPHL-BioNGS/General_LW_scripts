#!/usr/bin/env python3

"""
Author: Erin Young
Released: 2024-07-11
Version: 0.0.1
Description:
    This script should create a sample sheet for aws usage for donut falls as well as
    copy all files to a destination for upload.

EXAMPLE:
    python3 aws_samplesheet_df_create.py -r UT-M70330-240131 -s SampleSheet.csv -d reads
"""


import pandas as pd
import os
import sys
import argparse
import logging
from pathlib import Path


def concat_files():
    print("hwatever")

def illumina_files():
    print("whatever")

def upload_sample_sheet_instructions(run_name, directory):
    """

    Instruction for uploading the sample sheet
    (holding place for actual uploading)

    Args:
        run_name (str): run directory to upload to
        directory (str): where the sample sheet is located

    """
    logging.info("To get sample sheet to S3 bucket:")
    logging.info(f"cd {directory} && aws s3 cp --profile 155221691104_dhhs-uphl-biongs-dev --region us-west-2 aws_sample_sheet.csv s3://dhhs-uphl-omics-inputs-dev/{run_name}/aws_sample_sheet.csv")


def upload_reads_instructions(run_name, directory):
    """

    Instruction for uploading fastq files.
    (holding place for actual uploading)

    Args:
        run_name (str): run directory to upload to
        directory (str): where the files are located

    """

    logging.info("To get reads to S3 bucket:")
    logging.info(f"cd {directory} &&  ls *fastq.gz | parallel aws s3 cp --profile 155221691104_dhhs-uphl-biongs-dev --region us-west-2 {{}} s3://dhhs-uphl-omics-inputs-dev/{run_name}/{{}}")


def read_gridion_sample_sheet(samplesheet):
    print(samplesheet)

    df = pd.read_table(samplesheet)

    return df

def df_sample_sheet(run_name, samplesheet, directory):
    """

    Takes fastq file names and adds predicted paths for aws.

    Args:
        run_name (str): directory destination in aws (most commonly the run name)
        samplesheet (str): sample sheet used to generate the fastq files
        directory (str): directory that fastq files are located in

    """

    # S3 input directory
    final_dir=f"s3://dhhs-uphl-omics-inputs-dev/{run_name}/"

    # turn MiSeq sample sheet into pandas df
    df = read_gridion_sample_sheet(samplesheet)

    # file location for aws
    sample_files = []

    # get fastq file for each sample in GridIon sample sheet
    for index, row in df.iterrows():
        sample_name = row['Sample_Name']
        reads = concat_files(sample_name, directory)
        # sometimes there are no reads
        if reads:
            sample_files.append({'sample': sample_name, 'fastq': final_dir + reads[0].name, 'fastq_1': final_dir + reads[0].name, 'fastq_2': final_dir + reads[1].name})
        else:
            logging.debug(f"No fastq files were found for {sample_name}")

    # creating the final dataframe
    sample_file_df = pd.DataFrame(sample_files, columns=['sample', 'fastq_1', 'fastq_2'])
    sample_file_df = sample_file_df.sort_values(by='sample')
    sample_file_df.to_csv(f"{directory}/aws_sample_sheet.csv", index=False)

    logging.info("DataFrame saved to aws_sample_sheet.csv.")
    upload_sample_sheet_instructions(run_name, directory)
    upload_reads_instructions(run_name, directory)


def main():
    """

    Creates an AWS-friendly sample sheet.

    Args:
        args (argparse.Namespace): Parsed command-line arguments.
    
    """

    logging.basicConfig(level=logging.INFO) 

    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--run', required = True, type = str, help = 'Run name (i.e. UT-GXB04505-240621)')
    parser.add_argument('-s', '--samplesheet', required = True, type = str, help = 'sample sheet')
    parser.add_argument('-f', '--fastq_pass', required = True, type = str, help = 'fastq_pass directory with barcoded fastq files')
    parser.add_argument('-o', '--out', required=False, type=str, help='directory where files are copied to for upload')
    args = parser.parse_args()

    if not os.path.exists(args.samplesheet):
        logging.fatal(f"Sample sheet {args.samplesheet} does not exist!")
        sys.exit()

    if not os.path.exists(args.fastq_pass):
        logging.fatal(f"Directory {args.dir} does not exist!")
        sys.exit()

    df_sample_sheet(args.run, args.samplesheet, args.fastq_pass, args.out)


if __name__ == "__main__":
    main()