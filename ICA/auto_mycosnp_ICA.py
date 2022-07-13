#!/usr/bin/env python3

import os
import subprocess
import json
import re
import time
import pandas as pd
import numpy as np
from datetime import date

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

# While loop is infinate will keep script running as long as it dosent error out.
go=1
while go == 1:
# Sequencing runs are directly upload to ICA after basecalling into this project
    bashCommand="icav2 projects enter BSSH UPHL_Bioinfo"
    process = subprocess.Popen(bashCommand.split(" ",3), stdout=subprocess.PIPE)
    process.communicate()
#Folders of ICA Runs
    bashCommand = "icav2 projectdata list --data-type FOLDER --file-name app.* --match-mode FUZZY"
    tmp= icav_out(bashCommand)
# ICA runs
    ica_r=[]
    for i in tmp:
        ica_r.append(i.split(" ")[0])

    runs_on_ica=[]
    for i in range(len(tmp)):
        runs_on_ica.append(tmp[i].split()[0].split('/')[2])
# The plan is to download only the files that are commonly needed by Tom and use these directories as a way to way to moniter if anaylsis has completed.
    runs_completed_analysis=os.listdir("/Volumes/IDGenomics_NAS/ICA/Runs_On_ICA")
#This maybe unneeded but during testing I think the os package generates this file that needs to be removed from list
    try:
        runs_completed_analysis.remove('@eaDir')
    except:
        print("Nope")

#This checks if an anaylsis needs to be kicked off if not the script sleeps for an hour
    if len(runs_completed_analysis) == len(runs_on_ica):
        print('No new runs waiting 1 hr')
        time.sleep(3600)


    else:
        #Formats string to work in ICAv2
        run=list(set(runs_on_ica)-set(runs_completed_analysis))
        run='/datasets/'+run[0]+'/'

        try:
            os.remove('./bsshinput.json')
        except:
            print("No ./bsshinput.json")

        # The bsshinput.json has our experiment name that we typically use i.e. UT-VH0770-220318
        bashCommand = "icav2 projectdata list --data-type FILE --parent-folder %s --file-name bsshinput.json" % (run)
        print(bashCommand)
        tmp= icav_out(bashCommand)
        download=tmp[0].split(' ')[4]

        bashCommand = "icav2 projectdata download %s" % download
        process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
        process.communicate()

        Experiment=json.load(open('./bsshinput.json'))['BsshRun']['ExperimentName']

    #Mycosnp needs a samplesheet, as input and must be uploaded into ICA
        try:
            os.mkdir("./%s_samplesheet/" % Experiment)
        except:
            print("Folder Already Exits")

    #The names of the samples, and there ICA ids must be downloaded from ICA
        bashCommand = "icav2 projectdata list  --parent-folder " +  run + "output/fastqs/Samples/"
        tmp= icav_out(bashCommand)

        ica_lanes=[]
        for i in tmp:
            ica_lanes.append(i.split(" ")[1])

        ica_names=[]
        for i in ica_lanes:
            bashCommand = "icav2 projectdata list  --parent-folder  " +  run + "output/fastqs/Samples/Lane_1/"
            tmp= icav_out(bashCommand)
            for j in tmp:
                ica_names.append(j.split(" ")[0])

        ica_ids=[]
        sample_names=[]
        for i in ica_names:
            bashCommand = 'icav2 projectdata list  --parent-folder ' + i
            tmp= icav_out(bashCommand)
            for j in tmp:
                ica_ids.append(j.split(" ")[4]+",")
                sample_names.append(j.split(" ")[1])

        for i in range(len(ica_names)):
            if re.search("Undetermined/", ica_names[i]):
                del(ica_names[i])
                break

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

    # Mycosnp needs examples of clades so these samples need to be included in each run
        bashCommand = "icav2 projectdata list --parent-folder /Candida_auris_clade_controls/Raw/"
        controls= icav_out(bashCommand)
        for i in controls:
            if i.split('_')[5].split('.')[0] == 'R1':
                tmp=i.split()[1].split('.')[0]+','+i.split()[1]
                tmp=tmp+','+i.split()[1].replace('R1','R2')+'\n'
                sample_sheet.append(tmp)
            if i.split('_')[5].split('.')[0] == '1':
                tmp=i.split()[1].split('.')[0]+','+i.split()[1]
                tmp=tmp+','+i.split()[1].replace('1','2')+'\n'
                sample_sheet.append(tmp)

        file = open("./%s_samplesheet/samplesheet.csv" % Experiment, "w")
        file.write("".join(sample_sheet))
        file.close()

        file = open("./%s_samplesheet/samples.csv" % Experiment, "w")
        file.write("".join(ica_ids))
        file.close()

        bashCommand = "icav2 projects enter Testing"
        process = subprocess.Popen(bashCommand.split(" ",3), stdout=subprocess.PIPE)
        process.communicate()

    #All samples must be linked to Testing project in order to run in the pipeline
        sams=open('./%s_samplesheet/samples.csv' % Experiment,'r').read()
        for i in range(len(sams.split(','))):
               bashCommand = "icav2 projectdata link %s" % sams.split(',')[i]
               process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
               process.communicate()


        bashCommand = "icav2 projectdata upload ./%s_samplesheet" % Experiment
        process = subprocess.Popen(bashCommand.split(" "), stdout=subprocess.PIPE, stdin=subprocess.PIPE)
        process.communicate(input=b'y')

        bashCommand = "icav2 projectdata list --data-type FILE --parent-folder /%s_samplesheet/ --file-name samplesheet.csv" % Experiment
        tmp= icav_out(bashCommand)
        samplesheet=tmp[0].split(' ')[4]

        bashCommand = "icav2 projectdata list --parent-folder /Candida_auris_clade_controls/Raw/"
        tmp= icav_out(bashCommand)

        controls=''
        for i in tmp:
            controls=controls+i.split()[4]+','

        # Create icav2 argument
        arg = "icav2 projectpipelines start nextflow CDC_mycosnp_V1_3 --input input_samples:"
        arg = arg + controls
        arg = arg + sams[:-1]
        arg = arg + ' --input input_csv:%s ' % samplesheet
        arg = arg + '--input modules_json:fil.59d555e385bc44373e0508da602cff6c --input schema_json:fil.67a59465102f49653e0b08da602cff6c --input project_dirs:fol.9f7bb648f8b14ad1bd5908da602d9944,fol.1c6b76e2679e46a5bd5708da602d9944,fol.4c3975313355455e3e0708da602cff6c,fol.df431f633c8a405b3db608da602cff6c,fol.a0755943991b4b713d9f08da602cff6c,fol.287f4196a2574a77346f08da603e530e,fol.de2553cf82f74a103d8c08da602cff6c,fol.8bb8690a65d8459e3d5608da602cff6c,fol.08cbd7c3121a4b503dd008da602cff6c --input fasta:fil.a582dffcf93846d6f72908da19bdaa25 '
        arg = arg + '--user-reference CDC_mycosnp_V1_3_%s_update' % Experiment

        print(arg)
        process = subprocess.Popen(arg.split(" "), stdout=subprocess.PIPE)
        process.communicate()

        run=list(set(runs_on_ica)-set(runs_completed_analysis))
        os.mkdir('/Volumes/IDGenomics_NAS/ICA/Runs_On_ICA/%s' % run[0] )
