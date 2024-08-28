#!/usr/bin/env python3

# Written in Python 3.11.2. Tested on Python 3.7.11,3.8.8, 3.9.13, 3.10.8

# Packages Needed pandas, openpyxl, xlrd
# Install with: pip3 install pandas openpyxl xlrd

"""
This is a modified version of the orginal accession_for_clarity.py, which strips out the search and retrivial of 
samples tested at UPHL and found in the shared drives work books. This portion of the script often failed
for unknown reasons and these samples are the least the we process we get a majority from IHC,ARUP, and U of U;
because of this I made this backup for that the majority of samples could make it into Clarity. Please use the original script
if trying to capture these samples in the future. This is unlikly as accessioning will be automated with LabWare 8 in the future.
"""

import pandas as pd
import os
import sys
import numpy as np
import glob
import re
from datetime import datetime, timedelta

print("Running!!!")


import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=UserWarning)
### USAGE ### python accession_for_clarity.py "path/to/files/fromclarity" "path/to/files/fromclarity.etc"
# Must be log into or mount these servers smb://172.16.109.9 smb://168.180.220.43. Must include files, project samplesheets, from Clarity for all COVIDSEQ projects
# DO NOT MAKE DUPLICATES IN CLARITY!!! PLEASE READ README.md and proceed with caution. 


path_to_project_lists=[]
for i in range(len(sys.argv)-1):
    path_to_project_lists.append(str(sys.argv[i+1]))
    print('Import %d' % i)

atog=[]
for i in ['A','B','C','D','E','F','G','H']:

     for j in range(12):
        atog.append('%s%s' % (i,(j+1)))

# Import All_ncovid*.csv
#ip address smb://172.16.109.9 smb://168.180.220.43
ncovid=pd.read_csv('/Volumes/LABWARE/Shared_Files/Mirth/COVID_data_import/ncovOverview.csv',usecols=['submitterId','sampleNumber','collectionDate','receivedDate','result','customer'], encoding = "ISO-8859-1", low_memory=False)
print("Read ncovid!")
# Import NGS_Covid_*.csv
NGS_Covid=pd.read_csv('/Volumes/LABWARE/Shared_Files/Mirth/COVID_data_import/NGS_Covidtest.csv',usecols=['observations','customer','submitterId','sampleNumber','collectionDate','receivedDate','PlateName','PlateWell'], encoding = "ISO-8859-1", low_memory=False)
print("Read NGS_Covid")
NGS_Covid['receivedDate']=NGS_Covid['receivedDate'].fillna(NGS_Covid['collectionDate'])
# Clean up
end = datetime.now().date()
plot_end=end
plot_start=end-timedelta(days=30)
NGS_Covid['receivedDate']= pd.to_datetime(NGS_Covid['receivedDate']).dt.date
NGS_Covid=NGS_Covid[(NGS_Covid['receivedDate'] > plot_start) & (NGS_Covid['receivedDate'] < plot_end)]
NGS_Covid=NGS_Covid.drop(columns=['receivedDate'])

#Get Panther Tubes
end = datetime.now().date()
plot_end=end
plot_start=end-timedelta(days=30)
ncovid['receivedDate']= pd.to_datetime(ncovid['receivedDate'], errors='coerce').dt.date
panther=ncovid[(ncovid['receivedDate'] > plot_start) & (ncovid['receivedDate'] < plot_end)]
panther=panther.drop(columns=['receivedDate'])
ppanther = panther[panther['result']== 'SARS-COV-2 Detected']
#HOT FIX FOR SMH2
smh2=ncovid[ncovid['customer']== 'SMH2']
ppanther = pd.concat([ppanther, smh2], ignore_index=True)

# Create DF to merge into
clarity= pd.DataFrame(columns = ['Sample/Name', 'Container/Type', 'Container/Name', 'Sample/Well Location',
                             'UDF/External Sample ID',
                             'UDF/Sample Collection DateTime','UDF/Test Requested','UDF/Test Selected','UDF/Provider Code'])
# Merge NGS_Covid into clarity
tmp = NGS_Covid.rename(columns={'customer': 'UDF/Provider Code', 'sampleNumber': 'Sample/Name',
                               'submitterId':'UDF/External Sample ID', 'collectionDate':'UDF/Sample Collection DateTime',
                               'PlateName':'Container/Name','PlateWell':'Sample/Well Location'})
tmp = tmp.drop(columns= ['observations'])
clarity = clarity.append(tmp, ignore_index=True)

#tmp = tmp.drop(columns= ['ORF1ab Ct','N gene Ct','S gene Ct'])
#tmp['UDF/Provider Code'] = 'UPHL'
#clarity = clarity.append(tmp, ignore_index=True)

tmp=ppanther.rename(columns={'sampleNumber':'Sample/Name',
                      'collectionDate':'UDF/Sample Collection DateTime',
                     'customer':'UDF/Provider Code'})
tmp = tmp.drop(columns= ['submitterId','result'])
tmp['Sample/Name'] = tmp['Sample/Name'].astype(int)
clarity = clarity.append(tmp, ignore_index=True)


# Filter Out Samples Already in Clarity
i=0
for j in path_to_project_lists:
    columns=list(pd.read_excel('%s' % j, skiprows=2,nrows=0).columns)
    columns={v: k for v, k in enumerate(columns)}
    if i == 0:
        in_c_tmp=pd.read_excel('%s' % j, skiprows=5, header=None)
        in_c_tmp=in_c_tmp.rename(columns=columns)
        in_c_tmp.drop(in_c_tmp.tail(1).index,inplace=True)
        in_c=in_c_tmp
    if i >0:
        in_c_tmp=pd.read_excel('%s' % j, skiprows=5, header=None)
        in_c_tmp=in_c_tmp.rename(columns=columns)
        in_c_tmp.drop(in_c.tail(1).index,inplace=True, errors='ignore')
        in_c_tmp['Sample/Name'] = pd.to_numeric(in_c_tmp['Sample/Name'], errors='coerce')
        in_c=in_c.append(in_c_tmp, ignore_index=True)
    i=+ 1
    print("Imported: %s" % j)

samples = in_c['Sample/Name'].tolist()


clarity = clarity.drop(list(clarity[clarity['Sample/Name'].isin(samples)].index))


clarity['UDF/Test Requested']= 'COVIDSeq'
clarity['UDF/Test Selected']= 'COVIDSeq'
for index,row in clarity.iterrows():
    if  not pd.isnull(row['Container/Name']):
        row['Container/Type'] = '96 well plate'
# Fix the Well Locations to match Clarity
for index, row in clarity.iterrows():
    if not pd.isnull(row['Sample/Well Location']):
        tmp=list(row['Sample/Well Location'])
        tmp.insert(1, ':')
        if tmp[2] == '0':
            del tmp[2]
        tmp=''.join(tmp)
        row['Sample/Well Location'] = tmp

clarity = clarity.replace(np.nan, '', regex=True)
hold=clarity.values.tolist()
hold.insert( 0, ["<TABLE HEADER>"])
hold.insert( 1, ["Sample/Name", "Container/Type", "Container/Name", "Sample/Well Location", "UDF/External Sample ID","UDF/Sample Collection DateTime", "UDF/Test Requested","UDF/Test Selected", "UDF/Provider Code"])
hold.insert( 2, ["</TABLE HEADER>"])
hold.insert( 3, ["<SAMPLE ENTRIES>"])
hold.append(["</SAMPLE ENTRIES>"])

with open('accession_for_clarity%s.csv' % datetime.now().strftime("%Y_%m_%d"), 'w+') as f:
    for i in hold:
        for j in range(len(i)):
            if j == len(i)-1:
                f.write('%s' %i[j])
                continue
            f.write('%s,' %i[j])
        f.write('\n')

print("A csv file has been created for Clarity at: %s/accession_for_clarity%s.csv" % (os.getcwd(),datetime.now().strftime("%Y_%m_%d")))
