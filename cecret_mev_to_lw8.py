#!/usr/bin/env python3
import argparse
import pandas as pd
import os
import sys

def main():
    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(description="Convert Cecret results to LIMS import format.")
    
    # Positional arguments (or use flags like --run_name if preferred)
    parser.add_argument("-r", "--run_name", required=True, help="Name of the run (e.g., UT-VH00770-251017)")
    parser.add_argument("-c", "--results", required=True, help="Path to the cecret_results.csv file")
    parser.add_argument("-s", "--samplesheet", required=True, help="Path to the SampleSheet.csv file")
    parser.add_argument("-o", "--output", help="Output filename (default: cecret_mev_\{run_name\}.txt)")

    args = parser.parse_args()
    
    input_results = args.results
    input_samplesheet = args.samplesheet
    run_name = args.run_name
    if args.output:
        output_file = args.output
    else:
        output_file = f"cecret_mev_{run_name}.txt"
    
    # Check file existence
    if not os.path.exists(input_results):
        print(f"Error: Results file '{input_results}' not found.")
        sys.exit(1)
    if not os.path.exists(input_samplesheet):
        print(f"Error: Sample sheet file '{input_samplesheet}' not found.")
        sys.exit(1)

    # --- 1. Parse SampleSheet.csv ---
    print(f"Processing SampleSheet: {input_samplesheet}...")
    sample_map = {} # Mapping Sample_ID -> Submission Accession (LibraryName)
    
    try:
        with open(input_samplesheet, 'r') as f:
            lines = f.readlines()
            
            # Find the data section containing 'Sample_ID' and 'LibraryName'
            header_index = -1
            for i, line in enumerate(lines):
                if 'Sample_ID' in line and 'LibraryName' in line:
                    header_index = i
                    break
            
            if header_index != -1:
                header = lines[header_index].strip().split(',')
                # Identify column indices
                try:
                    idx_sample_id = header.index('Sample_ID')
                    idx_library_name = header.index('LibraryName') # Submission Accession
                    
                    for line in lines[header_index+1:]:
                        parts = line.strip().split(',')
                        # Ensure line has enough parts
                        if len(parts) > max(idx_sample_id, idx_library_name):
                            s_id = parts[idx_sample_id].strip()
                            sub_acc = parts[idx_library_name].strip()
                            if s_id:
                                sample_map[s_id] = sub_acc
                except ValueError:
                    print("Warning: 'Sample_ID' or 'LibraryName' columns not found in SampleSheet header.")
            else:
                print("Warning: Data header with Sample_ID and LibraryName not found in SampleSheet.")
                
    except Exception as e:
        print(f"Error reading SampleSheet: {e}")
        sys.exit(1)

    # --- 2. Process Results ---
    print(f"Processing Results: {input_results}...")
    try:
        cecret_df = pd.read_csv(input_results)
    except Exception as e:
        print(f"Error reading results CSV: {e}")
        sys.exit(1)
    
    output_rows = []
    
    for i, row in cecret_df.iterrows():
        s_id = str(row['sample_id'])
        
        # Map Columns
        submission_accession = sample_map.get(s_id, "")
        
        # Organism
        organism = "Morbillivirus hominis"
        
        # QC Status
        # Using 'vadr_p/f' column (PASS/FAIL)
        passed_qc = row.get('vadr_p/f', 'FAIL') 
        
        # Clade Logic
        clade = str(row.get('nextclade_clade', ''))
        b3 = "NOT_DETECT"
        d4 = "NOT_DETECT"
        d8 = "NOT_DETECT"
        h1 = "NOT_DETECT"
        other_clade = ""
        
        if clade == 'B3':
            b3 = "DETECTED"
        elif clade == 'D4':
            d4 = "DETECTED"
        elif clade == 'D8':
            d8 = "DETECTED"
        elif clade == 'H1':
            h1 = "DETECTED"
        elif clade and clade.lower() != 'nan':
            other_clade = clade

        output_rows.append({
            "LIMS_TEST_ID": s_id,
            "Run Name": run_name,
            "Submission Accession": submission_accession,
            "Isolate Name": "",
            "WGS Organism": organism,
            "Passed QC": passed_qc,
            "Nextclade clade": clade,
            "B3": b3,
            "D4": d4,
            "D8": d8,
            "H1": h1,
            "Other Clade": other_clade
        })

    # --- 3. Create Output CSV ---
    columns = [
        "LIMS_TEST_ID", "Run Name", "Submission Accession", "Isolate Name",
        "WGS Organism", "Passed QC", "Nextclade clade", "B3", "D4", "D8", "H1", "Other Clade"
    ]
    
    output_df = pd.DataFrame(output_rows, columns=columns)
    
    # Save as .txt but in csv format
    output_df.to_csv(output_file, index=False)
    print(f"Successfully created {output_file}")

if __name__ == "__main__":
    main()