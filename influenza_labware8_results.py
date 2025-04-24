#!/usr/bin/env python3

"""
Author: Tom Iverson
Description:
    This script processes influenza sequencing results for Labware 8 input. It gathers the 'RunName' from the SampleSheet.csv file 
    then filters the rows where 'ProjectName' starts with 'FLUSeq_*'. It then uses the summary_report.tsv file, output from the 
    walkercreek workflow, to create Labware8-compatible txt files per sample, a merged txt summary, and a csv summary. Samples 
    missing from the summary_report.tsv file are marked as 'No Data Found' in the summary csv file and added to a missing ids txt
    file to alert of any samples may have failed to sequence.

Required Files:
    - SampleSheet.csv (must contain [BCLConvert_Data] and [Cloud_Data] sections)
    - summary_report.tsv (workflow output)

Usage:
    python influenza_labware8.py -r <summary_report.tsv> -s <SampleSheet.csv> -o <output_dir>
"""

import argparse
import pandas as pd
import logging
from pathlib import Path
from io import StringIO

VERSION = '1.2.0'

def parse_args():
    parser = argparse.ArgumentParser(description="Process Influenza sequencing results for Labware 8 input.")
    parser.add_argument('-r', '--report', required=True, help='Path to summary_report.tsv file')
    parser.add_argument('-s', '--samplesheet', required=True, help='Path to SampleSheet.csv file')
    parser.add_argument('-o', '--output', default="labware8_NGS_INF_SEQ_results", help='Output directory (default: labware8_NGS_INF_SEQ_results)')
    parser.add_argument('--include-subtypes', default="H1N1,H2N2,H3N2,H5N1,H7N3,H7N7,H7N9,H9N2,H10N8,Victoria,Yamagata",
                        help='Comma-separated list of subtypes to consider as valid')
    return parser.parse_args()

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def extract_section(lines, section_name):
    """
    Extracts a block of lines from a given section ([BCLConvert_Data] or [Cloud_Data]). Returns only the table lines below the
    section header.
    """
    start_idx, end_idx = None, None
    for i, line in enumerate(lines):
        if line.strip() == section_name:
            start_idx = i + 1
        elif start_idx and line.startswith("["):
            end_idx = i
            break
    return lines[start_idx:end_idx or len(lines)]

def extract_run_name(lines):
    """
    Extracts the run name from the [Header] section in SampleSheet.csv.
    """
    for line in lines:
        if line.startswith("RunName,"):
            return line.split(",")[1].strip()
    return "Unknown_Run"

def determine_type(irma_type):
    """
    Converts IRMA_type ('Type_A' or 'Type_B') into simplified 'A' or 'B' and returns 'No Type Detected' if input is None or 
    unrecognized.
    """
    if pd.notna(irma_type):
        return "A" if "Type_A" in irma_type else "B" if "Type_B" in irma_type else "No Type Detected"
    return "No Type Detected"

def determine_subtype(row, valid_subtypes):
    """
    Determines the influenza subtype from IRMA_subtype or abricate_InsaFlu_subtype and returns a matching subtype if found, else returns 'No 
    Subtype Detected'.
    """
    if row.get('IRMA_subtype') in valid_subtypes:
        return row['IRMA_subtype']
    if row.get('abricate_InsaFlu_subtype') in valid_subtypes:
        return row['abricate_InsaFlu_subtype']
    return "No Subtype Detected"

def determine_passed_qc(row, valid_subtypes):
    """
    Determines whether a sample passed QC based on IRMA_subtype or abricate_InsaFlu_subtype results. Returns 'PASS' if the detected subtype is in the
    valid_subtypes list, otherwise 'FAIL'.
    """
    if row.get('IRMA_type') in ['Type_A', 'Type_B']:
        if row.get('IRMA_subtype') in valid_subtypes:
            return "PASS"
        if row.get('abricate_InsaFlu_subtype') in valid_subtypes:
            return "PASS"
    return "FAIL"

def main():
    args = parse_args()
    setup_logging()
    valid_subtypes = set(args.include_subtypes.split(','))
    output_dir = Path(args.output)
    txt_output_dir = output_dir / "labware8_NGS_INF_SEQ_results"
    output_dir.mkdir(parents=True, exist_ok=True)
    txt_output_dir.mkdir(parents=True, exist_ok=True)

    # Load SampleSheet
    with open(args.samplesheet, 'r') as f:
        lines = f.readlines()

    run_name = extract_run_name(lines)
    logging.info(f"Run Name: {run_name}")

    # Extract [BCLConvert_Data] and [Cloud_Data]
    bcl_data = extract_section(lines, "[BCLConvert_Data]")
    cloud_data = extract_section(lines, "[Cloud_Data]")

    bcl_df = pd.read_csv(StringIO("".join(bcl_data)), sep=",", dtype=str)
    cloud_df = pd.read_csv(StringIO("".join(cloud_data)), sep=",", dtype=str)

    # Merge on Sample_ID and filter to ProjectName startswith FLUSeq
    merged_samples = bcl_df.merge(cloud_df[['Sample_ID', 'ProjectName']], on='Sample_ID', how='left')
    flu_samples = merged_samples[merged_samples['ProjectName'].str.startswith("FLUSeq", na=False)].copy()
    flu_samples['LIMS_TEST_ID'] = flu_samples['Sample_ID'].str.split('_').str[0]

    if flu_samples.empty:
        logging.error("No samples found with ProjectName starting with 'FLUSeq'.")
        return

    logging.info(f"Found {len(flu_samples)} FLUSeq samples to process.")

    # Read summary_report.tsv and map LIMS_TEST_ID
    summary_df = pd.read_csv(args.report, sep='\t', dtype=str)
    summary_df['LIMS_TEST_ID'] = summary_df['Sample'].str.split('_').str[0]

    # Merge summary_report.tsv data to FLUSeq samples
    df = flu_samples[['LIMS_TEST_ID']].merge(summary_df, on='LIMS_TEST_ID', how='left')

    # Identify unmatched LIMS_TEST_IDs
    all_flu_ids = flu_samples['LIMS_TEST_ID'].tolist()
    found_ids = summary_df['LIMS_TEST_ID'].unique().tolist()
    missing_ids = sorted(set(all_flu_ids) - set(found_ids))

    if missing_ids:
        logging.warning(f"{len(missing_ids)} FLUSeq samples missing from summary_report.tsv:")
        for mid in missing_ids:
            logging.warning(f" - {mid}")
        # Drop unmatched LIMS_TEST_IDs from the merged DataFrame
        df = df[~df['LIMS_TEST_ID'].isin(missing_ids)]

    # Export missing IDs to a file
    missing_ids_file = output_dir / f"{run_name}_missing_ids.txt"
    with open(missing_ids_file, 'w') as f:
        if missing_ids:
            for mid in missing_ids:
                f.write(f"{mid}\n")
        else:
            f.write("0\n")
    logging.info(f"Missing sample ID list written to: {missing_ids_file.name}")

    # Update only rows with actual IRMA data (do NOT overwrite manually added values)
    has_irma = df['IRMA_type'].notna() if 'IRMA_type' in df.columns else pd.Series([False] * len(df))

    if 'IRMA_type' in df.columns:
        df.loc[has_irma, 'Type'] = df.loc[has_irma, 'IRMA_type'].apply(determine_type)
    else:
        df['Type'] = df.get('Type', 'No Type Detected')

    if 'IRMA_subtype' in df.columns or 'abricate_InsaFlu_subtype' in df.columns:
        df.loc[has_irma, 'Subtype'] = df.loc[has_irma].apply(lambda row: determine_subtype(row, valid_subtypes), axis=1)
    else:
        df['Subtype'] = df.get('Subtype', 'No Subtype Detected')

    if 'IRMA_type' in df.columns:
        df.loc[has_irma, 'Passed QC'] = df.loc[has_irma].apply(lambda row: determine_passed_qc(row, valid_subtypes), axis=1)
    else:
        df['Passed QC'] = df.get('Passed QC', 'FAIL')

    # Fill any missing values with safe defaults for unmatched rows
    df['Type'] = df['Type'].fillna("No Type Detected")
    df['Subtype'] = df['Subtype'].fillna("No Subtype Detected")
    df['Passed QC'] = df['Passed QC'].fillna("FAIL")

    # Safely assign 'Nextclade Clade' using 'clade' column if it exists
    if 'clade' in df.columns:
        df['Nextclade Clade'] = df['clade'].fillna("No Nextclade Clade Detected")
    else:
        df['Nextclade Clade'] = "No Nextclade Clade Detected"
        
    df['WGS Organism'] = df.get('WGS Organism')
    df['WGS Organism'] = df['WGS Organism'].fillna("Influenza")
    df['Run Name'] = run_name
    df['Submission Accession'] = df.get('Submission Accession', "")

    # Final output DataFrame
    final_columns = [
        'LIMS_TEST_ID', 'Run Name', 'Submission Accession', 'WGS Organism',
        'Passed QC', 'Type', 'Subtype', 'Nextclade Clade'
    ]
    df_final = df[final_columns]

    # Generate individual .txt files (only if subtype is known)
    all_txt_data = []
    for _, row in df_final.iterrows():
        if row['Subtype'] == "No Data Found":
            continue  # skip unmatched samples for individual .txt
        file_path = txt_output_dir / f"{row['LIMS_TEST_ID']}_{run_name}_inf_results.txt"
        row.to_frame().T.to_csv(file_path, index=False, sep=',', lineterminator="\r\n")
        logging.info(f"Created {file_path.name}")
        all_txt_data.append(row.to_frame().T)

    # Merged .txt file
    if all_txt_data:
        merged_txt_path = output_dir / f"{run_name}_labware8_inf_results_summary.txt"
        pd.concat(all_txt_data, ignore_index=True).to_csv(merged_txt_path, index=False, sep=',', lineterminator="\r\n")
        logging.info(f"Merged TXT file created: {merged_txt_path.name}")
    else:
        logging.warning("No valid data found to write merged TXT file.")

    # Summary .csv 
    summary_csv_path = output_dir / f"{run_name}_labware8_inf_results_summary.csv"
    df_sorted = df_final.sort_values(by=['Passed QC', 'Type', 'Subtype', 'Nextclade Clade', 'LIMS_TEST_ID'], ascending=[False, True, True, True, True])
    df_sorted.to_csv(summary_csv_path, index=False)
    logging.info(f"Summary CSV created: {summary_csv_path.name}")

    # Version file
    with open(output_dir / "version.txt", "w") as f:
        f.write(f"Script version: {VERSION}\n")

    logging.info("Processing complete.")

if __name__ == "__main__":
    main()
