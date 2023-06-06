#!/usr/bin/env python3

"""
Author: John Arnn
Released: 2022-09-20
Version: 1.0.0
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
import time

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

bashCommand = "icav2 projects enter Produciton"
process = subprocess.Popen(bashCommand.split(" ",3), stdout=subprocess.PIPE)
process.communicate()

run_name=str(sys.argv[1])
if len(sys.argv) > 2:
    additional_ref=str(sys.argv[2])
else:
    additional_ref=''


bashCommand = "icav2 projectdata list --file-name %s --match-mode FUZZY --parent-folder /" % (run_name[-6:]+"_"+run_name[3:9])
tmp= icav_out(bashCommand)
ica_folder=tmp[0].split()[0]

bashCommand = "icav2 projectdata list  --match-mode FUZZY --parent-folder /%s/Alignment_1/" % ica_folder
tmp= icav_out(bashCommand)
ica_folder2=tmp[0].split()[0]

bashCommand = "icav2 projectdata list  --match-mode FUZZY --parent-folder /%s/Alignment_1/%s/ --file-name Fastq" % (ica_folder,ica_folder2)
tmp= icav_out(bashCommand)
ica_id=tmp[0].split()[3]

# Create icav2 argument
arg = "icav2 projectpipelines start nextflow UPHL-BioNGS_Granduer_V3_1_20230523 --input reads:%s " % ica_id
arg = arg + "--input project_dirs:fol.8d6ce115bc654a98b4b908db5cb0c8b4,fol.4cfbf2608f0542e8822a08db520d1521,fol.083bc5fdf9cc4a1fb4d708db5cb0c8b4,fol.d8e135fc30984285829c08db520d1521,fol.258c3c406d844f39822208db520d1521,fol.17e932b9ea87429b824e08db520d1521,fol.3215c978710246b6694308daf8fa4ab4,fol.34b4cd1b57ab4c2331fd08db45a02d4f,fol.dc7067b8edf9407943ef08db4a610552 "
arg = arg + "--user-reference %s_Granduer_Analysis%s --storage-size medium" % (run_name,additional_ref)

print(arg)

os.system(arg)
