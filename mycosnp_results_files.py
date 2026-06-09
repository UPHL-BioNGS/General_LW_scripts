#!/usr/bin/env python3

'''
Author: Tom Iverson

Modification of Erin Young's script 'granduer_results_files.py' that collects needed files from mycosnp analyses for Labware 8 input:
1. C_auris tab
2. ARLN tab
3. Labware 8 input files: 
    b. ARLN samples

EXAMPLE:
python3 mycosnp_results_files.py -m <path to mycosnp_results> -s <input sample sheet>
'''

# dependencies
import argparse
import pandas as pd
import os
import glob

version = '1.0.0'

parser = argparse.ArgumentParser()
parser.add_argument('-m', '--mycosnp', type=str, help='directory where mycosnp has output results', default='mycosnp_results')
parser.add_argument('-s', '--samplesheet', type=str, help='sample sheet for run', default='SampleSheet.csv')
parser.add_argument('-l', '--list', type=str, help='list of samples for LabWare 8 upload', default='')
parser.add_argument('-v', '--version', help='print version and exit', action='version', version='%(prog)s ' + version)
args = parser.parse_args()

# Columns for final files
# C_auris tab
C_auris_cols = ['wgs_id', 'organism', 'Sample_Project', 'GC After Trimming', 'Average Q Score After Trimming', 'Reference Length Coverage After Trimming', 'Mean Coverage Depth', 'Pass']
# ARLN tab
arln_cols = ['wgs_id', 'organism', 'Sample_Project', 'GC After Trimming', 'Average Q Score After Trimming', 'Reference Length Coverage After Trimming']

# Function to get sample ids and run name from NextSeq 2k samplesheet
def read_samplesheet_nextseq(filename):
    sample_data = []
    found_data_section = False
    sample_project = None  # variable to store the Sample_Project value
    with open(filename, 'r') as file:
        for line in file:
            line = line.strip()
            if not found_data_section:
                if line.startswith('Sample_ID'):
                    found_data_section = True
            else:
                if line.startswith('['):
                    break  # stop parsing when encountering a new section in the samplesheet
                elif line:  # exclude empty lines
                    sample_data.append(line.split(','))  # appends only if the line is not empty
            if line.startswith('RunName'):
                sample_project = line.split(',')[1]  # extract the Sample_Project value
    
    # Convert the list of lists to a DataFrame for NextSeq 2k samplesheet
    df = pd.DataFrame(sample_data, columns=['Sample_ID', 'Index', 'Index2'])

    return sample_data, df, sample_project  # Return the Sample_Project value along with other data

# Function to get sample ids and run name from MiSeq samplesheet
def read_samplesheet_miseq(filename, column_names):
    sample_data = []
    found_data_section = False
    sample_project = None  # variable to store the Sample_Project value
    with open(filename, 'r') as file:
        for line in file:
            line = line.strip()
            if not found_data_section:
                if line.startswith('Sample_ID'):
                    found_data_section = True
            else:
                if line.startswith('['):
                    break  # stop parsing when encountering a new section in the samplesheet
                elif line:  # exclude empty lines
                    sample_data.append(dict(zip(column_names, line.split(','))))
            if line.startswith('Experiment Name'):
                sample_project = line.split(',')[1]  # extract the Sample_Project value

    # Convert the list of dictionaries to a DataFrame for MiSeq samplesheet
    df = pd.DataFrame(sample_data)

    # Print the extracted data for debugging
    print("Extracted data from MiSeq samplesheet:")

    return sample_data, df, sample_project  # Return the Sample_Project value along with other data

if os.path.exists(args.samplesheet):
    with open(args.samplesheet, 'r') as file:
        samplesheet_content = file.read()
    print('Getting samples from ' + args.samplesheet)
    if 'RunName' in samplesheet_content:
        sample_data, df, sample_project = read_samplesheet_nextseq(args.samplesheet)  

        df['lims_id'] = df['Sample_ID'].str.replace('-UT.*', '', regex=True)
        df['wgs_id'] = df['lims_id']
        df['Sample_Project'] = sample_project
        # Remove any rows with missing 'wgs_id' and 'Sample_ID'
        df = df.dropna(subset=['wgs_id', 'Sample_ID'], how='all')
    elif 'Experiment Name' in samplesheet_content:
        column_names = ['Sample_ID', 'Sample_Name', 'Description', 'Index_Plate', 'Index_Plate_Well',
                        'I7_Index_ID', 'index', 'I5_Index_ID', 'index2', 'Sample_Project', 'Description']
        sample_data, df, sample_project = read_samplesheet_miseq(args.samplesheet, column_names=column_names)  

        df['lims_id'] = df['Sample_ID'].str.replace('-UT.*', '', regex=True)
        df['wgs_id'] = df['lims_id']
        df['Sample_Project'] = sample_project
        # Remove any rows with missing 'wgs_id' and 'Sample_ID'
        df = df.dropna(subset=['wgs_id', 'Sample_ID'], how='all')
    else:
        print('Unknown samplesheet format! Please check the contents of the file.')
        exit(1)
else:
    print('Sample sheet could not be located! (Specify with -s)')
    exit(1)

# Add WGS organism "Candida auris"
if os.path.exists(args.mycosnp):
    print('Adding C. auris as organism')
    df['organism'] = 'Candida auris'

    df = pd.merge(df, df[['Sample_ID', 'organism']], left_on='Sample_ID', right_on='Sample_ID', how='left')
    df = df.drop('organism_y', axis=1)
    df = df.rename(columns={'organism_x': 'organism'})
else:
    print('FATAL: could not add C. auris to organism' )
    exit(1)

# Remove the '-UT' suffix from 'Sample_ID' in df
df['Sample_ID'] = df['Sample_ID'].str.replace(r'-UT.*', '', regex=True)

# Use glob to find the path to qc_report.txt
qc_report_path = os.path.join(args.mycosnp, '**', 'qc_report.txt')
qc_report_matches = glob.glob(qc_report_path, recursive=True)

if not qc_report_matches:
    print("qc_report.txt not found.")

# If there are multiple matches, take the first one
qc_report = qc_report_matches[0]

print('Extracting information from ' + qc_report)

# Get coverage, GC content, and average phred score from qc_report
qc_report_df = pd.read_csv(qc_report, delimiter='\t')
# Remove the '-UT' suffix from 'Sample Name' in qc_report_df
qc_report_df['Sample Name'] = qc_report_df['Sample Name'].astype(str)
qc_report_df['Sample Name'] = qc_report_df['Sample Name'].str.replace(r'-UT.*', '', regex=True)
df = pd.merge(df, qc_report_df[['Sample Name', 'GC After Trimming', 'Average Q Score After Trimming', 'Reference Length Coverage After Trimming', 'Mean Coverage Depth']], left_on='Sample_ID', right_on='Sample Name', how='left')
df.drop(columns=['Sample Name'], inplace=True)
df['Mean Coverage Depth'] = df['Mean Coverage Depth'].fillna(0)
df['Mean Coverage Depth'] = df['Mean Coverage Depth'].round(2)
df['Reference Length Coverage After Trimming'] = df['Reference Length Coverage After Trimming'].fillna(0)
df['Reference Length Coverage After Trimming'] = df['Reference Length Coverage After Trimming'].round(2)
df['Average Q Score After Trimming'] = df['Average Q Score After Trimming'].fillna(0)
df['Average Q Score After Trimming'] = df['Average Q Score After Trimming'].round(2)

# Conditions for 'Pass' column
df['Pass'] = 'TBD'
df['GC After Trimming'] = df['GC After Trimming'].str.rstrip('%')
df['GC After Trimming'] = df['GC After Trimming'].astype(float)
df['GC After Trimming'] = df['GC After Trimming'].fillna(0)
cond_gc = (df['GC After Trimming'] > 42) & (df['GC After Trimming'] < 47.5)
cond_depth = df['Mean Coverage Depth'] >= 20
cond_ref_length = df['Reference Length Coverage After Trimming'] >= 20
cond_qscore = df['Average Q Score After Trimming'] >= 28

# Set 'Y' for 'Pass' column where all conditions are met
df.loc[cond_gc & cond_depth & cond_ref_length & cond_qscore, 'Pass'] = 'Y'

# Set 'X' for 'Pass' column where conditions are not met
df.loc[~(cond_gc & cond_depth & cond_ref_length & cond_qscore), 'Pass'] = 'X'

df = df.sort_values('wgs_id')
df['organism'] = df['organism'].str.replace('_',' ',regex=False)

# Output C_auris tsv and txt files
if not args.list:
    print('Writing file for C. auris tab')
    # Filter out rows with missing 'wgs_id' and 'Sample_ID'
    df_filtered = df.dropna(subset=['wgs_id', 'Sample_ID'], how='any')
    df_filtered.to_csv('C_auris_tab.tsv', columns=C_auris_cols, index=False, sep='\t')
    df_filtered.to_csv('C_auris_tab.txt', columns=C_auris_cols, index=False, sep=';')
    print('Created C_auris_tab.{txt,tsv}')

print('Getting additional information for ARLN tab')

# Output arln tsv and txt files
if not args.list:
    print('Writing file for ARLN tab')
    df.to_csv('arln_tab.tsv', columns = arln_cols, index=False, sep = '\t' )
    df.to_csv('arln_tab.txt', columns = arln_cols, index=False, sep = ';' )
    print('Created arln_tab.{txt,tsv}')

# arln and altNGS Labware 8 columns

# LIMS_TEST_ID, Passed QC, ARLN WGS ID, WGS Organism, WGS MLST, Run Name, Genomic Coverage, AMR Gene symbol, AMR Name of closest sequence,AMR % Coverage of reference sequence,AMR % Identity to reference sequence,Virulence Gene symbol,Virulence Name of closest sequence,Virulence % Coverage of reference sequence, Virulence % Identity to reference sequence, SRA Accession, BioSample Accession, Genbank Accession, GC WGS ID, GC Percent, Avg PHRED, Clade
arln_labware_cols  = ['LIMS_TEST_ID', 'Passed QC', 'ARLN WGS ID', 'GC WGS ID', 'WGS Organism', 'WGS MLST', 'Run Name', 'Genomic Coverage', 'AMR Gene symbol', 'AMR Name of closest sequence', 'AMR % Coverage of reference sequence', 'AMR % Identity to reference sequence', 'Virulence Gene symbol', 'Virulence Name of closest sequence', 'Virulence % Coverage of reference sequence', 'Virulence % Identity to reference sequence', 'SRA Accession', 'BioSample Accession', 'Genbank Accession', 'GC Percent', 'Avg PHRED', 'Clade']

# creating columns for unused values 'SRA Accession', 'BioSample Accession', 'Genbank Accession', 'GC WGS ID', 'Clade'
optional_columns = [
    'ARLN WGS ID', 
    'SRA Accession', 
    'BioSample Accession', 
    'Genbank Accession', 
    'GC WGS ID',  
    'Clade',
    'WGS MLST', 
    'AMR Gene symbol', 
    'AMR Name of closest sequence', 
    'AMR % Coverage of reference sequence', 
    'AMR % Identity to reference sequence', 
    'Virulence Gene symbol',
    'Virulence Name of closest sequence',
    'Virulence % Coverage of reference sequence', 
    'Virulence % Identity to reference sequence',
    'Subtype', 
    'Date Uploaded to CDC', 
    'Date Uploaded to NCBI/SRA' ]

for unused in optional_columns:
    if unused not in df.columns:
        df[unused] = ''

# Get final columns 'LIMS_TEST_ID', 'Passed QC', 'WGS Organism', 'Run Name', 'Genomic Coverage', 'GC Percent', 'Avg PHRED'
df['LIMS_TEST_ID']                  = df['lims_id']
df['Passed QC']                     = df['Pass']
df['WGS Organism']                  = df['organism']
df['Run Name']                      = df['Sample_Project']
df['Genomic Coverage']              = df['Reference Length Coverage After Trimming']
df['GC Percent']                    = df['GC After Trimming']
df['Avg PHRED']                     = df['Average Q Score After Trimming']

# Create subset of samples for Labware 8 import files
sample_list = []

if args.list and os.path.exists(args.list) :
    print("Creating files for subset of samples")
    with open(args.list) as f:
        sample_list = f.read().splitlines()
else:
    print("Creating Labware 8 files for each sample")
    sample_list = df[df['Pass'] == 'Y']['LIMS_TEST_ID'].to_list()

if not os.path.exists("labware8"):
    os.mkdir("labware8")

for sample in sample_list:
    sample_df       = df[df['LIMS_TEST_ID'] == sample ].copy()
    sample_name     = str(sample_df['Sample_ID'].values[0])
    sample_organism = str(sample_df['WGS Organism'].values[0])

    # Writing the files for each sample separately
    arln_filename = 'labware8/arln_' + sample + '_results.csv'  # .csv file extension for labware8
    sample_df.to_csv(arln_filename, columns=arln_labware_cols, index=False, sep=',') 


