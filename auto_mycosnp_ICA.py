#!/usr/bin/env python3

"""
Author: John Arnn
Released: 2022-09-20
Version: 1.0.0
Description:
This script will create samplesheet; upload samplesheet to ICA; collect needed ICA ids to start a pipeline analysis;
build the icav2 command to start, and then start the analysis. If analysis fails to start use the icav2 arg that is created,
then use icav2 manually to troubleshoot issue. Most likely: IDS incorrect; IDS not linked to project; syntax issue with command.
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
import logging

logging.basicConfig(filename='/Volumes/IDGenomics_NAS/Bioinformatics/jarnn/analysis_for_run.log', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# create logger
logger = logging.getLogger('auto_mycosnp_ICA.py')
logger.setLevel(logging.DEBUG)

# This funciton uses the ica CLI tool to return info from ICA
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
logger.info("Current date and time : ")
logger.info(now.strftime("%Y-%m-%d %H:%M:%S"))

run_name=str(sys.argv[1])
if len(sys.argv) > 2:
    additional_ref=str(sys.argv[2])
else:
    additional_ref=''

bashCommand="icav2 projects enter BSSH UPHL_Bioinfo"
process = subprocess.Popen(bashCommand.split(" ",3), stdout=subprocess.PIPE)
process.communicate()

# Find and Link data on ICA related to run
bashCommand = "icav2 projectdata list --parent-folder /ilmn-analyses/"
tmp= icav_out(bashCommand)
for i in range(len(tmp)):
    tmp[i]=tmp[i].split()[0]

folders=tmp

experiments=[]
for folder in folders:
    if folder.startswith(run_name):
        print("found Folder")
        ica_target=folder
print(ica_target)

#Mycosnp needs a samplesheet, as input and must be uploaded into ICA
try:
    os.mkdir("./%s_samplesheet/" % run_name)
except:
    logger.info("Folder Already Exits")

#The names of the samples, and there ICA ids must be downloaded from ICA
bashCommand = "icav2 projectdata list  --parent-folder /ilmn-analyses/" +  ica_target + "/output/Samples/"
logger.info(bashCommand)
tmp= icav_out(bashCommand)
logger.info(tmp)
ica_lanes=[]
for i in tmp:
    ica_lanes.append(i.split(" ")[1])

ica_names=[]
for i in ica_lanes:
    bashCommand = "icav2 projectdata list  --parent-folder  /ilmn-analyses/" +  ica_target + "/output/Samples/Lane_1/"
    tmp= icav_out(bashCommand)
    for j in tmp:
        if not "Undetermined" in j.split(" ")[0]:
            ica_names.append(j.split(" ")[0])
logger.info(ica_names)
ica_ids=[]
sample_names=[]
for i in ica_names:
    bashCommand = 'icav2 projectdata list  --parent-folder /ilmn-analyses/' +  ica_target + '/output/Samples/Lane_1/' + i + '/'
    logger.info(bashCommand)
    tmp= icav_out(bashCommand)
    logger.info(tmp)
    for j in tmp:
        ica_ids.append(j.split(" ")[3]+",")
        sample_names.append(j.split(" ")[0])

logger.info(sample_names)
sample_sheet=[]
sample_sheet.append('sample_id,fastq_1,fastq_2\n')
for i in sample_names:
    if i.split('_')[3] == 'R1':
        tmp=i.split('_')[0]+','+i
        tmp=tmp+','+i.replace('R1','R2')+'\n'
        sample_sheet.append(tmp)

bashCommand = "icav2 projects enter Testing"
process = subprocess.Popen(bashCommand.split(" ",3), stdout=subprocess.PIPE)
process.communicate()

file = open("./%s_samplesheet/samplesheet.csv" % run_name, "w")
file.write("".join(sample_sheet))
file.close()

file = open("./%s_samplesheet/samples.csv" % run_name, "w")
file.write("".join(ica_ids))
file.close()

bashCommand = "icav2 projects enter Testing"
process = subprocess.Popen(bashCommand.split(" ",3), stdout=subprocess.PIPE)
process.communicate()

#All samples must be linked to Testing project in order to run in the pipeline
sams=open('./%s_samplesheet/samples.csv' % run_name,'r').read()
for i in range(len(sams.split(','))):
       bashCommand = "icav2 projectdata link %s" % sams.split(',')[i]
       process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
       process.communicate()

bashCommand = "icav2 projectdata link %s" % ica_target
process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
process.communicate()

time.sleep(60)

bashCommand = "icav2 projects enter Testing"
process = subprocess.Popen(bashCommand.split(" ",3), stdout=subprocess.PIPE)
process.communicate()

time.sleep(10)

bashCommand = "icav2 projectdata upload ./%s_samplesheet" % run_name
process = subprocess.Popen(bashCommand.split(" "), stdout=subprocess.PIPE, stdin=subprocess.PIPE)
process.communicate(input=b'y')

time.sleep(60)

bashCommand = "icav2 projectdata list --data-type FILE --parent-folder /%s_samplesheet/ --file-name samplesheet.csv" % run_name
tmp= icav_out(bashCommand)
samplesheet=tmp[0].split(' ')[3]

# Create icav2 argument
arg = "icav2 projectpipelines start nextflow CDC_mycosnp_V1_5 --input input_samples:"
arg = arg + sams[:-1]
arg = arg + ' --input input_csv:%s ' % samplesheet
arg = arg + '--input modules_json:fil.c342df9dfda44a04d1c908db4e9f2230 --input schema_json:fil.f615c3ae7e4443dcd1c808db4e9f2230  --input project_dirs:fol.2c483d7be7ad4157d1d408db4e9f2230,fol.7a306f76d98145550b0108db50afa89b,fol.a39c43d0b19a43420a8908db50afa89b,fol.a8886091ec374f12d15908db4e9f2230,fol.13265a82fd7d4e6e0a6808db50afa89b,fol.5b0716dd740544260a6108db50afa89b,fol.56d4d2b443f44148098c08db50afa89b,fol.214d19fe98244c610aaf08db50afa89b --input fasta:fil.a582dffcf93846d6f72908da19bdaa25 --input vcfs:fil.153d26c111c24a8f83f208da91c1bd10,fil.b2dfdf02c73f4202840a08da90e3f08e,fil.0997542c46584ac7c22608da90e46b13,fil.2b5a649a82a741223e3908da91ac5070,fil.6f3b4b60bcc1428f840808da90e3f08e,fil.3aa000758ee74665840708da90e3f08e,fil.48e5da86c23c4477840908da90e3f08e,fil.fda5367ecc594e453e3408da91ac5070,fil.2a23225c87364ab0840608da90e3f08e,fil.3e098ebbea8e4a153e3308da91ac5070,fil.d1492fa460a84cc3840408da90e3f08e,fil.5f59db21427d401a840508da90e3f08e,fil.4229c1f391704be73e3808da91ac5070,fil.cfbecd65057f43653e3708da91ac5070,fil.be8d2841fb814e17840308da90e3f08e,fil.fdd7cdf1e1bf4ad03e3208da91ac5070,fil.b3c8ebad381c4ef73e3508da91ac5070,fil.e5e192ef1c6a4f49840208da90e3f08e,fil.519bdcea0ff94e0b3e3008da91ac5070,fil.b205683a41b24adf3e3608da91ac5070,fil.07fb83a0249a4652840108da90e3f08e,fil.8b2e87488a0142713e3108da91ac5070,fil.5d6e950bbcaf4b7b3e2f08da91ac5070,fil.1e2f78b70baa437883fd08da90e3f08e,fil.09f27ac17c9443da83fc08da90e3f08e,fil.845c726350b74ba983fe08da90e3f08e,fil.f18b1d1deb6742283e2e08da91ac5070 --parameters add_vcf_file:add_clades_vcf.txt '
arg = arg + '--storage-size large --user-reference CDC_mycosnp_V1_5_%s%s' % (run_name,additional_ref)

logger.info(arg)
os.system(arg)
