#!/usr/bin/env python3

"""
Author: Erin Young
Updated: 2025-03-20
Version: 0.0.2
Description:
    This script isn't intended to be used alone, but it contains the functions
    for converting a sample sheet to a pandas dataframe.

    Since the line where the dataframe should begin is variable, it first 
    performs a check for the header line.

EXAMPLE:
    python3 samplesheet_to_df.py -s sample_sheet.csv -o new_sample_sheet.csv 
"""

import argparse
import logging
import os
import pandas as pd

from miseq_i100_samplesheet_to_df import read_miseq_i100_sample_sheet

def contains_sample_name(file_path):
    with open(file_path, 'r') as file:
        for line in file:
            if 'Sample_Name' in line:
                return True
    return False

def find_header_line(file_path, header_signal='sample_id'):
    """
    Uses a string to search for the first line where the dataframe should begin.

    Args:
        file_path (str): Path to the sample sheet file.
        header_signal (str): String found in the header line (e.g., "sample_id").

    Returns:
        int: The line number where pandas should start creating a dataframe.
    """
    with open(file_path, 'r') as file:
        for line_number, line in enumerate(file):
            if header_signal in line.lower():
                logging.debug(f"The line number in {file_path} was {line_number}")
                return line_number
    raise ValueError('Header line not found in file')

def read_miseq_sample_sheet(sample_sheet, header_signal='sample_id'):
    """
    Converts MiSeq Sample Sheet into a pandas dataframe.

    Args:
        sample_sheet (str): Path to the MiSeq sample sheet.
        header_signal (str): String found in the header line (e.g., "sample_id").

    Returns:
        pd.DataFrame: Pandas dataframe containing the information in the sample sheet.
    """

    df = pd.DataFrame()
    if contains_sample_name(sample_sheet):
        lines_to_skip = find_header_line(sample_sheet, header_signal)
        df = pd.read_csv(sample_sheet, skiprows=lines_to_skip)
    else:
        df = read_miseq_i100_sample_sheet(sample_sheet)

    return df

def main():
    """
    Converts MiSeq Sample Sheet into a pandas dataframe and writes it to a CSV file.
    """
    logging.basicConfig(level=logging.INFO) 
    
    parser = argparse.ArgumentParser(description='Converts Sample Sheet into a pandas dataframe')

    parser.add_argument('-s', '--sample_sheet', type=str, required=True, help='Path to the sample sheet file.')
    parser.add_argument('-d', '--header', type=str, required=False, default='sample_id', help='String found in the header line.')
    parser.add_argument('-o', '--out', type=str, required=False, default='sample_sheet.csv', help='Output file path.')

    args = parser.parse_args()
    
    if not os.path.exists(args.sample_sheet):
        raise FileNotFoundError(f"The file {args.sample_sheet} does not exist.")

    df = read_miseq_sample_sheet(args.sample_sheet, args.header)
    df.to_csv(args.out, index=False)

if __name__ == '__main__':
    main()
