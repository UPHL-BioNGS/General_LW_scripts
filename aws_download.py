#!/usr/bin/env python3

'''
Author: Erin Young

Description:

This script will download all files from an AWS bucket to a
designated directory. 

EXAMPLE:
python3 aws_download.py -a UT-M07101-240710 -d /Volumes/IDGenomics_NAS/pulsenet_and_arln/UT-M07101-240710/aws_results

'''

import boto3
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse

def download_file(s3_resource, bucket_name, s3_key, local_directory):
    """
    Downloads a single file from S3 to a local directory.

    Args:
        s3_resource (boto3.resource('s3')): Boto3 S3 resource.
        bucket_name (str): Name of the S3 bucket.
        s3_key (str): Key of the file in S3.
        local_directory (str): Local directory path where the file will be saved.
    """
    local_path = os.path.join(local_directory, os.path.basename(s3_key))
    try:
        s3_resource.Bucket(bucket_name).download_file(s3_key, local_path)
        print(f'Downloaded {s3_key} to {local_path}')
        return s3_key, True
    except Exception as e:
        print(f'Error downloading {s3_key}: {e}')
        return s3_key, False


def download_directory(bucket_name, s3_directory, local_directory, profile_name, region_name):
    """
    Downloads all files from a directory in an S3 bucket to a local directory in parallel.

    Args:
        bucket_name (str): Name of the S3 bucket.
        s3_directory (str): Directory in the S3 bucket to download from.
        local_directory (str): Local directory path where files will be saved.
        profile_name (str): AWS profile name configured in your AWS credentials.
        region_name (str): AWS region where the S3 bucket is located.
    """
    # Create a session using the specified profile and region
    session = boto3.Session(profile_name=profile_name, region_name=region_name)
    s3_resource = session.resource('s3')

    # Ensure the local directory exists
    os.makedirs(local_directory, exist_ok=True)

    # List all objects in the S3 directory
    bucket = s3_resource.Bucket(bucket_name)
    objects = bucket.objects.filter(Prefix=s3_directory)

    # Download files in parallel
    with ThreadPoolExecutor() as executor:
        futures = []
        for obj in objects:
            if obj.key == s3_directory:  # Skip the directory itself
                continue
            futures.append(executor.submit(download_file, s3_resource, bucket_name, obj.key, local_directory))

        # Process completed futures
        for future in as_completed(futures):
            s3_key, success = future.result()
            if success:
                print(f'Successfully downloaded {s3_key}')
            else:
                print(f'Failed to download {s3_key}')


def main():
    parser = argparse.ArgumentParser(description='Download files from S3 bucket directory.')
    parser.add_argument('-b', '--bucket', help='Name of the S3 bucket', default='dhhs-uphl-omics-outputs-dev', required=False)
    parser.add_argument('-a', '--awsdir', help='Directory in the S3 bucket to download from', required=True)
    parser.add_argument('-d', '--dir', help='Local directory path where files will be saved', required=True)
    parser.add_argument('-r', '--region', type=str, help='AWS bucket region', default='us-west-2', required=False)
    parser.add_argument('-p', '--profile', type=str, help='AWS credential profile', default='155221691104_dhhs-uphl-biongs-dev', required=False)
    args = parser.parse_args()

    download_directory(args.bucket, args.awsdir, args.dir, args.profile, args.region)


if __name__ == '__main__':
    main()
