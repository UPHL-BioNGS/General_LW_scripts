#!/usr/bin/env python3

'''
Author: Erin Young

Description:

This script will create two directories with the same name in 
dhhs-uphl-omics-inputs-dev and dhhs-uphl-omics-outputs-dev designated 
by '-a'. Then it will upload the files designated by '-f' and/or
everything in the directory designated by '-d'. 

If the directory already exists, this script is intended to fail unless
'-F' or '--force' is used.

EXAMPLE:
python3 aws_upload.py -a UT-M07101-240710 -d /Volumes/IDGenomics_NAS/pulsenet_and_arln/UT-M07101-240710/reads

python3 aws_upload.py -a UT-M07101-240710 -f /Volumes/IDGenomics_NAS/pulsenet_and_arln/UT-M07101-240710/reads/SampleSheet.csv

'''

# may need to configure with aws configure --profile 155221691104_dhhs-uphl-biongs-dev
import argparse
import os
import boto3
import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

def check_directory(bucket_name, directory_name, s3):
    """
    Checks if directory exists in S3 bucket.
    
    Args:
        bucket_name (str): Bucket name.
        directory_name (str): Directory name to check.
        s3 (session.client): AWS session.client('s3').
        
    Returns:
        boolean: True if directory exists, False otherwise.
    """
    try:
        response = s3.head_object(Bucket=bucket_name, Key=f'{directory_name}/')
        return True
    except:
        return False


def create_directory(bucket_name, directory_name, s3, force):
    """
    Creates directory in S3 bucket if it doesn't already exist.
    
    Args:
        bucket_name (str): Bucket name.
        directory_name (str): Directory name to create.
        s3 (session.client): AWS session.client('s3').
        force (bool): Whether to force creation if directory already exists.
    """
    if check_directory(bucket_name, directory_name, s3):
        logging.warning(f'Directory {directory_name} already exists in {bucket_name}!')

        if not force:
            logging.fatal(f'Use \'--force\' to upload to directory anyway.')
            sys.exit(1)
        else:
            return

    else:
        try:
            s3.put_object(Bucket=bucket_name, Key=f'{directory_name}/')
            logging.info(f'Directory {directory_name} created in bucket {bucket_name}')
        except Exception as e:
            logging.error(f'Error creating directory {directory_name} in bucket {bucket_name}: {e}')
            sys.exit(1)


def upload_dir(bucket_name, s3_directory, local_directory, s3):
    """
    Uploads entire directory to S3.
    
    Args:
        bucket_name (str): Bucket name.
        s3_directory (str): Directory path in S3.
        local_directory (str): Local directory path.
        s3 (session.client): AWS session.client('s3').
    """
    logging.info(f'Uploading everything in {local_directory} to {s3_directory}')
    
    # Ensure the directory name ends with a '/'
    if not s3_directory.endswith('/'):
        s3_directory += '/'

    # Create a list to hold the files to be uploaded
    files_to_upload = []

    # Walk through the local directory to collect file paths
    for root, dirs, files in os.walk(local_directory):
        for file in files:
            local_path = os.path.join(root, file)
            relative_path = os.path.relpath(local_path, local_directory)
            s3_path = os.path.join(s3_directory, relative_path)
            files_to_upload.append((s3_path, local_path))

    # Upload files in parallel
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(upload_file_from_dir, s3, bucket_name, s3_path, local_path) for s3_path, local_path in files_to_upload]
        for future in as_completed(futures):
            local_path, success = future.result()
            if success:
                logging.info(f'Successfully uploaded {local_path}')
            else:
                logging.error(f'Failed to upload {local_path}')


def upload_file(s3, bucket_name, s3_directory, local_file):
    """
    Uploads files to base of directory in bucket.
    
    Args:
        s3 (session.client): AWS session.client('s3').
        bucket_name (str): Bucket name.
        s3_path (str): Directory path in S3.
        local_path (str): Local file path.
    """

    try:
        s3_path = os.path.join(s3_directory, os.path.basename(local_file))
        s3.upload_file(local_file, bucket_name, s3_path)
        logging.info(f'Uploaded {local_file} to s3://{bucket_name}/{s3_path}')
        return local_file, True
    except Exception as e:
        logging.error(f'Error uploading {local_file}: {e}')
        return local_file, False


def upload_file_from_dir(s3, bucket_name, s3_path, local_path):
    """
    Uploads files to directory in bucket.
    
    Args:
        s3 (session.client): AWS session.client('s3').
        bucket_name (str): Bucket name.
        s3_path (str): Directory path in S3.
        local_path (str): Local file path.
    """
    logging.info(f'Uploading {local_path} to {s3_path}')
    try:
        s3.upload_file(local_path, bucket_name, s3_path)
        logging.info(f'Uploaded {local_path} to s3://{bucket_name}/{s3_path}')
        return local_path, True
    except Exception as e:
        logging.error(f'Error uploading {local_path} to s3://{bucket_name}/{s3_path}: {e}')
        return local_path, False


def upload_files(bucket_name, s3_directory, files, s3):
    """
    Uploads specified files to S3 directory.
    
    Args:
        bucket_name (str): Bucket name.
        s3_directory (str): Directory path in S3.
        files (list): List of file paths to upload.
        s3 (session.client): AWS session.client('s3').
    """
    logging.info(f'Uploading file(s) {files} to {s3_directory}')
    
    # Ensure the directory name ends with a '/'
    if not s3_directory.endswith('/'):
        s3_directory += '/'

    # Upload files in parallel
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(upload_file, s3, bucket_name, s3_directory, file) for file in files]
        for future in as_completed(futures):
            file, success = future.result()
            if success:
                logging.info(f'Successfully uploaded {file}')
            else:
                logging.warning(f'Failed to upload {file}')


def main():
    """
    Main function to handle command line arguments and execute script.
    """
    logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%y-%b-%d %H:%M:%S', level=logging.INFO)

    version = '0.1.0'

    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--awsdir', type=str, help='Directory in AWS S3 to create/upload to', required=True)
    parser.add_argument('-d', '--dir', type=str, help='Local directory with files to upload', required=False)
    parser.add_argument('-f', '--file', type=str, nargs='+', help='File(s) to upload', required=False)
    parser.add_argument('-v', '--version', help='Print version and exit', action='version', version='%(prog)s ' + version)
    parser.add_argument('-b', '--input_bucket', type=str, help='Name of S3 input bucket', default='dhhs-uphl-omics-inputs-dev', required=False)
    parser.add_argument('-B', '--output_bucket', type=str, help='Name of S3 output bucket', default='dhhs-uphl-omics-outputs-dev', required=False)
    parser.add_argument('-F', '--force', action='store_true', help='Force upload to bucket that already exists', required=False)
    parser.add_argument('-r', '--region', type=str, help='AWS bucket region', default='us-west-2', required=False)
    parser.add_argument('-p', '--profile', type=str, help='AWS credential profile', default='155221691104_dhhs-uphl-biongs-dev', required=False)

    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    s3 = session.client('s3')

    # Create directories for workflows
    create_directory(args.input_bucket, args.awsdir, s3, args.force)
    create_directory(args.output_bucket, args.awsdir, s3, args.force)

    # Upload files
    if args.file and len(args.file) > 0:
        upload_files(args.input_bucket, args.awsdir, args.file, s3)

    # Upload contents of directory
    if args.dir:
        if os.path.isdir(args.dir):
            upload_dir(args.input_bucket, args.awsdir, args.dir, s3)
        else:
            logging.fatal(f'{args.dir} does not exist!')
            sys.exit(1)


if __name__ == '__main__':
    main()