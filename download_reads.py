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


# Make dir that reads and anaylsis files will be saved to

if run_type == "granduer":
    path = "/Volumes/IDGenomics_NAS/WGS_Serotyping/%s/Sequencing_reads"% run_name
if run_type == "mycosnp":
    path = "/Volumes/IDGenomics_NAS/fungal/%s/Sequencing_reads"% run_name

try:
    os.makedirs(path)
except:
    print("Directory Already Exits, Make sure Reads are not already downloaded and delete Directory" % datetime.now())
    sys.exit()


# Once the run is completed it will be downloaded
bashCommand='bs list --config=%s runs' % i
tmp=bs_out(bashCommand)
tmp=pd.DataFrame(index=[row.split()[2] for row in tmp[1:]], columns=tmp[0].split()[1:], data=[row.split()[1:4] for row in tmp[1:]])
idd=tmp.at[arun_name,'Id']


# First the samplesheet must be downloaded
bashCommand = """bs run download --config=bioinfo
          --output= "%s"
          --id=%s
          --extension=csv
""" % (path,run_name,idd)

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
            --config=bioinfo \
            --id=%s \
            --output="%s/" \
            --retry
    """ % (i,path)
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
print("Reads %s at %s" % (path,datetime.now()))
slack_message("Reads downloaded into: /Volumes/IDGenomics_NAS/WGS_Serotyping/%s/Sequencing_reads/Raw" % path)
