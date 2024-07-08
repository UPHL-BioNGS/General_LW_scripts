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
project=str(sys.argv[2])

try:
    run_type = str(sys.argv[3])
except:
    run_type = None

config = SourceFileLoader("config","/Volumes/IDGenomics_NAS/Bioinformatics/jarnn/config.py").load_module()

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

# While loop to look in ICA to See if run is finished
slack_message('Started %s Anaylysis on ICA and Monitoring' % run_name)
print('Started %s Anaylysis on ICA and Monitoring' % run_name)
bashCommand = "icav2 projects enter Testing"
process = subprocess.Popen(bashCommand.split(" ",3), stdout=subprocess.PIPE)
process.communicate()
t=0
while t == 0:
    bashCommand = "icav2 projects enter %s" % project
    process = subprocess.Popen(bashCommand.split(" ",3), stdout=subprocess.PIPE)
    process.communicate()
    bashCommand = "icav2 projectanalyses list --max-items 0"
    tmp=icav_out(bashCommand)
    tmp2=[]
    for i in range(len(tmp)):
        if run_name in tmp[i]:
            tmp2.append(tmp[i])
    try:
        if tmp2[-1].split()[-1] == 'SUCCEEDED':
            slack_message('%s is "SUCCEEDED" on ICA' % run_name)
            print('%s is "SUCCEEDED" on ICA' % run_name)
            t=1
        if tmp2[-1].split()[-1] == 'FAILED':
            slack_message('%s is "FAILED" on ICA' % run_name)
            print('%s is "FAILED" on ICA' % run_name)
            t=1
            break
    except:
        pass
    if t==0:
        time.sleep(1200)

slack_message("%s has comleted analysis on ICA" % run_name)
print("%s has comleted analysis on ICA" % run_name)

if run_type:
    subprocess.run(['python3','download_ica.py', run_name, run_type])
