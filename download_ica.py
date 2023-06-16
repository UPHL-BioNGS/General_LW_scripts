#!/usr/bin/env python3

import os
import sys
import subprocess
import re
import time
import pandas as pd
import numpy as np
from datetime import date
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from importlib.machinery import SourceFileLoader

run_name = str(sys.argv[1])
run_type = str(sys.argv[2])

# Slack_sdk values needed for sending messages to Slack. Uses an API already set up on the Slack website for the UPHL Workspace to post messages on the notifications channel.
# Function makes sending Slack messages as easy as using the print funcition.
config = SourceFileLoader("config","/Volumes/IDGenomics_NAS/Bioinformatics/jarnn/config.py").load_module()

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
def ica_download(run_type):
    if run_type == 'mycosnp':
        bashCommand = "icav2 projects enter Testing"
        process = subprocess.Popen(bashCommand.split(" ",3), stdout=subprocess.PIPE)
        process.communicate()

        bashCommand = "icav2 projectdata list --file-name %s --match-mode FUZZY" % run_name
        tmp= icav_out(bashCommand)
        for i in tmp:
            try:
                bashCommand = "icav2 projectdata list --parent-folder /%s/Results/" % i.split()[0]
                tmp= icav_out(bashCommand)
                target_dir= i.split()[0]
                print("Works!!!")
                break
            except:
                pass
        for i in ['Results/stats/*','Results/multiqc_report.html','Results/combined/*','Results/snpeff/*', 'Results/samples/*']:
            bashCommand = "icav2 projectdata download /%s/%s /Volumes/IDGenomics_NAS/fungal/%s/" % (target_dir,i, run_name)
            process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
            process.communicate()
    if run_type == 'granduer':
        bashCommand = "icav2 projects enter Produciton"
        process = subprocess.Popen(bashCommand.split(" ",3), stdout=subprocess.PIPE)
        process.communicate()

        bashCommand = "icav2 projectdata list --file-name %s --match-mode FUZZY --parent-folder /" % run_name
        tmp= icav_out(bashCommand)
        for i in tmp:
            try:
                bashCommand =  "icav2 projectdata list --parent-folder /%s/grandeur/" % i.split()[0]
                tmp= icav_out(bashCommand)
                target_dir= i.split()[0]
                break
            except:
                pass
        for i in ['/grandeur/*']:
            bashCommand = "icav2 projectdata download /%s%s /Volumes/IDGenomics_NAS/WGS_Serotyping/%s/" % (target_dir,i, run_name)
            process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
            process.communicate()

ica_download(run_type)
slack_message("Files for Analysis for %s on ICA downloaded to NAS" % (run_name))
