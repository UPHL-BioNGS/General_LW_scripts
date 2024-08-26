#!/usr/bin/env python3

"""
Author: John Arnn
Released: 1997-04-05
Version: 1.2.0
Description:
    This script is for downloading reads from basespace and starting analysis.

EXAMPLE:
    python3 screen_run.py -r UT-M70330-240131 --grandeur
"""

import argparse
import sys
import subprocess
import re
import time
import pandas as pd
import numpy as np
from datetime import date, datetime
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from importlib.machinery import SourceFileLoader
from typing import Union
import functools
import logging

# local functions
from bssh_reads_by_run import bs_out, download_reads
from bssh_sample_sheet import download_sample_sheet
from aws_samplesheet_grandeur_create import grandeur_sample_sheet

# setting up logging
logging.basicConfig(filename=f"/Volumes/IDGenomics_NAS/Bioinformatics/jarnn/analysis_for_run_{datetime.today().strftime('%Y_%m_%d')}.log", format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# create logger
logger = logging.getLogger('screen_run.py')
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
def my_subprocess_run(*args, **kwargs):
    """
    Runs a command in the shell.
    
    Args:
        args/kwargs (argparse.Namespace): Parsed command-line arguments.

    """
    return subprocess.run(*args, **kwargs)


@log(my_logger=logger)
def check_bs(run_name, time_interval = 1200 ):
    """
    Checks bssh for run completeness

    Args:
        run_name (str): run name
        time_interval (int): second to wait before checking again
    
    Returns:
        idd (str): Run id on bssh

    """
    t=0
    while t == 0:
        bash_command='bs list --config=bioinfo runs'
        
        df = bs_out(bash_command)

        if run_name in df['ExperimentName'].values:
            status = df.loc[df['ExperimentName'] == run_name,'Status'].iloc[0]
            idd = df.loc[df['ExperimentName'] == run_name,'Id'].iloc[0]
            if status == 'Complete':
                t = 1
                slack_message(f"{run_name} is \"Complete\" on BSSH")
                logger.info(f"{run_name} is \"Complete\" on BSSH")
                break
            elif status == 'Failed' or status == 'Stopped' or status == 'Needs Attention' or status == 'Timed Out':
                slack_message(f"{run_name} has \"{status}\" status and was unable to complete on BSSH; Script is aborting, check BSSH for more information")
                logger.warning(f"{run_name} has \"{status}\" status and was unable to complete on BSSH; Script is aborting, check BSSH for more information {datetime.now()}")
                sys.exit(0)
            else:
                logging.info(f"{run_name} has a {status} status")    
        else:
            logging.info(f"{run_name} not found in bssh yet!")

        if t == 0:
            logging.info(f"sleeping for {time_interval}")
            time.sleep(time_interval)

    logging.info(f"{run_name} id is {idd}")    
    return idd


# Slack_sdk values needed for sending messages to Slack. Uses an API already set up on the Slack website for the UPHL Workspace to post messages on the notifications channel.
# Function makes sending Slack messages as easy as using the print funcition.
@log(my_logger=logger)
def slack_message(string):
    """
    Sends a message to slack.
    
    Args:
        string (str): Slack message.

    """

    config = SourceFileLoader("config","/Volumes/IDGenomics_NAS/Bioinformatics/jarnn/config.py").load_module()

    client = WebClient(token=config.token)
    channel_id = config.channel_id
    try:

        result = client.chat_postMessage(
            channel=channel_id,
            text=string
        )

    except:
        logger.info("Slack Error")


@log(my_logger=logger)
def main():
    """
    Waits for run to finish in BSSH.

    Once complete, downloads the sample sheet and fastq files into local storage.
    
    Args:
        args (argparse.Namespace): Parsed command-line arguments.

    """

    parser = argparse.ArgumentParser(description="Runs in screen for sequencing run")
    
    # Define your arguments here
    parser.add_argument('-r', '--run', type=str, required=True, help="Run name")
    parser.add_argument('-o', '--out', type=str, required=False, default="reads", help="Directory where sample sheet will be downloaded to")
    parser.add_argument('-g', '--grandeur', action='store_true', default = False, help = 'Flags run for Grandeur')
    parser.add_argument('-m', '--mycosnp', action='store_true', default = False, help = 'Flags run for MycoSnp')
    
    # Parse the arguments
    args = parser.parse_args()

    # wait until run is complete
    idd = check_bs(args.run)

    # set path for downloading reads and sample sheet from basespace
    path = ''
    if args.grandeur:
        path = f"/Volumes/IDGenomics_NAS/pulsenet_and_arln/{args.run}/reads"
    elif args.mycosnp:
        path = f"/Volumes/IDGenomics_NAS/fungal/{args.run}/Sequencing_reads/Raw"

    download_reads(args.run, path)
    download_sample_sheet(args.run, path)

    if args.grandeur:
        grandeur_sample_sheet(args.run, f"{path}/SampleSheet.csv", path)
    
    # close screen when finished
    my_subprocess_run(["screen", "-S", args.run, "-X", "quit"])


if __name__ == "__main__":
    main()