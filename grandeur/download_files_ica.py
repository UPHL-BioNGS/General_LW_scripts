#!/usr/bin/env python3

'''
Author: Erin Young

Description:

This script will download the results from ica

EXAMPLE:
python3 download_files_ica.py -o <directory to download to> -r <run name>
'''

# trying to keep dependencies really low
import argparse
import subprocess
import concurrent.futures
import os

version = '0.0.20230925'

parser = argparse.ArgumentParser()
parser.add_argument('-o', '--out', type=str, help='directory where files will get downloaded to', default='ica')
parser.add_argument('-r', '--run', type=str, help='sequencing run', required = True )
parser.add_argument('-v', '--version', help='print version and exit', action='version', version='%(prog)s ' + version)
args   = parser.parse_args()


# getting id 
# icav2 projectdata list --file-name UT-M03999-230830 --match-mode FUZZY --parent-folder /
ica_lines = subprocess.check_output(['icav2', 'projectdata', 'list', '--file-name', args.run + '_Gran', '--match-mode', 'FUZZY', '--parent-folder', '/'], universal_newlines= True, text='str')
for line in ica_lines.split('\n'):
    if 'AVAILABLE' in line:
        folder_id=line.split("\t")[3]


print("The folder id is " + folder_id)


# downloading the folder
# icav2 projectdata download fol.bfc81abb416c437ee3cf08dbaac3cd7c /Volumes/IDGenomics_NAS/pulsenet_and_arln/UT-M03999-230830
subprocess.check_output(['icav2', 'projectdata', 'download', folder_id, args.out],universal_newlines= True, text='str')

