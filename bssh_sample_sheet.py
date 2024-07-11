#!/usr/bin/env python3

"""
Author: Erin Young
Released: 2024-07-11
Version: 0.0.1
Description:
    This script isn't intended to be used alone, but it contains the functions
    for downloading a sample sheet from bssh.

EXAMPLE:
    python3 bssh_sample_sheet.py -r UT-M70330-240131 -o  /Volumes/IDGenomics_NAS/pulsenet_and_arln/UT-M70330-240131/reads
"""

import argparse
import logging
import subprocess

# local functions
from bssh_reads_by_run import get_run_id

# download the sample sheet used to generate reads from basespace
def download_sample_sheet(run_name, path):
    """
    Downloads the initial sample sheet for a sequencing run.

    Args:
        run_name (str): run name
        path (str): directory to download file to

    """

    idd = get_run_id(run_name)

    bashCommand = f"bs run download --config=bioinfo --output={path} --id={idd} --extension=csv"
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    logging.info(f"Sample sheet downloaded to {path}")


def main():
    """
    Downloads the initial sample sheet for a run.

    Args:
        args (argparse.Namespace): Parsed command-line arguments.

    """

    logging.basicConfig(level=logging.INFO) 

    parser = argparse.ArgumentParser(description="Description of your script")
    
    # Define your arguments here
    parser.add_argument("-r", "--run", type=str, required=True, help="Run name")
    parser.add_argument("-o", "--out", type=str, required=False, default="reads", help="Directory where sample sheet will be downloaded to")
    
    # Parse the arguments
    args = parser.parse_args()
    
    download_sample_sheet(args.run, args.out)


if __name__ == "__main__":
    main()
