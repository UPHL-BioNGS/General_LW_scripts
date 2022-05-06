#!/bin/bash

USAGE="
This script was written to automate uploading completed runs on basespace to ICA.
Currently MiSeq_runs_basespace.sh downloads runs locally, this script takes those
files and uploads them to ICA.

It is disigned to work on a screen on the linux workstaion, and kicks off when it
finds a download_comlete.txt file created by MiSeq_runs_basespace.sh.

icav2 must be already installed and configured.

Usage:
upload_BS_to_ICA.sh

Version:
20220506

"

while [ -d "/Volumes/IDGenomics_NAS/WGS_Serotyping" ]
do
  if [[ -n $(find /Volumes/IDGenomics_NAS/WGS_Serotyping -maxdepth 2 -name download_complete.txt) ]]
  then
    echo "Found new run downloaded! Starting Upload to ICA!"
    CHANGE=$(find /Volumes/IDGenomics_NAS/WGS_Serotyping -maxdepth 2 -name download_complete.txt)
    NEW=$(echo $CHANGE | cut -d/ -f-5)
    NEW="$NEW/Sequencing_reads/Raw"
    ICA_PATH=$(echo $CHANGE | cut -d/ -f5)
    ICA_PATH="/$ICA_PATH/"
    icav2 projects enter Testing
    icav2 projectdata upload $NEW $ICA_PATH
    wait
    echo "Uploaded to ICA!"
    COMPLETED=$(echo $CHANGE | cut -d/ -f-5)
    COMPLETED="$COMPLETED/upload_complete.txt"
    mv $CHANGE $COMPLETED

  fi
  echo " Nothing to upload to ICA. Sleeping for 20 minutes"
  sleep 20m
done

echo " $(date): Loop Broken Restart!"
