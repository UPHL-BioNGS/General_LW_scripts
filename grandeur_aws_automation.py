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

# Script Inputs
run_name = str(sys.argv[1])
output_path = "/Volumes/NGS_2/pulsenet_and_arln/%s" % run_name


# Find fastq files in run output foler
find_run_folder = os.listdir("/Volumes/NGS/Output/%s" % run_name.split('-')[1])
for i in find_run_folder:
    if run_name.split('-')[2] in i:
        path_to_fastqs = "/Volumes/NGS/Output/%s/%s/Analysis/1/Data/BCLConvert/fastq" % (run_name.split('-')[1],i)
        path_to_samplesheet =  "/Volumes/NGS/Output/%s/%s/" % (run_name.split('-')[1],i)
fastqs =[ i for i in os.listdir(path_to_fastqs) if '.fastq.gz' in i and not i.startswith("Undetermined")]

# Move fastq files to output folder
os.makedirs(output_path+"/reads", exist_ok=True)
for i in fastqs:
    shutil.copy(path_to_fastqs+"/"+i,output_path+"/reads")
shutil.copy(path_to_samplesheet +"SampleSheet.csv",output_path+"/reads")

#Create Granduer Samplesheet
list_3=[]
fastqs.sort()
s3="s3://dhhs-uphl-biongs-grandeur-4-2-20240425-22-04-01-input-prod/%s" % run_name
for i in fastqs[::2]:
    list_1=[]
    list_1.append(i.split('_')[0])
    list_1.append(s3+"/reads/"+i)
    list_1.append(s3+"/reads/"+i.replace("R1","R2"))
    list_3.append(list_1)

df_graduer_samplesheet = pd.DataFrame(list_3, columns = ['sample', 'fastq_1','fastq_2']) 
df_graduer_samplesheet.to_csv("%s/reads/%s_graduer_samplesheet.csv" % (output_path,run_name),index=False)

#Upload to AWS using AWS CLI
process = subprocess.Popen(["aws", "s3", "cp", output_path, s3, "--profile", "aws_prod", "--recursive" ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

stdout, stderr = process.communicate()
print("Output:", stdout, stderr)

#Create AWS JSON file
aws_json="""
{
  "workflowId": "9550235",
  "runName": "Automated_Run_%s",
  "roleArn": "arn:aws:iam::226424408322:role/omics-base-OmicsResources-OmicsWorkflowStartRunJobR-2om9MkMWNQbm",
  "outputUri": "s3://dhhs-uphl-biongs-grandeur-4-2-20240425-22-04-01-output-prod/",
  "runGroupId": "4657844",
  "parameters": {
    "sample_sheet": "s3://dhhs-uphl-biongs-grandeur-4-2-20240425-22-04-01-input-prod/%s/reads/%s_graduer_samplesheet.csv"
  }
}
""" % (run_name,run_name,run_name)

with open("%s/%s_awsparameters.json" % (output_path,run_name) , 'w') as f:
    f.write(aws_json)

# Upload json file to start run
process = subprocess.Popen(["aws", "s3", "cp", "%s/%s_awsparameters.json" % (output_path,run_name),
                            "s3://dhhs-uphl-biongs-grandeur-4-2-20240425-22-04-01-input-prod/",
                            "--profile", "aws_prod" ], stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, text=True)

stdout, stderr = process.communicate()
print("Output:", stdout, stderr)

slack_message("%s has started Granduer Analysis on AWS" % run_name)
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

slack_message("%s has COMPLETED Granduer Analysis on AWS; Results downloading to %s" % (run_name, output_path))

for i in data['items']:
        if "Automated_Run_"+run_name in i.values():
            if i['status'] == 'COMPLETED':
                run_id=i['id']

# Download Results
process = subprocess.Popen(["aws", "s3", "cp",
                            "s3://dhhs-uphl-biongs-grandeur-4-2-20240425-22-04-01-output-prod/%s/" % run_id,
                            "%s" % output_path,
                            "--profile", "aws_prod", "--recursive" ], stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, text=True)

stdout, stderr = process.communicate()
print("Output:", stdout, stderr)
