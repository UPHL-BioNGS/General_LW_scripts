#!/usr/bin/env python3

"""
Author: Erin Young
Released: 2025-03-20
Version: 0.0.1
Description:
    This script isn't intended to be used alone, but it contains the functions
    for converting a sample sheet for the miseq i100 to a pandas dataframe.

    Since the line where the dataframe should begin is variable, it first 
    performs a check for the header line.

EXAMPLE:
    python3 samplesheet_to_df.py -s sample_sheet.csv -o new_sample_sheet.csv 
"""

import argparse
import logging
import os
import pandas as pd

def read_miseq_i100_sample_sheet(sample_sheet):
    """
    Converts MiSeq i100 Sample Sheet into a pandas dataframe.

    Args:
        sample_sheet (str): Path to the MiSeq sample sheet.

    Returns:
        pd.DataFrame: Pandas dataframe containing the information in the sample sheet.
    """
    
    with open(sample_sheet, 'r') as file:
        lines = file.readlines()

        start_index = None
        for i, line in enumerate(lines):
            if line.strip() == "[BCLConvert_Data]":
                start_index = i + 1
                break

        if start_index is None:
            raise ValueError("BCLConvert_Data section not found")

        data_lines = []
        for line in lines[start_index:]:
            if line.startswith('['): 
                break
            data_lines.append(line.strip())

        df = pd.DataFrame([x.split(',') for x in data_lines[1:]], columns=data_lines[0].split(','))
        df = df[df["Sample_ID"].str.strip() != ""]
        df["Sample_Name"] = df["Sample_ID"]

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

    df = read_miseq_i100_sample_sheet(args.sample_sheet)
    df.to_csv(args.out, index=False)

if __name__ == '__main__':
    main()
