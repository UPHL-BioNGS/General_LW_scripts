'''
Author: Robby Sainsbury

Description:

This script will collect needed files to get results from Cecret updating the Measles clinical tab on the WGS Tracking Google Sheet.

Outputs a file called "wgs_tracking_formatted_data.csv" whose contents can be copied into the first column of the Measles clinical tab.

Then the user will have to use the "Split text to columns" functionality under "Data" in Google Sheets to split the data into the proper columns.

EXAMPLE:
python3 /General_LW_scripts/mev_cecret_to_sheets.py <run name>
'''

import pandas as pd
import numpy as np
import sys


#getting command line input for run name
if len(sys.argv) == 2:
    run_name = sys.argv[1]
else:
    print("Enter run name")

run_folder=f"/home/rsainsbury/measles/{run_name}-mev"

## Reading in data
#cecret results
cecretResults = pd.read_csv(f"{run_folder}/cecret/cecret_results.csv")
#opening the SampleSheet.csv file to find the line where the data starts (the header line starts with "Sample_ID,ProjectName,"), then reading in the sample sheet data
with open(f"{run_folder}/SampleSheet.csv") as fh:
    for i, line in enumerate(fh):
        if line.startswith("Sample_ID,ProjectName,"):
            foundHeader=True
            sampleSheet = pd.read_csv(f"{run_folder}/SampleSheet.csv",header=i,skip_blank_lines=False)
if not foundHeader:
    print("SampleSheet.csv did not include the correct format for finding the metadata, did the format change?")

## Processing and formatting data
#joining the data from cecrete results and the sample sheet
cecretResults["sample"] = cecretResults["sample"].astype(str)
wgs_tracking_format = cecretResults.merge(sampleSheet, left_on = "sample", right_on="Sample_ID")

#adding other columns, some will need to be filled in by hand currently
wgs_tracking_format = wgs_tracking_format.assign(isolate_name="", source="",state="",collection_date="",successful_sequencing_run=run_name)

#selecting columns we want in the order we want
wgs_tracking_format = wgs_tracking_format[["sample","LibraryName","isolate_name","source","state","collection_date","successful_sequencing_run","top_organism","percent_reads_top_organism","num_N","nextclade_clade"]]

#adding note if the measles virus isn't the top organism, then removing the data in percent reads column for those rows
wgs_tracking_format["Notes"] = np.where(
    wgs_tracking_format["top_organism"] != "Morbillivirus hominis", "top_organism: "+wgs_tracking_format["top_organism"]+" at "+wgs_tracking_format["percent_reads_top_organism"].astype(str)+"%","")
wgs_tracking_format["percent_reads_top_organism"] = np.where(
    wgs_tracking_format["top_organism"] != "Morbillivirus hominis", np.nan,wgs_tracking_format["percent_reads_top_organism"])
#dropping the top organism column because we no longer need it
wgs_tracking_format.drop("top_organism",axis=1,inplace=True)

wgs_tracking_format.to_csv(f"{run_folder}/wgs_tracking_formatted_data.csv",index=False,header=False)