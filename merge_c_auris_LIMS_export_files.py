#!/usr/bin/env python3

import pandas as pd
import os

# Get the current date in the format 'yymmdd'
current_date = pd.Timestamp.now().strftime('%y%m%d')

# Full paths to CSV files that have been copied from /Volumes/LABWARE/Shared_Files/PHT/C_AURIS_DAILY
colony_csv_file = "/Volumes/IDGenomics_NAS/pulsenet_and_arln/investigations/C_auris/complete_UPHL_analysis/C_auris_LIMS_export/C_AURIS_Positive_Colony_Daily.csv"
isolates_csv_file = "/Volumes/IDGenomics_NAS/pulsenet_and_arln/investigations/C_auris/complete_UPHL_analysis/C_auris_LIMS_export/C_AURIS_Positive_Isolates_Daily.csv"

# Full path to output Excel file
output_file_dir = f"/Volumes/IDGenomics_NAS/pulsenet_and_arln/investigations/C_auris/complete_UPHL_analysis/C_auris_LIMS_export/C_auris_LIMS_export_{current_date}"
output_file = f"{output_file_dir}/C_auris_LIMS_export_{current_date}.xlsx"

# Read CSV files into pandas DataFrames with proper encoding (try 'latin-1' if 'utf-8' isn't working)
try:
    colony_df = pd.read_csv(colony_csv_file, encoding='utf-8')
except UnicodeDecodeError:
    colony_df = pd.read_csv(colony_csv_file, encoding='latin-1')

try:
    isolates_df = pd.read_csv(isolates_csv_file, encoding='utf-8')
except UnicodeDecodeError:
    isolates_df = pd.read_csv(isolates_csv_file, encoding='latin-1')

# Remove duplicate 'ARLN_Specimen_ID' values and the first column 'ARLN_PHL' from 'C_AURIS_Positive_Colony_Daily.csv'
colony_df = colony_df.drop_duplicates(subset='ARLN_Specimen_ID', keep='first').drop(columns=['ARLN_PHL'])

# Remove duplicate 'ARLN_Specimen_ID' values from 'C_AURIS_Positive_Isolates_Daily.csv'
isolates_df = isolates_df.drop_duplicates(subset='ARLN_Specimen_ID', keep='first')

# Concatenate both DataFrames
result_df = pd.concat([colony_df, isolates_df])

# Create the parent directory if it doesn't exist
os.makedirs(output_file_dir, exist_ok=True)

# Save the merged DataFrame as an Excel file
result_df.to_excel(output_file, index=False)

print("CSV files have been merged and saved as an Excel file:", output_file)

# Remove the original CSV files
os.remove(colony_csv_file)
os.remove(isolates_csv_file)

print("Original CSV files have been removed.")

