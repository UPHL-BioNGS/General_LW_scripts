#!/usr/bin/env python3

"""
Author: Tom Iverson

Description:
    This script processes influenza sequencing results for Labware 8 input. It gathers run name data from the sequencing 'SampleSheet.csv' file
    and results from the walkercreek workflow output 'summary_report.tsv' file to create individual Labware 8 input files (txt format)
    for each sample. It also generates a merged txt file and a CSV summary sorted by QC status and subtype.

Required Files:
    - SampleSheet.csv file (must contain sample ID and index information).
    - summary_report.tsv file (walkercreek workflow output).

Usage:
    python influenza_labware8.py -r <summary_report.tsv> -s <SampleSheet.csv> -o <output_directory> [--include-subtypes H1N1,H3N2,Victoria,Yamagata]
"""

import argparse
import pandas as pd
import logging
from pathlib import Path
from io import StringIO

VERSION = '1.0.0'

# Function to parse command-line arguments. Includes paths to input files and a customizable list of valid subtypes for QC determination.
def parse_args():
    parser = argparse.ArgumentParser(description="Process influenza sequencing results for Labware 8 input.")
    parser.add_argument('-r', '--report', required=True, help='Path to summary_report.tsv file')
    parser.add_argument('-s', '--samplesheet', required=True, help='Path to SampleSheet.csv file')
    parser.add_argument('-o', '--output', default="labware8_inf_results", help='Output directory (default: labware8_inf_results)')
    parser.add_argument('--include-subtypes', default="H1N1,H2N2,H3N2,H5N1,H7N3,H7N7,H7N9,H9N2,H10N8,Victoria,Yamagata",
                        help='Comma-separated list of subtypes to consider as valid (default includes both Victoria and Yamagata)')
    return parser.parse_args()

# Function to set up logging format and level (INFO).
def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Function to parse the SampleSheet.csv lines to extract the 'RunName' from the [Header] section. Returns 'Unknown_Run' if not found.
def extract_run_name(lines):
    for line in lines:
        if line.startswith("RunName,"):
            return line.split(",")[1].strip()
    return "Unknown_Run"

# Function to locate and extract the [BCLConvert_Data] table from the SampleSheet.csv file. Raises an error if the section is not found. Returns only the lines containing the actual data rows.
def extract_bclconvert_data(lines):
    start_idx, end_idx = None, None
    for i, line in enumerate(lines):
        if line.strip() == "[BCLConvert_Data]":
            start_idx = i + 1
        elif start_idx and line.startswith("["):
            end_idx = i
            break
    if start_idx is None:
        raise ValueError("Error: [BCLConvert_Data] section not found in SampleSheet.csv")
    return lines[start_idx:end_idx or len(lines)]

# Function to determine whether a sample passed QC based on IRMA or InsaFlu subtype results. Returns 'PASS' if the detected subtype is in the valid_subtypes list, otherwise 'FAIL'.
def determine_passed_qc(row, valid_subtypes):
    if row.get('IRMA_type') in ['Type_A', 'Type_B']:
        if row.get('IRMA_subtype') in valid_subtypes:
            return "PASS"
        if row.get('abricate_InsaFlu_subtype') in valid_subtypes:
            return "PASS"
    return "FAIL"

# Function that converts IRMA_type ('Type_A' or 'Type_B') into simplified 'A' or 'B' and returns 'No Type Detected' if input is None or unrecognized.
def determine_type(irma_type):
    if pd.notna(irma_type):
        return "A" if "Type_A" in irma_type else "B" if "Type_B" in irma_type else "No Type Detected"
    return "No Type Detected"

# Function that determines the influenza subtype from IRMA or InsaFlu annotations and returns a matching subtype if found, else returns 'No Subtype Detected'.
def determine_subtype(row, valid_subtypes):
    if row.get('IRMA_subtype') in valid_subtypes:
        return row['IRMA_subtype']
    if row.get('abricate_InsaFlu_subtype') in valid_subtypes:
        return row['abricate_InsaFlu_subtype']
    return "No Subtype Detected"

def main():
    args = parse_args()
    setup_logging()
    valid_subtypes = set(args.include_subtypes.split(','))

    output_dir = Path(args.output)
    txt_output_dir = output_dir / "labware8_inf_results"
    output_dir.mkdir(parents=True, exist_ok=True)
    txt_output_dir.mkdir(parents=True, exist_ok=True)

    # Process SampleSheet.csv
    with open(args.samplesheet, 'r') as f:
        lines = f.readlines()

    run_name = extract_run_name(lines)
    bcl_data = extract_bclconvert_data(lines)
    sample_sheet = pd.read_csv(StringIO("".join(bcl_data)), sep=",", dtype=str)
    sample_sheet['LIMS_TEST_ID'] = sample_sheet['Sample_ID'].str.split('_').str[0]

    logging.info(f"SampleSheet processed. Run Name: {run_name}")

    # Process summary_report.tsv
    summary_report = pd.read_csv(args.report, sep='\t', dtype=str)
    summary_report['LIMS_TEST_ID'] = summary_report['Sample'].str.split('_').str[0]

    # Merge on LIMS_TEST_ID
    df = sample_sheet[['LIMS_TEST_ID']].merge(summary_report, on='LIMS_TEST_ID', how='left')

    # Assign derived columns
    df['Passed QC'] = df.apply(lambda row: determine_passed_qc(row, valid_subtypes), axis=1)
    df['Type'] = df['IRMA_type'].apply(determine_type)
    df['Subtype'] = df.apply(lambda row: determine_subtype(row, valid_subtypes), axis=1)
    df['WGS Organism'] = "Influenza"
    df['Nextclade Clade'] = df['clade'].fillna("No Nextclade Clade Detected")
    df['Run Name'] = run_name
    df['Submission Accession'] = ""

    final_columns = [
        'LIMS_TEST_ID', 'Run Name', 'Submission Accession', 'WGS Organism',
        'Passed QC', 'Type', 'Subtype', 'Nextclade Clade'
    ]
    df_final = df[final_columns]

    # Write individual .txt files
    all_txt_data = []
    for _, row in df_final.iterrows():
        file_path = txt_output_dir / f"{row['LIMS_TEST_ID']}_inf_results.txt"
        row.to_frame().T.to_csv(file_path, index=False, sep=',', lineterminator="\r\n")
        logging.info(f"Created {file_path}")
        all_txt_data.append(row.to_frame().T)

    # Write merged .txt file
    merged_txt = pd.concat(all_txt_data, ignore_index=True)
    merged_txt_path = output_dir / f"{run_name}_labware8_inf_results_summary.txt"
    merged_txt.to_csv(merged_txt_path, index=False, sep=',', lineterminator="\r\n")
    logging.info(f"Merged TXT file created: {merged_txt_path}")

    # Write summary .csv file
    summary_csv_path = output_dir / f"{run_name}_labware8_inf_results_summary.csv"
    df_sorted = df_final.sort_values(by=['Passed QC', 'Type', 'Subtype', 'Nextclade Clade', 'LIMS_TEST_ID'], ascending=[False, True, True, True, True])
    df_sorted.to_csv(summary_csv_path, index=False)
    logging.info(f"Summary CSV created: {summary_csv_path}")

    # Write version
    with open(output_dir / "version.txt", "w") as f:
        f.write(f"Script version: {VERSION}\n")
    logging.info("Processing complete.")

if __name__ == "__main__":
    main()
