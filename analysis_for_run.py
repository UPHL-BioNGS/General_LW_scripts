#!/usr/bin/env python3

import subprocess
import time
import re
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from importlib.machinery import SourceFileLoader
import xml.etree.ElementTree as ET
import requests
from requests.auth import HTTPBasicAuth
from typing import Union
import functools
import logging

logging.basicConfig(filename='/Volumes/IDGenomics_NAS/Bioinformatics/jarnn/analysis_for_run.log', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# create logger
logger = logging.getLogger('analysis_for_run.py')
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

config = SourceFileLoader("config","/Volumes/IDGenomics_NAS/Bioinformatics/jarnn/config.py").load_module()

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

# Clarity login info
c_user=config.clarity_user
c_password=config.clarity_password

@log(my_logger=logger)
def my_subprocess_run(*args, **kwargs):
    return subprocess.run(*args, **kwargs)

@log(my_logger=logger)
def slack_message(string):
    try:

        result = client.chat_postMessage(
            channel=channel_id,
            text=string
        )

    except:
        logger.info("Slack Error")
@log(my_logger=logger)
def open_screen_and_run_script(script_path, experiment_name, run_type=None):
    # Open a new detached screen session
    my_subprocess_run(["screen", "-dmS",  experiment_name])

    # Send the command to run the script in the screen session
    if run_type is None:
        my_subprocess_run(["screen", "-S", experiment_name, "-X", "stuff", f"python3 {script_path}  {experiment_name}\n"])

    else:
        my_subprocess_run(["screen", "-S", experiment_name, "-X", "stuff", f"python3 {script_path}  {experiment_name}  {run_type}\n"])

@log(my_logger=logger)
def my_requests_get(*args, **kwargs):
    return requests.get(*args, **kwargs)


try:
    x=1
    while x==1:
            
        experiments_done = []

        with open('experiments_done.txt', 'r') as file:
            for line in file:
                experiments_done.append(line.strip())

        bssh_now=[]
        try:
            tmp=bs_out('bs list --config=bioinfo runs')
            for i in range(1,len(tmp)):
                bssh_now.append(tmp[i].split()[2])

            change=set(bssh_now) - set(experiments_done)
        except:
            change=[]

        logger.info(change)

        if len(change) > 0:
            for i in change:
                try:
                    xml=(requests.get("https://uphl-ngs.claritylims.com/api/v2/artifacts?containername=%s" % i, auth=HTTPBasicAuth(c_user, c_password)).content).decode("utf-8")
                                        # Parse the XML
                    root = ET.fromstring(xml)

                    # Extract the limsid attribute
                    artifact_limsids = re.findall(r'limsid="([^"]+)"', xml)

                    # Extract the limsid attribute

                    sample_lims_ids = []
                    for artifact_id in artifact_limsids:
                        xml=(requests.get("https://uphl-ngs.claritylims.com/api/v2/artifacts/%s" % artifact_id, auth=HTTPBasicAuth(c_user, c_password)).content).decode("utf-8")
                        match = re.search(r'sample\s+limsid="([^"]+)"', xml)
                        if match:
                            sample_lims_ids.append(match.group(1))

                    species=[]
                    for j in sample_lims_ids:
                        xml=(requests.get("https://uphl-ngs.claritylims.com/api/v2/samples/%s" % j, 
                                            auth=HTTPBasicAuth(c_user, c_password)).content).decode("utf-8")
                        # Parse the XML data
                        root = ET.fromstring(xml)
                                            
                        namespace_map = {
                                'udf': 'http://genologics.com/ri/userdefined',
                                'ri': 'http://genologics.com/ri',
                                'file': 'http://genologics.com/ri/file',
                                'smp': 'http://genologics.com/ri/sample'}

                        # Find the udf:field element with name="Species"
                        species_element = root.find('.//udf:field[@name="Species"]', namespaces=namespace_map)

                        # Extract the value of the udf:field element
                        species_value = species_element.text

                        species.append(species_value)
                    logger.info(species)
                    if len(species) > 0:
                        species=set(species)
                    if len(species) < 1:
                        xml=(requests.get("https://uphl-ngs.claritylims.com/api/v2/processes?type=Load%%20To%%20Reagent%%20Cartridge%%20(NextSeq%%201000/2000%%20Sequencing%%20v2.1)&udf.Run%%20Name=%s" % i, auth=HTTPBasicAuth('jarnn', 'civic1225CIVIC!@@%')).content).decode("utf-8")
                        art_step_details = re.findall(r'limsid="([^"]+)"', xml)
                        for j in art_step_details:
                            xml_art_step_details=(requests.get("https://uphl-ngs.claritylims.com/api/v2/steps/%s/details" % j,
                                        auth=HTTPBasicAuth(c_user, c_password)).content).decode("utf-8")
                            art_step_details = re.findall(r'limsid="([^"]+)"', xml_art_step_details)[0]
                            xml=(requests.get("https://uphl-ngs.claritylims.com/api/v2/artifacts/%s" % art_step_details, auth=HTTPBasicAuth('jarnn', 'civic1225CIVIC!@@%')).content).decode("utf-8")

                        # Extract the limsid attribute
                        sample_lims_ids= re.findall(r'limsid="([^"]+)"', xml)

                        species=[]
                        for j in sample_lims_ids:
                            xml=(requests.get("https://uphl-ngs.claritylims.com/api/v2/samples/%s" % j, 
                                                auth=HTTPBasicAuth(c_user, c_password)).content).decode("utf-8")
                            # Find the udf:field element with name="Species"
                            species_match = re.search(r'<udf:field name="Species" type="String">([^<]+)</udf:field>', xml)

                            # Extract the value of the udf:field element
                            if species_match:
                                species_value = species_match.group(1)
                                species.append(species_value)
                        logger.info(species)
                        if len(species) > 0:
                            species=set(species)
                except ValueError as ve:
                    logger.warning("API Calls to Clarity Failed for %s. Error: %s " % (i, str(ve)))
                if 'species' in locals():
                    slack_message("New Sequecning Run Started: %s. This is a run with %s samples" %  (i,species))
                    logger.info("New Sequecning Run Started: %s. This is a run with %s samples" %  (i,species))
                    if 'Candida' in species:
                        run_type = "mycosnp"
                    elif len(species) < 1:
                       run_type = ""
                    else:
                        run_type= "grandeur"
                    open_screen_and_run_script('screen_run.py',i, run_type)
                    del species

                else:
                    slack_message("New Sequecning Run Started: %s" %  i)
                    open_screen_and_run_script('screen_run.py',i)

            with open('experiments_done.txt', 'w') as file:
                for item in bssh_now:
                    file.write(str(item) + '\n')

        logger.info("No new runs sleeping: 20 min")
        time.sleep(1200)
except ValueError as ve:
    slack_message("analysis_for_run.py has errored out please restart!")
    logger.error('analysis_for_run.py has errored out. Error: %s' % ve)

