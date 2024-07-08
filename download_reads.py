#!/usr/bin/env python3

import os
import sys
import subprocess
import re
import time
import pandas as pd
import numpy as np
from datetime import date,datetime
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from importlib.machinery import SourceFileLoader
from typing import Union
import functools
import logging

# local functions
from aws_samplesheet_grandeur_create import grandeur_sample_sheet

logging.basicConfig(filename='/Volumes/IDGenomics_NAS/Bioinformatics/jarnn/analysis_for_run.log', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# create logger
logger = logging.getLogger('download_reads.py')
logger.setLevel(logging.DEBUG)

def log(_func=None, *, my_logger):
    def decorator_log(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = my_logger
            args_repr = [repr(a) for a in args]
            kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
            signature = ", ".join(args_repr + kwargs_repr)
            logger.debug(f"function {func.__name__} called with args {signature}")
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                logger.exception(f"Exception raised in {func.__name__}. exception: {str(e)}")
                raise e
        return wrapper

    if _func is None:
        return decorator_log
    else:
        return decorator_log(_func)

@log(my_logger=logger)
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
    logging.info("tmp value %s" % (tmp))
    return tmp

# download the sample sheet used to generate reads from basespace
def download_sample_sheet(path, idd):
    bashCommand = "bs run download --config=bioinfo --output=%s --id=%s --extension=csv" % (path,idd)
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    logging.info("Sample sheet downloaded to %s" % (path))

def download_fastq_files(path, idd):
    idds = get_sample_ids(idd)

    # Download Reads from Run
    for i in idds:
        bashCommand ="bs download dataset --config=bioinfo --id=%s --output=%s/ --retry" % (i,path)
        process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
        output, error = process.communicate()
    
    logging.info("Reads downloaded to %s" % (path))

def get_sample_ids(idd):
    # Now the BSSH ids must be collected into a list
    bashCommand = "bs list dataset --config=bioinfo --input-run=%s " % (idd)
    tmp=bs_out(bashCommand)
    for i in range(len(tmp)):
        if tmp[i].split()[0]== 'Undetermined':
            del tmp[i]
            del tmp[i]
            break
    tmp=pd.DataFrame(columns=tmp[0].split()[1:], data=[row.split()[1:4] for row in tmp[1:]])
    idds=list(tmp['Id'])
    logging.info("Reads ids are %s" % (idds))
    return idds

# Get the basespace run id from run name
def get_run_id(run_name):
    # Once the run is completed it will be downloaded
    bashCommand='bs list --config=bioinfo runs'
    tmp=bs_out(bashCommand)
    tmp=pd.DataFrame(index=[row.split()[2] for row in tmp[1:]], columns=tmp[0].split()[1:], data=[row.split()[1:4] for row in tmp[1:]])
    idd=tmp.at[run_name,'Id']
    logging.info("Run id is %s" % (idd))
    return idd

# Slack_sdk values needed for sending messages to Slack. Uses an API already set up on the Slack website for the UPHL Workspace to post messages on the notifications channel.
# Function makes sending Slack messages as easy as using the print funcition.
@log(my_logger=logger)
def slack_message(string):
    config = SourceFileLoader("config","/Volumes/IDGenomics_NAS/Bioinformatics/jarnn/config.py").load_module()

    client = WebClient(token=config.token)
    channel_id = config.channel_id

    try:
        result = client.chat_postMessage(
            channel=channel_id,
            text=string
        )
    except:
        logger.fatal("Slack Error")

def main():
    if len(sys.argv) != 3:
        logging.fatal("Required positional args not found:")
        logging.info("Usage: %s run_name run_type" % sys.argv[0])
        sys.exit(0)

    run_name = str(sys.argv[1])
    run_type = str(sys.argv[2])

    # Make dir that reads and anaylsis files will be saved to
    if run_type == "grandeur":
        path = "/Volumes/IDGenomics_NAS/pulsenet_and_arln/%s/reads"% run_name
    elif run_type == "mycosnp":
        path = "/Volumes/IDGenomics_NAS/fungal/%s/Sequencing_reads/Raw"% run_name

    try:
        os.makedirs(path)
    except:
        logger.fatal("Directory Already Exits, Make sure Reads are not already downloaded and delete Directory %s" % datetime.now())
        sys.exit()

    idd = get_run_id(run_name)

    download_sample_sheet(path, idd)

    download_fastq_files(path, idd)

    grandeur_sample_sheet(run_name, path + "/SampleSheet.csv", path)

    logger.info("Reads and sample sheet downloaded to %s at %s" % (path,datetime.now()))
    slack_message("Reads downloaded to %s" % path)

if __name__ == "__main__":
    main()