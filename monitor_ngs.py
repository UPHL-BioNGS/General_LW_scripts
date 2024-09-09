#!/usr/bin/env python3

"""
Author: Erin Young
Released: 2024-07-15
Version: 0.0.1

Description:
Checks if all GridIon runs in /Volumes/NGS/Output/GridION 
have been synced with /Volumes/BioNGS_1

EXAMPLE:
python3 monitor_ngs.py
"""

import logging 
import glob
import shutil
import os


def new_gridion():
    """
    Sync directories containing specific files from the source to the destination.

    This function searches for files matching the pattern 
    '/Volumes/NGS/Output/GridION/*/*/*/sequencing_summary*.txt'. It then extracts
    the run name for syncing.

    Returns:
    run (str): The run name used to construct the source and destination paths.
    """

    file_pattern = "/Volumes/NGS/Output/GridION/*/*/*/sequencing_summary*.txt"

    files = glob.glob(file_pattern)

    if not files:
        logging.warning("No new files found.")
        return
    
    for file in files:
        run = os.path.dirname(file).split('/')[5]
        if not os.path.exists(f"/Volumes/BioNGS_1/{run}"):
            logging.info(f"New run found!: {run}")
            return run


def sync_directories(run):
    """
    Sync directories containing specific files from the source to the destination.

    This function searches for files matching the pattern 
    '/Volumes/NGS/Output/GridION/{run}/*', excluding any files with "fail" in the 
    filename. It then syncs the directories containing these files to the 
    destination '/Volumes/BioNGS_1/{run}' if they haven't been synced already.

    Parameters:
    run (str): The run name used to construct the source and destination paths.

    Returns:
    None
    """
    source_pattern = f"/Volumes/NGS/Output/GridION/{run}/"
    destination_base = f"/Volumes/BioNGS_1/{run}"

    # Find files matching the pattern, exclude "fail"
    files = glob.glob(source_pattern)

    # Get the directories containing the matched files
    directories = {os.path.dirname(file) for file in files}

    for directory in directories:
        # Determine the corresponding destination directory
        relative_path = os.path.relpath(directory, f"/Volumes/NGS/Output/GridION/{run}")
        destination_dir = os.path.join(destination_base, relative_path)

        # Sync the directory if it hasn't been synced already
        if not os.path.exists(destination_dir):
            logging.info(f"Syncing {directory} to {destination_dir}")
            shutil.copytree(directory, destination_dir)
        else:
            logging.info(f"{destination_dir} already exists, skipping.")


def main():
    """
    Checks if run is finished and syncs to new destination.
    """

    logging.basicConfig(level=logging.INFO) 

    run = new_gridion()
    sync_directories(run)


if __name__ == "__main__":
    main()