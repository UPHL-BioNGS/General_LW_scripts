#!/usr/bin/env python3

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

logging.basicConfig(filename='/Volumes/NGS_2/Bioinformatics/jarnn/analysis_for_run.log', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

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
    return subprocess.run(*args, **kwargs)

run_name = str(sys.argv[1])
try:
    run_type = str(sys.argv[2])
except:
    run_type = None

config = SourceFileLoader("config","/Volumes/NGS_2/Bioinformatics/jarnn/config.py").load_module()

# Function to handle the stdout of the bs CLI tool. Returns a list of list of strings.
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
    return tmp

# Slack_sdk values needed for sending messages to Slack. Uses an API already set up on the Slack website for the UPHL Workspace to post messages on the notifications channel.
# Function makes sending Slack messages as easy as using the print funcition.
client = WebClient(token=config.token)
channel_id = config.channel_id
@log(my_logger=logger)
def slack_message(string):
    try:

        result = client.chat_postMessage(
            channel=channel_id,
            text=string
        )

    except:
        logger.info("Slack Error")

# These are the config files that are on the production account
configurations=["bioinfo"]

# This While loops Uses the BaseSpace CLI tool to monitor the progress of the run
t=0
p=0
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
                logger.info('%s is "Complete" on BSSH' % run_name)
                t=1
                break
        except:
            print('Not Complete')

        try:
            if tmp.at[args.run_name,'Status']=='Failed' or tmp.at[args.run_name,'Status']=='Stopped' or tmp.at[run_name,'Status']=='Needs Attention' or tmp.at[run_name,'Status']=='Timed Out':
                user=i
                idd=tmp.at[args.run_name,'Id']
                slack_message('%s has "Failed" or was unable to complete on BSSH; Script is aborting, check BSSH for more information' % run_name)
                logger.info('%s has "Failed" or was unable to complete on BSSH; Script is aborting, check BSSH for more information %s' % (run_name,datetime.now()))
                sys.exit()
        except:
            print('Not Failed')
        if run_type == 'mycosnp':
            if tmp.at[run_name,'Status']=='Needs' and  p == 0:
                user=i
                idd=tmp.at[run_name,'Id']
                slack_message('%s is "Needs Attention" on BSSH, starting "BCL Convert for ICA (Beta)" with CLI' % run_name)
                logger.info('%s is "Needs Attention" on BSSH, starting "BCL Convert for ICA (Beta)" with CLI' % run_name)
                bashCommand="bs launch application --config=bioinfo --name 'BCL Convert for ICA (Beta)' --option=bssh_run_id:%s" % idd
                result = subprocess.run(bashCommand, shell=True, stdout=subprocess.PIPE)
                logger.info(result.stdout)
                p = 1
    if t==0:
        print('Sleep')
        time.sleep(1200)


if run_type:
    if run_type == 'grandeur':
        process = subprocess.Popen(["python","/Volumes/NGS_2/Bioinformatics/jarnn/grandeur_aws_automation.py", "%s" % run_name], stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, text=True)

        stdout, stderr = process.communicate()
        print("Output:", stdout, stderr)
    if run_type == 'mycosnp':
        print("No automation")

my_subprocess_run(["screen", "-S", "%s" % run_name, "-X", "quit"])
