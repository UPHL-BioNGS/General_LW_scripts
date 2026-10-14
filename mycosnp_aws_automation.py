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
output_path = "/Volumes/NGS_2/fungal/%s" % run_name


# Find fastq files in run output foler
find_run_folder = os.listdir("/Volumes/NGS/Output/%s" % run_name.split('-')[1])
for i in find_run_folder:
    if run_name.split('-')[2] in i:
        path_to_fastqs = "/Volumes/NGS/Output/%s/%s/Analysis/1/Data/fastq" % (run_name.split('-')[1],i)
        path_to_samplesheet =  "/Volumes/NGS/Output/%s/%s/" % (run_name.split('-')[1],i)
fastqs =[ i for i in os.listdir(path_to_fastqs) if '.fastq.gz' in i and not i.startswith("Undetermined") and os.path.getsize(os.path.join(path_to_fastqs,i)) > 23]

# Move fastq files to output folder
os.makedirs(output_path+"/Sequencing_reads", exist_ok=True)
for i in fastqs:
    shutil.copy(path_to_fastqs+"/"+i,output_path+"/Sequencing_reads")
shutil.copy(path_to_samplesheet +"SampleSheet.csv",output_path+"/Sequencing_reads")

#Create Mycosnp Samplesheet
list_3=[]
fastqs.sort()

#Remove samples whose FASTQ files are smaller than 23 bytes
fastqs[:] =  [x for x in fastqs if os.path.getsize(path_to_fastqs+"/"+x) > 23]

s3="s3://dhhs-uphl-biongs-mycosnp-nf-1-6-2-input-prod/%s" % run_name
for i in fastqs[::2]:
    list_1=[]
    list_1.append(i.split('_')[0])
    list_1.append(s3+"/Sequencing_reads/"+i)
    list_1.append(s3+"/Sequencing_reads/"+i.replace("R1","R2"))
    list_3.append(list_1)

df_graduer_samplesheet = pd.DataFrame(list_3, columns = ['sample', 'fastq_1','fastq_2']) 
df_graduer_samplesheet.to_csv("%s/Sequencing_reads/%s_mycosnp_samplesheet.csv" % (output_path,run_name),index=False)

#Upload to AWS using AWS CLI
process = subprocess.Popen(["aws", "s3", "cp", output_path, s3, "--profile", "aws_prod", "--recursive" ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

stdout, stderr = process.communicate()
print("Output:", stdout, stderr)

#Create AWS JSON file for Pre-Mycosnp
aws_json_pre="""
{
  "workflowId": "4460798",
  "runName": "Automated_Run_Pre_%s",
  "roleArn": "arn:aws:iam::226424408322:role/omics-base-OmicsResources-OmicsWorkflowStartRunJobR-2om9MkMWNQbm",
  "outputUri": "s3://dhhs-uphl-biongs-mycosnp-nf-1-6-2-output-prod/",
  "runGroupId": "4657844",
  "networkingMode":"VPC",
  "configurationName": "dhhs-uphl-biongs-omics-vpc",
  "engineSettings": {"profile": "aws"},
  "scratchStorageMode": "LOCAL",
  "parameters": {
    "input": "s3://dhhs-uphl-biongs-mycosnp-nf-1-6-2-input-prod/%s/Sequencing_reads/%s_mycosnp_samplesheet.csv",
    "workflow": "PRE_MYCOSNP",
    "skip_combined_analysis": false,
    "coverage": 70,
    "add_vcf_file": "s3://dhhs-uphl-biongs-mycosnp-nf-1-6-2-input-prod/reference_files/add_clades_vcf.csv",
    "skip_phylogeny": false,
    "fasta": "s3://dhhs-uphl-biongs-mycosnp-nf-1-6-2-input-prod/reference_files/B11205_reference.fasta",
    "snpeff": true
  }
}
""" % (run_name,run_name,run_name)

with open("%s/%s_pre_awsparameters.json" % (output_path,run_name) , 'w') as f:
    f.write(aws_json_pre)
#Create AWS JSON file for Pre-Mycosnp
aws_json_nfcore="""
{
  "workflowId": "4460798",
  "runName": "Automated_Run_NFCore_%s",
  "roleArn": "arn:aws:iam::226424408322:role/omics-base-OmicsResources-OmicsWorkflowStartRunJobR-2om9MkMWNQbm",
  "outputUri": "s3://dhhs-uphl-biongs-mycosnp-nf-1-6-2-output-prod/",
  "runGroupId": "4657844",
  "networkingMode":"VPC",
  "configurationName": "dhhs-uphl-biongs-omics-vpc",
  "engineSettings": {"profile": "aws"},
  "scratchStorageMode": "LOCAL",
  "parameters": {
    "input": "s3://dhhs-uphl-biongs-mycosnp-nf-1-6-2-input-prod/%s/Sequencing_reads/%s_mycosnp_samplesheet.csv",
    "workflow": "NFCORE_MYCOSNP",
    "skip_combined_analysis": false,
    "coverage": 70,
    "add_vcf_file": "s3://dhhs-uphl-biongs-mycosnp-nf-1-6-2-input-prod/reference_files/add_clades_vcf.csv",
    "skip_phylogeny": false,
    "fasta": "s3://dhhs-uphl-biongs-mycosnp-nf-1-6-2-input-prod/reference_files/B11205_reference.fasta",
    "snpeff": true
  }
}
""" % (run_name,run_name,run_name)

with open("%s/%s_nfcore_awsparameters.json" % (output_path,run_name) , 'w') as f:
    f.write(aws_json_nfcore)

# Upload json file to start run
process = subprocess.Popen(["aws", "s3", "cp", "%s/%s_pre_awsparameters.json" % (output_path,run_name),
                            "s3://dhhs-uphl-biongs-mycosnp-nf-1-6-2-input-prod/",
                            "--profile", "aws_prod" ], stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, text=True)

stdout, stderr = process.communicate()
print("Output:", stdout, stderr)


process = subprocess.Popen(["aws", "s3", "cp", "%s/%s_nfcore_awsparameters.json" % (output_path,run_name),
                            "s3://dhhs-uphl-biongs-mycosnp-nf-1-6-2-input-prod/",
                            "--profile", "aws_prod" ], stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, text=True)

stdout, stderr = process.communicate()
print("Output:", stdout, stderr)

slack_message("%s has started Mycosnp Analysis on AWS" % run_name)
# Moniter AWS Run
loop = True
pre = False
nfcore = False
while loop:
    process = subprocess.Popen(["aws", "omics", "list-runs","--profile", "aws_prod", "--region", "us-west-2"  ], stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, text=True)
    data, stderr = process.communicate()
    data = json.loads(data)
    for i in data['items']:
        if "Automated_Run_Pre_"+run_name in i.values():
            if i['status'] == 'COMPLETED':
                pre = True
    for i in data['items']:
        if "Automated_Run_NFCore_"+run_name in i.values():
            if i['status'] == 'COMPLETED':
                nfcore = True
    if pre and nfcore:
        loop = False
    else:
        time.sleep(1200)

slack_message("%s has COMPLETED Mycosnp Analysis on AWS; Results downloading to %s" % (run_name, output_path))

for i in data['items']:
        if "Automated_Run_Pre_"+run_name in i.values():
            if i['status'] == 'COMPLETED':
                run_id_pre=i['id']

for i in data['items']:
        if "Automated_Run_NFCore_"+run_name in i.values():
            if i['status'] == 'COMPLETED':
                run_id_nfcore=i['id']

# Download Results
os.makedirs(output_path+"/Pre-Mycosnp_results", exist_ok=True)
process = subprocess.Popen(["aws", "s3", "cp",
                            "s3://dhhs-uphl-biongs-mycosnp-nf-1-6-2-output-prod/%s/" % run_id_pre,
                            "%s/Pre-Mycosnp_results/" % output_path,
                            "--profile", "aws_prod", "--recursive" ], stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, text=True)

stdout, stderr = process.communicate()

os.makedirs(output_path+"/NFCore-Mycosnp_results", exist_ok=True)
process = subprocess.Popen(["aws", "s3", "cp",
                            "s3://dhhs-uphl-biongs-mycosnp-nf-1-6-2-output-prod/%s/" % run_id_nfcore,
                            "%s/NFCore-Mycosnp_results/" % output_path,
                            "--profile", "aws_prod", "--recursive" ], stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, text=True)

stdout, stderr = process.communicate()
print("Output:", stdout, stderr)