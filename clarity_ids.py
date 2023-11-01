#!/usr/bin/env python3

"""
Author: John Arnn
Release Date: 10/12/2023

Usage:
This script is used for the collection of Unquie IDs found in Clarity for all samples UPHL NGS processes.
It uses the Clarity API to retrieve data so you must have a active user account and password.
You also need to provide one of three flags:
    --all will download every samples unique ids. Tens of thousands of API calls so it takes at least 45 min to run.
    --list 1234,1234,1234 Provide the uphl accession followed by a , with no spaces for results for specfic samples
    --file provide a path to a txt file that has each sample seperated by a new line

The output of this script is a csv file into the directory the script was ran in named clarity_ids_output.csv.
OR use flag '--output' to provide full path and name of file

Users must have an account in Clarity that has the System Adminastrator Role.
"""

import argparse
import xml.etree.ElementTree as ET
import requests
from requests.auth import HTTPBasicAuth
import re
import pandas as pd

parser = argparse.ArgumentParser(description="A script that accepts user, password, and data source options.")
    
# Required arguments
parser.add_argument("--user", required=True, help="User name")
parser.add_argument("--password", required=True, help="User's password")
parser.add_argument("--output", help="Creates csv of all sampels")

# Either list or file must be provided
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("--list", help="Specify a list of samples you need ids for. 123,124,125")
group.add_argument("--file", help="Specify a file that has a sample name for each line of file")
group.add_argument("--all", action="store_true", help="Creates csv of all sampels")

args = parser.parse_args()

def flatten(l):
    return [item for sublist in l for item in sublist]

udfs=['ARLN ID','CDC ID','GCWGS ID','GISP ID','PNUSA Number']

# Check User Name and Password
xml = (requests.get("https://uphl-ngs.claritylims.com/api/v2/samples/%s" % 'WAG357A292', 
        auth=HTTPBasicAuth(args.user, args.password)).content).decode("utf-8")
check=(re.findall(r'<message>(.*?)</message>', xml))

if check == ['Unauthorized']:
    sys.exit('User name or password is unauthorized. Please check username and password!')

if args.all:
    sample_lims_ids = []

    xml=(requests.get("https://uphl-ngs.claritylims.com/api/v2/samples", 
            auth=HTTPBasicAuth(args.user, args.password)).content).decode("utf-8")

    sample_lims_ids.append(re.findall(r'limsid="([^"]+)"', xml))

    index=500
    while index > 0:
        xml=(requests.get("https://uphl-ngs.claritylims.com/api/v2/samples?start-index=%s" % index, 
            auth=HTTPBasicAuth(args.user, args.password)).content).decode("utf-8")
        index+=500
        if len(xml) < 300:
            index=0
        sample_lims_ids.append(re.findall(r'limsid="([^"]+)"', xml))

    sample_lims_ids=flatten(sample_lims_ids)

if args.list:
    sample_lims_ids = args.list.split(',')

if args.file:
    sample_lims_ids = []

    with open(args.file, 'r') as file:
        for line in file:
            sample_lims_ids.append(line.strip())


if not args.all:
    limsids = {}
    for j in sample_lims_ids:
        xml=(requests.get("https://uphl-ngs.claritylims.com/api/v2/samples?name=%s" % j, 
            auth=HTTPBasicAuth(args.user, args.password)).content).decode("utf-8")
        # Parse the XML data
        limsids[j]=(re.findall(r'limsid="([^"]+)"', xml))

    ids_df=[]

    for j in limsids.keys():
        try:
            xml=(requests.get("https://uphl-ngs.claritylims.com/api/v2/samples/%s" % limsids[j][0], 
                auth=HTTPBasicAuth(args.user, args.password)).content).decode("utf-8")
            # Parse the XML data
            root = ET.fromstring(xml)
                                                    
            namespace_map = {
                            'udf': 'http://genologics.com/ri/userdefined',
                            'ri': 'http://genologics.com/ri',
                            'file': 'http://genologics.com/ri/file',
                            'smp': 'http://genologics.com/ri/sample'}

            # Find the udf:field element with name="Species"
            ids=[]
            for i in udfs:
                species_element = root.find('.//udf:field[@name="%s"]'% i, namespaces=namespace_map)
                try:
                    ids.append(species_element.text)
                except:
                    ids.append("")
            ids_df.append([j]+ids)

        except:
            continue

    if args.output:
        pd.DataFrame(ids_df, columns = ['Sample_ID']+udfs).to_csv(args.output, index=False)
    else:
        pd.DataFrame(ids_df, columns = ['Sample_ID']+udfs).to_csv('clarity_ids_output.csv', index=False)

else:
    ids_df=[]

    for j in sample_lims_ids:
        try:
            xml=(requests.get("https://uphl-ngs.claritylims.com/api/v2/samples/%s" % j, 
                auth=HTTPBasicAuth(args.user, args.password)).content).decode("utf-8")
            # Parse the XML data

            name = re.findall(r'<name>(.*?)</name>', xml)

            root = ET.fromstring(xml)
                                                    
            namespace_map = {
                            'udf': 'http://genologics.com/ri/userdefined',
                            'ri': 'http://genologics.com/ri',
                            'file': 'http://genologics.com/ri/file',
                            'smp': 'http://genologics.com/ri/sample'}

            # Find the udf:field element with name="Species"
            ids=[]
            for i in udfs:
                species_element = root.find('.//udf:field[@name="%s"]'% i, namespaces=namespace_map)
                try:
                    ids.append(species_element.text)
                except:
                    ids.append("")
            ids_df.append([name]+ids)

        except:
            continue

    if args.output:
        pd.DataFrame(ids_df, columns = ['Sample_ID']+udfs).to_csv(args.output, index=False)
    else:
        pd.DataFrame(ids_df, columns = ['Sample_ID']+udfs).to_csv('clarity_ids_output.csv', index=False)
