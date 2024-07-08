#!/usr/bin/env python3

import pandas as pd
import os
import sys
import argparse
import logging
import glob
from pathlib import Path

def find_files(sample_name, directory):
    files = list(Path(directory).glob(f"{sample_name}*fastq.gz"))
    if len(files) >=2:
        # Return the first two files, and there should only be two matches
        logging.debug(f"The two files found: {files}")
        return files[:2]
    else:
        logging.debug(f"Two files not found: {files}")

def find_header_line(file_path):
    with open(file_path, 'r') as file:
        for line_number, line in enumerate(file):
            if "sample_id" in line.lower():
                logging.debug(f"The line number in {file_path} was {line_number}")
                return line_number
    raise ValueError("Header line not found in file")

def read_miseq_sample_sheet(sample_sheet):
    # Find the number of lines to skip because it's sometimes variable
    lines_to_skip = find_header_line(sample_sheet)
    
    # Read the CSV file into a DataFrame, skipping the appropriate number of lines
    df = pd.read_csv(sample_sheet, skiprows=lines_to_skip)
    return df

def upload_sample_sheet_instructions(run, directory):
    logging.info("To get sample sheet to S3 bucket:")
    logging.info(f"cd {directory} && aws s3 cp --profile 155221691104_dhhs-uphl-biongs-dev --region us-west-2 aws_sample_sheet.csv s3://dhhs-uphl-omics-inputs-dev/{run}/aws_sample_sheet.csv")

def upload_reads_instructions(run, directory):
    logging.info("To get reads to S3 bucket:")
    logging.info(f"cd {directory} &&  ls *fastq.gz | parallel aws s3 cp --profile 155221691104_dhhs-uphl-biongs-dev --region us-west-2 {{}} s3://dhhs-uphl-omics-inputs-dev/{run}/{{}}")

def grandeur_sample_sheet(run, sample_sheet, directory):

    # S3 input directory
    final_dir=f"s3://dhhs-uphl-omics-inputs-dev/{run}/"

    # turn MiSeq sample sheet into pandas df
    df = read_miseq_sample_sheet(sample_sheet)

    # file location for aws
    sample_files = []

    # get fastq file for each sample in MiSeq sample sheet
    for index, row in df.iterrows():
        sample_name = row['Sample_Name']
        reads = find_files(sample_name, directory)
        # sometimes there are no reads
        if reads:
            sample_files.append({'sample': sample_name, 'fastq_1': final_dir + reads[0].name, 'fastq_2': final_dir + reads[1].name})

    # creating the final dataframe
    sample_file_df = pd.DataFrame(sample_files, columns=['sample', 'fastq_1', 'fastq_2'])
    sample_file_df = sample_file_df.sort_values(by='sample')
    sample_file_df.to_csv(directory + "aws_sample_sheet.csv", index=False)
    logging.info("DataFrame saved to aws_sample_sheet.csv.")
    upload_sample_sheet_instructions(run, directory)
    upload_reads_instructions(run, directory)

def main():
    logging.basicConfig(level=logging.INFO) 

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-r', '--run',
        required = True,
        type = str,
        help = 'MiSeq run (i.e. UT-M03999-240627)')
    parser.add_argument(
        '-s', '--samplesheet',
        required = False,
        type = str,
        help = 'sample sheet')
    parser.add_argument('-d', '--dir',
        required = False,
        type = str,
        help = 'directory with fastq files')
    args = parser.parse_args()

    # getting the sample sheet from some default locations
    if args.samplesheet is None or args.samplesheet.strip() == "":
        sample_sheet = f"/Volumes/IDGenomics_NAS/pulsenet_and_arln/{args.run}/reads/SampleSheet.csv"
    else:
        sample_sheet = args.samplesheet

    if not os.path.exists(sample_sheet):
        logging.fatal(f"Sample sheet {sample_sheet} does not exist!")
        sys.exit()

    # getting the directory of fastq files from some default locations
    if args.dir is None or args.dir.strip() == "":
        dir = f"/Volumes/IDGenomics_NAS/pulsenet_and_arln/{args.run}/reads/"
    else:
        dir = args.dir

    if not os.path.exists(dir):
        logging.fatal(f"Directory {dir} does not exist!")
        sys.exit()

    grandeur_sample_sheet(args.run, sample_sheet, dir)

if __name__ == "__main__":
    main()