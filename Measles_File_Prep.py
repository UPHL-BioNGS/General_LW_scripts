import os
from Bio import SeqIO
import pandas as pd

# --- User Input Section ---
input_csv = input("Enter the path to Measles_Metadata.csv: ")


# --- CSV Processing Function (Second Block) ---
def process_data(input_csv, output_tsv):
    """
    Reads a CSV, filters rows without required accession or date, and saves
    the accession number and date columns to a TSV file.
    
    Args:
        input_csv (str): The path to the input CSV file.
        output_tsv (str): The path to the output TSV file.
    """
    try:
        # 1. Read the CSV file into a pandas DataFrame.
        # Assuming 'UPHL_lab_accession' and 'patient_disease_onset_date' are the column names.
        df = pd.read_csv(input_csv, dtype={'UPHL_lab_accession': str})

        # 2. Remove rows where the required columns are null or missing.
        df_filtered = df.dropna(subset=['UPHL_lab_accession'])
        df_filtered = df_filtered.dropna(subset=['patient_disease_onset_date'])
        
        # 3. Select only the "Accession" and "Date" columns.
        df_filtered = df_filtered[['UPHL_lab_accession', 'patient_disease_onset_date']]

        # 4. Rename the columns to "Accession" and "Date".
        df_final = df_filtered.rename(columns={'UPHL_lab_accession': 'Accession', 'patient_disease_onset_date': 'Date'})

        # 5. Save the new DataFrame to a TSV file.
        df_final.to_csv(output_tsv, sep='\t', index=False)

        print(f"Successfully processed data. Filtered data saved to '{output_tsv}'.")

    except FileNotFoundError:
        print(f"Error: The file '{input_csv}' was not found.")
    except KeyError as e:
        print(f"Error: A required column was not found. Please check your column names. Missing column: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during CSV processing: {e}")

# Run the CSV processing block
process_data(input_csv, 'measles_dates.txt')
