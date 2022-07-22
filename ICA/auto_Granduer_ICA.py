#!/usr/bin/env python3

import os
import subprocess
import json
import re
import time
import pandas as pd
import numpy as np
from datetime import date,datetime,timedelta
from collections import Counter

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

# While loop is infinite will keep script running as long as it doesn't error out.
go=1
while go == 1:
    print('Looking for analyses that need to start!')
    #This block set the icav2 tool to correct project in use
    bashCommand="icav2 projects enter Testing"
    process = subprocess.Popen(bashCommand.split(" ",3), stdout=subprocess.PIPE)
    process.communicate()

    #This  block collects the information of data and runs on ICA
    bashCommand = "icav2 projectdata list --file-name UT-M03999-,UT-M07101-,UT-M70330-,UT-FS10001397-  --parent-folder / --match-mode FUZZY"
    tmp= icav_out(bashCommand)

    #This block removes runs that have already had anaylsis completed
    stubs=[]
    for i in tmp:
        stubs.append(i.split()[0][0:17])
    counts = Counter(stubs)
    keeps=[k for k in stubs if counts[k] == 1]
    stubs_d = {k: v for v, k in enumerate(stubs)}
    keeps2=[]
    for i in keeps:
        keeps2.append(int(stubs_d[i]))
    tmp = [tmp[i] for i in keeps2]
    #This block is needed becuase we started to stream data to ICA before pipelines were working
    delta = 10
    today = datetime.now()    
    cutoff = today - timedelta(days=delta)


    for i in range(3):
        for i in range(len(tmp)-1,-1,-1):
            try:
                date=datetime.strptime(tmp[i].split()[1].split('-')[2].split('_')[0], '%y%m%d')
            except:
                del tmp[i]
                break
            if date < cutoff:
                del tmp[i]

    #This block kicks off a new anaylsis run for data that does not had it done yet
    if len(tmp)>0:
        print('Start Analysis on ICA \n %s' % tmp)
        run_name=tmp[0].split()[1]
        bashCommand = "icav2 projectdata list --parent-folder %s --match-mode FUZZY" % tmp[0].split()[0]
        tmp= icav_out(bashCommand)
        ica_id=tmp[0].split()[4]

        # Create icav2 argument
        arg = "icav2 projectpipelines start nextflow UPHL-BioNGS_Granduer_V2 --input reads:%s " % ica_id
        arg = arg + "--input project_dirs:fol.fb0091ef9e4d4e515b6408da63045a75,fol.90b6b7865bc7434384e408da6377c840,fol.8802646a4148485884df08da6377c840,fol.17212ac619d44b68296008da58d44868,fol.ae742e54d4a54a8acb9c08da64f9d308,fol.97c3321c555a4b1c672f08da58d44868 "
        arg = arg + "--user-reference %s_Granduer_Analysis" % run_name

        print(arg)

        process = subprocess.Popen(arg.split(" "), stdout=subprocess.PIPE)
        print(process.communicate())
        print('Run started; wait 12 hr to check for new run')
    else:
        print('No new runs waiting 12 hr')
    time.sleep(31200)
