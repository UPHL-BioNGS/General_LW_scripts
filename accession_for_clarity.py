#!/usr/bin/env python3

# Written in Python 3.11.2. Tested on Python 3.7.11,3.8.8, 3.9.13, 3.10.8

# Packages Needed pandas, openpyxl, xlrd
# Install with: pip3 install pandas openpyxl xlrd

import pandas as pd
import os
import sys
import numpy as np
import glob
import re
from datetime import datetime, timedelta


import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=UserWarning)
### USAGE ### python accession_for_clarity.py "path/to/files/fromclarity" "path/to/files/fromclarity.etc"
# Must be log into or mount these servers smb://172.16.109.9 smb://168.180.220.43. Must include files, project samplesheets, from Clarity for all COVIDSEQ projects
# DO NOT MAKE DUPLICATES IN CLARITY!!! PLEASE READ README.md and proceed with caution. 

path_to_project_lists=[]
for i in range(len(sys.argv)-1):
    path_to_project_lists.append(str(sys.argv[i+1]))

atog=[]
for i in ['A','B','C','D','E','F','G','H']:

     for j in range(12):
        atog.append('%s%s' % (i,(j+1)))

# Import All_ncovid*.csv
#ip address smb://172.16.109.9 smb://168.180.220.43
ncovid=pd.read_csv('/Volumes/LABWARE/Shared_Files/Mirth/COVID_data_import/ncovOverview.csv',usecols=['submitterId','sampleNumber','collectionDate','receivedDate','result','customer'], encoding = "ISO-8859-1", low_memory=False)
# Import NGS_Covid_*.csv
NGS_Covid=pd.read_csv('/Volumes/LABWARE/Shared_Files/Mirth/COVID_data_import/NGS_Covidtest.csv',usecols=['observations','customer','submitterId','sampleNumber','collectionDate','receivedDate','PlateName','PlateWell'], encoding = "ISO-8859-1", low_memory=False)
NGS_Covid['receivedDate']=NGS_Covid['receivedDate'].fillna(NGS_Covid['collectionDate'])
# Clean up
end = datetime.now().date()
plot_end=end
plot_start=end-timedelta(days=30)
NGS_Covid['receivedDate']= pd.to_datetime(NGS_Covid['receivedDate']).dt.date
NGS_Covid=NGS_Covid[(NGS_Covid['receivedDate'] > plot_start) & (NGS_Covid['receivedDate'] < plot_end)]
NGS_Covid=NGS_Covid.drop(columns=['receivedDate'])

# kfs by workbooks
#ip address smb://172.16.109.9 smb://168.180.220.43
list_of_files = glob.glob('/Volumes/DDCP/UPHL/MICRO/MOLECULAR LABORATORY/TESTING/2019-nCoV/ThermoFisher Kit/Worksheets/Completed Worksheets/*')
these=[]
date_regex = r"^\d{4}-\d{2}-\d{2}_.*\.xlsx?$"
for i in list_of_files:
    if re.match(date_regex, i.split('/')[-1]):
        try:
            if datetime.strptime(i.split('/')[-1][0:10], '%Y-%m-%d') > (datetime.today()-timedelta(days=30)):
                these.append(i)
        except:
            print('\n \n \n Looks like you are not connected to /DDCP/UPHL/!!! \n \n \n \n Please connect to smb://172.16.109.9 smb://168.180.220.43 \n \n \n \n OR You do not have the imported moduels install for the version of python you are using. See line 6. \n\n\n\n\n\n')
            continue
dels=[]
for i in range(len(these)):
    if these[i].split('/')[-1][0:15][-1] == 'R':
        for j in range(len(these)):
            if these[i].split('/')[-1][0:14] == these[j].split('/')[-1][0:14]:
                if len(these[i].split('/')[-1]) > len(these[j].split('/')[-1]):
                    dels.append(j)
dels=list(set(dels))

dels.sort(reverse=True)



for i in dels:
    del these[i]
positives=[]
for k in these:
    try:
        kf_plate=pd.read_excel(k,sheet_name='Export File', skiprows=9)
    except:
        print('\n \n \n Looks like you are not connected to /DDCP/UPHL/!!! \n \n \n \n Please connect to smb://172.16.109.9 smb://168.180.220.43 \n \n \n \n OR You do not have the imported moduels install for the version of python you are using. See line 6. \n\n\n\n\n\n')
        continue
    kf_samples=[]
    for i,j in kf_plate.iterrows():
        if type(j['Sample Name']) == int:
            kf_samples.append([j['Sample Name'],atog[j['Well']-1]])
    pos=[]
    for i in kf_samples:
        tmp=ncovid[ncovid['sampleNumber']==i[0]]
        if len(tmp) == 0:
            print("STOP SAMPLES NOT IN NCOV FILE")
            break
        if tmp['result'].values[0] == 'Positive for SARS-CoV-2' or tmp['result'].values[0] == 'SARS-COV-2 Detected' :
            i.append(tmp['collectionDate'].values[0])
            i.append(k.split('/')[-1][0:-5])
            positives.append(i)
kfs = pd.DataFrame(positives, columns=['Sample Name','Well','collectionDate','Batch ID'])

#kfs for comboflu
list_of_files = glob.glob('/Volumes/DDCP/UPHL/MICRO/MOLECULAR LABORATORY/TESTING/2019-nCoV/FluAFluBCOVID/Worksheets/*')
these=[]
date_regex = r"^\d{4}-\d{2}-\d{2}_.*\.xlsx?$"
for i in list_of_files:
    if re.match(date_regex, i.split('/')[-1]):
        try:
            if datetime.strptime(i.split('/')[-1][0:10], '%Y-%m-%d') > (datetime.today()-timedelta(days=30)):
                these.append(i)
        except:
            print('\n \n \n Looks like you are not connected to /DDCP/UPHL/!!! \n \n \n \n Please connect to smb://172.16.109.9 smb://168.180.220.43 \n \n \n \n OR You do not have the imported moduels install for the version of python you are using. See line 6. \n\n\n\n\n\n')
            continue
dels=[]
for i in range(len(these)):
     if these[i].split('/')[-1][0:15][-1] == 'R':
         for j in range(len(these)):
             if these[i].split('/')[-1][0:14] == these[j].split('/')[-1][0:14]:
                 if len(these[i].split('/')[-1]) > len(these[j].split('/')[-1]):
                     dels.append(j)
dels=list(set(dels))

dels.sort(reverse=True)

for i in dels:
    del these[i]
positives=[]
for k in these:
 try:
         kf_plate=pd.read_excel(k,sheet_name='Export File', skiprows=9)
 except:
        print('\n \n \n Looks like you are not connected to /DDCP/UPHL/!!! \n \n \n \n Please connect to smb://172.16.109.9 smb://168.180.220.43 \n \n \n \n OR You do not have the imported moduels install for the version of python you are using. See line 6. \n\n\n\n\n\n')
        continue
 kf_samples=[]
 for i,j in kf_plate.iterrows():
         if type(j['Sample Name']) == int:
             kf_samples.append([j['Sample Name'],atog[j['Well']-1]])
pos=[]

for i in kf_samples:
    tmp=ncovid[ncovid['sampleNumber']==i[0]]
    if len(tmp) == 0:
       print("STOP SAMPLES NOT IN NCOV FILE")
       break
    if tmp['result'].values[0] == 'Detected' :
        i.append(tmp['collectionDate'].values[0])
        i.append(k.split('/')[-1][0:-5])
        positives.append(i)
kfs2 = pd.DataFrame(positives, columns=['Sample Name','Well','collectionDate','Batch ID'])


#Get Panther Tubes
end = datetime.now().date()
plot_end=end
plot_start=end-timedelta(days=30)
ncovid['receivedDate']= pd.to_datetime(ncovid['receivedDate'], errors='coerce').dt.date
panther=ncovid[(ncovid['receivedDate'] > plot_start) & (ncovid['receivedDate'] < plot_end)]
panther=panther.drop(columns=['receivedDate'])
ppanther = panther[panther['result']== 'SARS-COV-2 Detected']

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

# Merge kfs in clarity
tmp = kfs.rename(columns={'Sample Name':'Sample/Name','Well':'Sample/Well Location',
                      'Batch ID':'Container/Name','collectionDate':'UDF/Sample Collection DateTime'})

# Merge kfs2 in clarity
tmp = kfs2.rename(columns={'Sample Name':'Sample/Name','Well':'Sample/Well Location',
                          'Batch ID':'Container/Name','collectionDate':'UDF/Sample Collection DateTime'})
tmp['UDF/Provider Code'] = 'UPHL'
clarity = clarity.append(tmp, ignore_index=True)
    
#tmp = tmp.drop(columns= ['ORF1ab Ct','N gene Ct','S gene Ct'])
tmp['UDF/Provider Code'] = 'UPHL'
clarity = clarity.append(tmp, ignore_index=True)

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
        in_c=in_c.append(in_c_tmp, ignore_index=True)
    i=+ 1 

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
