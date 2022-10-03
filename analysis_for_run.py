#!/usr/bin/env python3

"""
Author: John Arnn
Released: 2022-09-20
Description:
This script will download the reads from BSSH once run completes on sequencer, start analysis on ICA,
and download results from ICA while sending updates to Slack at UPHL Workspace notifications channel.
EXAMPLE:
python analysis_for_run.py UT-VH0770-220915 -a mycosnp
"""

import os
import sys
import argparse
import subprocess
import re
import time
import pandas as pd
import numpy as np
from datetime import date
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from importlib.machinery import SourceFileLoader

config = SourceFileLoader("config","/Volumes/IDGenomics_NAS/config.py").load_module()

#Create Arguments useing argparse
parser = argparse.ArgumentParser(description= "This script will downloads fastq files from sequencer runs; start ICA analysis using additional scripts, download ICA analysis results using additional scripts, and send Slack messages to update progress")

parser.add_argument('run_name', help='This is an required argument of the Run Name or Experiment name that can be found on BSSH; generated when sequecning run is started')

parser.add_argument('--analysis','-a', choices=['mycosnp','Grandeur'], required=True, help='This tells the script what pipeline needs to run on ICA, which uses the specialized script to start the run; also which files to download once the analsis completes')
parser.add_argument('--download_reads','-d', action='store_true', help='This is an optional argument that makes the script only monitor the run on BSSH, then download when it is completed')
parser.add_argument('--ica_download','-i', action='store_true', help='This is an opitonal flag but analysis results will not be downloaded without this flag')
parser.add_argument('--ica_reference', help='This is an opitonal flag to modify the ICA User Reference, it is recommended to provide this flag if an ICA analysis has already been tried. Having the same User Reference can give ICA problems.')

args = parser.parse_args()

# These are the config files that are on the production account
configurations=["kelly","uphl_ngs","ica","bioinfo"]

# Function to handle the stdout of the bs CLI tool. Returns a list of list of strings.
def bs_out(bashCommand):
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    tmp=output.decode("utf-8")
    tmp=tmp.split('\n')
    tmp.pop(0)
    tmp.pop(1)
    tmp.pop(-1)
    tmp.pop(-1)
    tmp=[x.replace('|', '') for x in tmp]
    tmp=[re.sub(r"\s+", ' ', x) for x in tmp]
    return tmp

# Function to handle the stdout of the ICA CLI tool. Returns a list of list of strings.
def icav_out(bashCommand):
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    tmp=output.decode("utf-8")
    tmp=tmp.split('\n')
    tmp.pop(0)
    tmp.pop(-1)
    tmp.pop(-1)
    tmp=[x.replace('\t', ' ') for x in tmp]
    return tmp

# Function to loop through files needed to be downloaded for each analysis.
def ica_download(target_dir,files_list):
    for i in files_list:
        bashCommand = "icav2 projectdata download %s%s /Volumes/IDGenomics_NAS/WGS_Serotyping/%s/Sequencing_reads" % (target_dir,i,args.run_name)
        process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
        process.communicate()

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

slack_message('Monitoring %s on BSSH' % args.run_name)
print('Monitoring %s on BSSH' % args.run_name)
# This While loops Uses the BaseSpace CLI tool to monitor the progress of the run
t=0
while t==0:
    for i in configurations:
        bashCommand='bs list --config=%s runs' % i
        tmp=bs_out(bashCommand)
        tmp=pd.DataFrame(index=[row.split()[2] for row in tmp[1:]], columns=tmp[0].split()[1:], data=[row.split()[1:4] for row in tmp[1:]])
        try:
            if tmp.at[args.run_name,'Status']=='Complete':
                user=i
                idd=tmp.at[args.run_name,'Id']
                slack_message('%s is "Complete" on BSSH' % args.run_name)
                print('%s is "Complete" on BSSH' % args.run_name)
                t=1
                break
        except:
            continue
        try:
            if tmp.at[args.run_name,'Status']=='Failed':
                user=i
                idd=tmp.at[args.run_name,'Id']
                slack_message('%s is "Failed"; Script is aborting, check BSSH for more information' % args.run_name)
                print('%s is "Failed"; Script is aborting, check BSSH for more information' % args.run_name)
                sys.exit()
        except:
            continue
    # Wait 20 min then look again.
    if t==1:
        break
    time.sleep(1200)

# Make dir that reads and anaylsis files will be saved to
try:
    os.makedirs("/Volumes/IDGenomics_NAS/WGS_Serotyping/%s/Sequencing_reads"% args.run_name)
except:
    print("Directory Already Exits, Make sure Reads are not already downloaded and delete Directory")
    sys.exit()

#If samples are directly avaiable in ICA there is no need to wait for download to start anaylsis by calling another python script
if args.analysis == 'mycosnp':
    subprocess.call("python auto_%s_ICA.py %s %s" % (args.analysis,args.run_name,args.ica_reference), shell=True)

# Once the run is completed it will be downloaded
# First the samplesheet must be downloaded
bashCommand = """bs run download --config=%s
          --output= "/Volumes/IDGenomics_NAS/WGS_Serotyping/%s/Sequencing_reads"
          --id=%s
          --extension=csv
""" % (user,args.run_name,idd)

process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
output, error = process.communicate()

# Now the BSSH ids must be collected into a list
bashCommand = "bs list dataset --config=%s --input-run=%s " % (user,idd)
tmp=bs_out(bashCommand)
for i in range(len(tmp)):
    if tmp[i].split()[0]== 'Undetermined':
        del tmp[i]
        del tmp[i]
        break
tmp=pd.DataFrame(columns=tmp[0].split()[1:], data=[row.split()[1:4] for row in tmp[1:]])
idds=list(tmp['Id'])

# Download Reads from Run
for i in idds:
    bashCommand ="""
    bs download dataset \
            --config=%s \
            --id=%s \
            --output="/Volumes/IDGenomics_NAS/WGS_Serotyping/%s/Sequencing_reads/Raw" \
            --retry
    """ % (user,i,args.run_name)
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
print("Reads downloaded into: /Volumes/IDGenomics_NAS/WGS_Serotyping/%s/Sequencing_reads/Raw" % args.run_name)
slack_message("Reads downloaded into: /Volumes/IDGenomics_NAS/WGS_Serotyping/%s/Sequencing_reads/Raw" % args.run_name)

if args.download_reads:
    sys.exit()

# Start ICA Anaylsis if not mycosnp; Call other python script
if args.analysis == 'Grandeur':
    subprocess.call("python auto_%s_ICA.py %s %s" % (args.analysis,args.run_name,args.ica_reference), shell=True)

# While loop to look in ICA to See if run is finished
slack_message('Started %s Anaylysis on ICA and Monitoring' % args.run_name)
print('Started %s Anaylysis on ICA and Monitoring' % args.run_name)
bashCommand = "icav2 projects enter Testing"
process = subprocess.Popen(bashCommand.split(" ",3), stdout=subprocess.PIPE)
process.communicate()
t=0
while t == 0:
    bashCommand = "icav2 projectanalyses list --max-items 0"
    tmp=icav_out(bashCommand)
    tmp2=[]
    for i in range(len(tmp)):
        if args.run_name in tmp[i]:
            tmp2.append(tmp[i])
    try:
        if tmp2[-1].split()[-1] == 'SUCCEEDED':
            slack_message('%s is "SUCCEEDED" on ICA' % args.run_name)
            print('%s is "SUCCEEDED" on ICA' % args.run_name)
            t=1
        if tmp2[-1].split()[-1] == 'FAILED':
            slack_message('%s is "FAILED" on ICA' % args.run_name)
            print('%s is "FAILED" on ICA' % args.run_name)
            t=1
            break
    except:
        continue
    time.sleep(1200)

slack_message("%s has comleted analysis on ICA" % args.run_name)
print("%s has comleted analysis on ICA" % args.run_name)

# Now that the analysis has 'SUCCEEDED', the most important files needed for analysis are downloaded
if args.ica_download:
    bashCommand = "icav2 projectdata list --file-name %s --match-mode FUZZY" % run_name
    tmp= icav_out(bashCommand)
    for i in tmp:
        try:
            bashCommand = "icav2 projectdata list --parent-folder %sResults/" % i.split()[0]
            tmp= icav_out(bashCommand)
            target_dir= i.split()[0]
        except:
            continue
    mycosnp_files=['Results/stats/*','Results/multiqc_report.html','Results/combined/*']
    Grandeur_files=['grandeur/summary/grandeur_summary.txt','grandeur/grandeur_results.tsv','grandeur/ncbi-AMRFinderplus/*','grandeur/kraken2/*','grandeur/blobtools/*','grandeur/contigs/*','grandeur/multiqc/multiqc_report.html']
    if args.Grandeur:
        ica_download(target_dir,Grandeur_files)
    if args.mycosnp:
        ica_download(target_dir,mycosnp_files)

print("analysis_for_run.py completed Successfully")
slack_message("analysis_for_run.py completed Successfully")
