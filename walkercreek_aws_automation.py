#!/usr/bin/env python3

import os
import re
import shutil
import pandas as pd
import subprocess
import json
import time
import sys
from importlib.machinery import SourceFileLoader

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

config = SourceFileLoader("config","/Volumes/NGS_2/Bioinformatics/jarnn/config.py").load_module()

# Slack_sdk values needed for sending messages to Slack. Uses an API already set up on the Slack website for the UPHL Workspace to post messages on the notifications channel.
# Function makes sending Slack messages as easy as using the print funcition.
client = WebClient(token=config.token)
channel_id = config.channel_id
def slack_message(string):
    try:

        result = client.chat_postMessage(
            channel=channel_id,
            text=string
        )

    except:
        print("Slack Error")

#Function to read Illumina Samplesheet
def parse_samplesheet_section(file_path, section_name="[Cloud_Data]"):
    start_line = None
    
    # Step 1: Find the line where the section starts
    with open(file_path, 'r') as f:
        for i, line in enumerate(f):
            if line.strip() == section_name:
                start_line = i + 1  # Data starts on the next line
                break
                
    if start_line is None:
        raise ValueError(f"Section {section_name} not found in the sample sheet.")
        
    # Step 2: Read from that line until the next section (marked by '[') or end of file
    lines_to_read = []
    with open(file_path, 'r') as f:
        # Skip to the start of the section
        for _ in range(start_line):
            next(f)
            
        # Read lines until another section starts or file ends
        for line in f:
            if line.startswith('['):
                break
            lines_to_read.append(line)
            
    # Step 3: Convert the extracted lines into a pandas DataFrame
    from io import StringIO
    section_data = "".join(lines_to_read)
    df = pd.read_csv(StringIO(section_data))
    
    # Optional: Drop completely empty rows or columns if they exist
    df = df.dropna(how='all')
    
    return df

# Script Inputs
run_name = str(sys.argv[1])
output_path = "/Volumes/NGS_2/flu/flu_runs/%s" % run_name


# Find fastq files in run output foler
find_run_folder = os.listdir("/Volumes/NGS/Output/%s" % run_name.split('-')[1])
for i in find_run_folder:
    if run_name.split('-')[2] in i:
        path_to_fastqs = "/Volumes/NGS/Output/%s/%s/Analysis/1/Data/fastq" % (run_name.split('-')[1],i)
        path_to_samplesheet =  "/Volumes/NGS/Output/%s/%s/" % (run_name.split('-')[1],i)
fastqs =[ i for i in os.listdir(path_to_fastqs) if '.fastq.gz' in i and not i.startswith("Undetermined") and os.path.getsize(os.path.join(path_to_fastqs,i)) > 23]

#Filter out Flu samples and controls using samplesheet
data_section = parse_samplesheet_section(path_to_samplesheet+'SampleSheet.csv')
flu_samples = data_section[data_section['ProjectName'].str.contains('Influenza', case=False, na=False)]['Sample_ID'].to_list()

flu_fastqs=[]
for i in flu_samples:
    for k in fastqs:
        if k.startswith(i):
            flu_fastqs.append(k)

for i in fastqs:
    if "NTC" in i or "POS" in i:
        flu_fastqs.append(i)

# Move fastq files to output folder
os.makedirs(output_path+"/Sequencing_reads", exist_ok=True)
for i in flu_fastqs:
    shutil.copy(path_to_fastqs+"/"+i,output_path+"/Sequencing_reads")
shutil.copy(path_to_samplesheet +"SampleSheet.csv",output_path+"/Sequencing_reads")

#Create Walkercreek Samplesheet
list_3=[]
flu_fastqs.sort()

#Remove samples whose FASTQ files are smaller than 23 bytes
flu_fastqs[:] =  [x for x in flu_fastqs if os.path.getsize(path_to_fastqs+"/"+x) > 23]

s3="s3://dhhs-uphl-biongs-walkercreek-3-0-input-prod/%s" % run_name
for i in flu_fastqs[::2]:
    list_1=[]
    list_1.append(i.split('_')[0])
    list_1.append(s3+"/Sequencing_reads/"+i)
    list_1.append(s3+"/Sequencing_reads/"+i.replace("R1","R2"))
    list_3.append(list_1)

df_walkercreek_samplesheet = pd.DataFrame(list_3, columns = ['sample', 'fastq_1','fastq_2']) 
df_walkercreek_samplesheet.to_csv("%s/Sequencing_reads/%s_walkercreek_samplesheet.csv" % (output_path,run_name),index=False)

#Upload to AWS using AWS CLI
process = subprocess.Popen(["aws", "s3", "cp", output_path, s3, "--profile", "aws_prod", "--recursive" ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

stdout, stderr = process.communicate()
print("Output:", stdout, stderr)

#Create AWS JSON file for Walkercreek
aws_json="""
{
  "workflowId": "8041727",
  "runName": "Automated_Run_%s",
  "roleArn": "arn:aws:iam::226424408322:role/omics-base-OmicsResources-OmicsWorkflowStartRunJobR-2om9MkMWNQbm",
  "outputUri": "s3://dhhs-uphl-biongs-walkercreek-3-0-output-prod/",
  "runGroupId": "4657844",
  "networkingMode":"VPC",
  "configurationName": "dhhs-uphl-biongs-omics-vpc",
  "engineSettings": {"profile": "aws"},
  "scratchStorageMode": "LOCAL",
  "parameters": {
    "input": "s3://dhhs-uphl-biongs-walkercreek-3-0-input-prod/%s/Sequencing_reads/%s_walkercreek_samplesheet.csv",
    "skip_ncbi_sra_human_scrubber": false,
    "skip_vadr": false,
    "skip_snpeff": false,
    "skip_nextclade": false,
    "skip_adapter_trimming": false,
    "skip_kraken2": false,
    "irma_module": "FLU",
    "platform": "flu_illumina"
  }
}
""" % (run_name,run_name,run_name)

with open("%s/%s_awsparameters.json" % (output_path,run_name) , 'w') as f:
    f.write(aws_json)


# Upload json file to start run
process = subprocess.Popen(["aws", "s3", "cp", "%s/%s_awsparameters.json" % (output_path,run_name),
                            "s3://dhhs-uphl-biongs-walkercreek-3-0-input-prod/",
                            "--profile", "aws_prod" ], stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, text=True)

stdout, stderr = process.communicate()
print("Output:", stdout, stderr)

slack_message("%s has started Walkercreek Analysis on AWS" % run_name)
# Moniter AWS Run
loop = True
while loop:
    process = subprocess.Popen(["aws", "omics", "list-runs","--profile", "aws_prod", "--region", "us-west-2"  ], stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, text=True)
    data, stderr = process.communicate()
    data = json.loads(data)
    for i in data['items']:
        if "Automated_Run_"+run_name in i.values():
            if i['status'] == 'COMPLETED':
                loop = False
    else:
        time.sleep(1200)

slack_message("%s Flu samples has COMPLETED Walkercreek Analysis on AWS; Results downloading to %s" % (run_name, output_path))

for i in data['items']:
        if "Automated_Run_"+run_name in i.values():
            if i['status'] == 'COMPLETED':
                run_id=i['id']


# Download Results
os.makedirs(output_path+"/Walkercreek_results", exist_ok=True)
process = subprocess.Popen(["aws", "s3", "cp",
                            "s3://dhhs-uphl-biongs-walkercreek-3-0-output-prod/%s/" % run_id,
                            "%s/Walkercreek_results/" % output_path,
                            "--profile", "aws_prod", "--recursive" ], stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, text=True)

stdout, stderr = process.communicate()