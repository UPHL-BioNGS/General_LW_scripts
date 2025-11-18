import os
from Bio import SeqIO
import pandas as pd

# --- User Input Section ---
print("--- FASTA Merging Setup ---")
input_folder1 = input("Enter the path for the FASTA input folder (ML tree preparation): ")
input_folder2 = input("Enter the path for the FASTA input folder (BEAST preparation): ")

# Define output paths for the FASTA merging (you can make these inputs too if desired)
output_file1 = "measles_merged_ML.fasta"
output_file2 = "measles_merged_Beast.fasta"

print("\n--- CSV Processing Setup ---")
input_csv = input("Enter the path for the input CSV file: ")
# Define output path for the TSV (you can make this an input too if desired)
output_tsv = "measles_dates.txt"


# --- FASTA Merging Function (First Block) ---
def merge_fasta_files(input_folder, output_file):
    """
    Finds all .fa files in a folder, merges them into a single FASTA file,
    and replaces each sequence header with its original filename (prefix).
    """
    try:
        # Get all FASTA files in the folder
        fasta_files = [f for f in os.listdir(input_folder) if f.endswith(".fa")]
        
        

        with open(output_file, "w") as out_f:
            for file in fasta_files:
                file_path = os.path.join(input_folder, file)
                # Extract filename without extension for the new header
                file_prefix = os.path.splitext(file)[0]

                with open(file_path, "r") as in_f:
                    for record in SeqIO.parse(in_f, "fasta"):
                        record.id = file_prefix       # Replace header with filename
                        record.description = ""       # Remove any additional description
                        SeqIO.write(record, out_f, "fasta")

        print(f"Merged {len(fasta_files)} FASTA files from '{input_folder}' into '{output_file}' with modified headers.")
    except FileNotFoundError:
        print(f"Error: The input folder '{input_folder}' was not found.")
    except Exception as e:
        print(f"An error occurred during FASTA merging for '{input_folder}': {e}")

# Run the FASTA merging for both paths
merge_fasta_files(input_folder1, output_file1)
merge_fasta_files(input_folder2, output_file2)

print("-" * 40)

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
        df = pd.read_csv(input_csv, dtype={'UPHL ID #': str})

        # 2. Remove rows where the required columns are null or missing.
        df_filtered = df.dropna(subset=['UPHL ID #', 'Collection Date'])
        
        # 3. Select only the required columns.
        df_filtered = df_filtered[['UPHL ID #', 'Collection Date']]

        # 4. Rename the columns to "Accession" and "Date".
        df_final = df_filtered.rename(
            columns={'UPHL_lab_accession': 'Accession', 
                     'Collection Date': 'Date'}
        )

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
process_data(input_csv, output_tsv)