import argparse
import xml.etree.ElementTree as ET
import requests
from requests.auth import HTTPBasicAuth
import re
import pandas as pd

parser = argparse.ArgumentParser(description="A script that accepts user, password, and data source options.")
    
# Required arguments
parser.add_argument("--user", help="User name")
parser.add_argument("--password", help="User's password")

# Either list or file must be provided
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("--list", help="Specify a list of samples you need ids for. 123,124,125")
group.add_argument("--file", help="Specify a file that has a sample name for each line of file")
group.add_argument("--all", action="store_true", help="Creates csv of all sampels")

args = parser.parse_args()

def flatten(l):
    return [item for sublist in l for item in sublist]

udfs=['ARLN ID','CDC ID','GCWGS ID','GISP ID','PNUSA Number']

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

    with open(args.fil, 'r') as file:
        for line in file:
            sample_lims_ids.append(line.strip())

limsids = {}
for j in sample_lims_ids:
    print(j)
    xml=(requests.get("https://uphl-ngs.claritylims.com/api/v2/samples?name=%s" % j, 
        auth=HTTPBasicAuth(args.user, args.password)).content).decode("utf-8")
    # Parse the XML data
    limsids[j]=(re.findall(r'limsid="([^"]+)"', xml))

ids_df=[]

for j in limsids.keys():
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

pd.DataFrame(ids_df, columns = ['Sample_ID']+udfs).to_csv('clarity_ids_output.csv', index=False)
