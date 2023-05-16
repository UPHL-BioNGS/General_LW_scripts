#!/usr/bin/env python3

"""
Author: John Arnn
Released: 2023-03-20
Version: 1.0.0
Description:
This script automates messaging to the UPHL slack channel to help monitor runs that are on BSSH. 
You provide the script with the name of the run and when it completes a message will be sent to slack. 
EXAMPLE:
python3 monitor_bssh.py UT-VH0770-220915 
"""

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

config = SourceFileLoader("config","/Volumes/IDGenomics_NAS/Bioinformatics/jarnn/config.py").load_module()

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

# These are the config files that are on the production account
configurations=["bioinfo"]

slack_message('Monitoring %s on BSSH' % run_name)
print('Monitoring %s on BSSH' % run_name)
# This While loops Uses the BaseSpace CLI tool to monitor the progress of the run
t=0
while t==0:
    for i in configurations:
        bashCommand='bs list --config=%s runs' % i
        tmp=bs_out(bashCommand)
        tmp=pd.DataFrame(index=[row.split()[2] for row in tmp[1:]], columns=tmp[0].split()[1:], data=[row.split()[1:4] for row in tmp[1:]])
        try:
            if tmp.at[run_name,'Status']=='Complete':
                user=i
                idd=tmp.at[run_name,'Id']
                slack_message('%s is "Complete" on BSSH' % run_name)
                print('%s is "Complete" on BSSH' % run_name)
                t=1
                break
        except:
            continue
    # Wait 20 min then look again.
    if t==1:
        break
    time.sleep(1200)
