#!/usr/bin/env python3

import os
import sys
import argparse
import subprocess
import re
import time
import pandas as pd
import numpy as np
from datetime import date, datetime
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from importlib.machinery import SourceFileLoader

run_name = str(sys.argv[1])
try:
    run_type = str(sys.argv[2])
except:
    run_type = None

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

        try:
            if tmp.at[args.run_name,'Status']=='Failed' or tmp.at[args.run_name,'Status']=='Stopped' or tmp.at[run_name,'Status']=='Needs Attention' or tmp.at[run_name,'Status']=='Timed Out':
                user=i
                idd=tmp.at[args.run_name,'Id']
                slack_message('%s has "Failed" or was unable to complete on BSSH; Script is aborting, check BSSH for more information' % run_name)
                print('%s has "Failed" or was unable to complete on BSSH; Script is aborting, check BSSH for more information %s' % (run_name,datetime.now()))
                sys.exit()
        except:
            continue
    if t==0:
        time.sleep(1200)

if run_type:
    print("Running download_reads.py")
    subprocess.run(['python3','download_reads.py %s %s' % (run_name, run_type)])
    print("Running auto_%s_ICA.py" % run_type)
    subprocess.run(['python3','auto_%s_ICA.py' % run_type ,run_name])
    if run_type == 'granduer':
        project = 'Produciton'
    if run_type == 'mycosnp':
        project = 'Testing'
    print("Running moniter_ica.py")
    subprocess.run(['python3','moniter_ica.py', run_name, project, run_type])

subprocess.run(["screen", "-S", "my_screen", "-X", "quit"])
