#!/usr/bin/env python3

"""
Author: John Arnn
Released: 2022-09-20
Description:
This script will collect needed ICA ids to start a pipeline analysis; build the icav2 command to start, and then start the analysis.
If analysis fails to start use the icav2 arg that is created, then use icav2 manually to troubleshoot issue.
Most likely: IDS incorrect; IDS not linked to project; syntax issue with command.
EXAMPLE:
python auto_mycosnp_ICA.py UT-VH0770-220915
"""

import os
import sys
import subprocess
import json
import re
import pandas as pd
import numpy as np
import datetime

# This function uses the ica CLI tool to return info from ICA
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

now = datetime.datetime.now()
print ("Current date and time : ")
print (now.strftime("%Y-%m-%d %H:%M:%S"))

bashCommand = "icav2 projects enter Testing"
process = subprocess.Popen(bashCommand.split(" ",3), stdout=subprocess.PIPE)
process.communicate()

run_name=str(sys.argv[1])
if len(sys.argv) > 2:
    additional_ref=str(sys.argv[2])
else:
    additional_ref=''

bashCommand = "icav2 projectdata upload /Volumes/IDGenomics_NAS/WGS_Serotyping/%s/Sequencing_reads/Raw /%s/" % (run_name,run_name)
process = subprocess.Popen(bashCommand.split(" ",3), stdout=subprocess.PIPE)
process.communicate()

bashCommand = "icav2 projectdata list --parent-folder /%s/ --match-mode FUZZY" % run_name
tmp= icav_out(bashCommand)
ica_id=tmp[0].split()[4]

# Create icav2 argument
arg = "icav2 projectpipelines start nextflow UPHL-BioNGS_Granduer_V2 --input reads:%s " % ica_id
arg = arg + "--input project_dirs:fol.fb0091ef9e4d4e515b6408da63045a75,fol.90b6b7865bc7434384e408da6377c840,fol.8802646a4148485884df08da6377c840,fol.17212ac619d44b68296008da58d44868,fol.756293fdaa3942cc3b9f08da58d44869,fol.97c3321c555a4b1c672f08da58d44868 "
arg = arg + "--user-reference %s_Granduer_Analysis%s" % (run_name,additional_ref)

print(arg)

process = subprocess.Popen(arg.split(" "), stdout=subprocess.PIPE)
print(process.communicate())
