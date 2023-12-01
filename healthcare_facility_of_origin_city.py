import pandas as pd  # data manipulation
import logging  # log errors and information
import sys  # system-specific parameters and functions

"""
Author: Tom Iverson
Released: 2023-11-30
Version: 1.0.0
Description:
This script's main functionality is to determine a samples' city from the C. auris LIMS export data (ARLN_Specimen_ID, Healthcare_facility_of_origin_name, and Healthcare_facility_of_origin_state).
It does this by taking a 'samples.txt' file that the user has created with the following headers "ARLN_Specimen_ID, Healthcare_facility_of_origin_name, Healthcare_facility_of_origin_state" and merges
the data with 'C_auris_Healthcare_Facility_of_origin_name_city_state.txt'.
EXAMPLE:
python healthcare_facility_of_origin_city.py
"""

# Function to read data from a file
def read_data(file_path, sep='\t'):
    try:
        return pd.read_csv(file_path, sep=sep)  # Read the file using pandas
    except Exception as e:
        logging.error(f"Error reading {file_path}: {e}")  # Log any errors during file reading
        sys.exit(1)  # Exit the script in case of an error

# Function to merge dataframes
def merge_data(samples_df, facilities_df):
    try:
        # Merge the dataframes on specified columns using a left join
        return pd.merge(samples_df, facilities_df, on=['Healthcare_facility_of_origin_name', 'Healthcare_facility_of_origin_state'], how='left')
    except Exception as e:
        logging.error(f"Error merging data: {e}")  # Log any errors during merging
        sys.exit(1)  # Exit the script in case of an error

# Main function to execute the script
def main(samples_file, facilities_file, output_file):
    logging.basicConfig(level=logging.INFO)  # Set up the logging configuration
    
    samples_df = read_data(samples_file)  # Read the first data file (samples.txt)
    facilities_df = read_data(facilities_file)  # Read the second data file (C_auris_Healthcare_Facility_of_origin_name_city_state.txt)

    merged_df = merge_data(samples_df, facilities_df)  # Merge the dataframes
    # Fill in missing values in a specific column with 'NULL'
    merged_df['Healthcare_facility_of_origin_city'] = merged_df['Healthcare_facility_of_origin_city'].fillna('NULL')

    try:
        # Write the merged dataframe to an Excel file
        merged_df.to_excel(output_file, index=False)
        logging.info(f"Merge complete. Output saved to '{output_file}'.")  # Log successful completion
    except Exception as e:
        logging.error(f"Error writing to Excel: {e}")  # Log any errors during file writing

# Check if the script is the main program and not imported
if __name__ == "__main__":
    # Calling the main function with predefined file names
    main('samples.txt', 'C_auris_Healthcare_Facility_of_origin_name_city_state.txt', 'facility_city_output.xlsx')
