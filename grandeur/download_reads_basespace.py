#!/usr/bin/env python3

'''
Author: Erin Young

Description:

This script will download fastq files and sample sheets for MiSeq runs

EXAMPLE:
python3 download_reads_basespace.py -o <directory to download to> -r <run name>
'''

# trying to keep dependencies really low
import argparse
import subprocess
import concurrent.futures
import os

version = '0.0.20230728'

parser = argparse.ArgumentParser()
parser.add_argument('-o', '--out', type=str, help='directory where files will get downloaded to', default='basespace')
parser.add_argument('-r', '--run', type=str, help='sequencing run', required = True )
parser.add_argument('-s', '--samplesheet', action='store_true', help ='flag that specifies to only download the sample sheet')
parser.add_argument('-u', '--upload',      action='store_true', help ='flag that specifies if reads should be uploaded to ICA')
parser.add_argument('-f', '--fastq',       action='store_true', help ='flag that specifies to only download the fastq files')
parser.add_argument('-t', '--threads', type=int, help='specifies number of threads to use', default=4)
parser.add_argument('-v', '--version', help='print version and exit', action='version', version='%(prog)s ' + version)
args   = parser.parse_args()

def download_fastq(id):
    subprocess.check_output(['bs', 'download', 'dataset', '--id=' + id, '--output=' + args.out, '--extension=fastq.gz', '--log=' + args.out + '/basespace.download_' + id+ '.log', '--retry']) 

# bs list run --filter-term=UT-M70330-230725 --filter-field=ExperimentName
bs_list_run = subprocess.check_output(['bs', 'list', 'runs', '--filter-term=' + args.run, '--filter-field=ExperimentName'], universal_newlines= True, text='str')

# getting the run id for the sequencing run
run_id = ''
if (bs_list_run):
    for line in bs_list_run.split('\n'):
        if args.run in line:
            split_line = line.split()
            if len(split_line) == 9:
                run_id = split_line[3]
                if not split_line[7] == 'Complete':
                    print('Sequencing run ' + args.run + ' with run id ' + run_id + 'has not finished sequencing. Exiting.')
                    exit()
                break
else:
    print("FATAL : No results on basespace for run " + args.run)
    exit()

if not run_id:
    print("FATAL : Coult not continue")
    exit()

# Creating the final directory
if not os.path.exists(args.out):
    os.mkdir(args.out)

# Getting the sample sheet
if not args.fastq:
    subprocess.check_output(['bs', 'run', 'download', '--output=' + args.out, '--id=' + run_id, '--extension=csv', '--log=' + args.out + '/download_sample_sheet.' + run_id + '.log']) 

# Getting the fastq files
if not args.samplesheet:
    bs_list_dataset = subprocess.check_output(['bs', 'list', 'dataset', '--input-run=' + run_id], universal_newlines= True, text='str')
    sample_ids = []
    for line in bs_list_dataset.split('\n'):
            split_line = line.split()
            if len(split_line) == 9 and not split_line[3] == 'Id':
                sample_ids.append(split_line[3])

    pool = concurrent.futures.ThreadPoolExecutor(max_workers=args.threads)
    for id in sample_ids:
            pool.submit(download_fastq,id)

    pool.shutdown(wait=True)

# uploading files to ICA
if args.upload and not args.samplesheet and not args.fastq:
    subprocess.check_output(['icav2', 'projects', 'enter', 'Produciton'])
    subprocess.check_output(['icav2', 'projectdata', 'upload', args.out, '/' + args.run + '/'])

print('Files are downloaded!')

