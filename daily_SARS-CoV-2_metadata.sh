#!/bin/bash

USAGE="
Usage:
For creating the daily metadata file

bash daily_metadata_file.sh

Version: 2022-11-16
"

echo "$USAGE"

while [ -d "/Volumes/IDGenomics_NAS/" ]
do
  current_date=$(date +"%Y-%m-%d")
  echo "$(date) : the current date is $current_date"

  if [ ! -d "/Volumes/IDGenomics_NAS/COVID/daily_metadata/$current_date" ]
  then
    mkdir -p /Volumes/IDGenomics_NAS/COVID/daily_metadata/$current_date/logs
    err_file=/Volumes/IDGenomics_NAS/COVID/daily_metadata/$current_date/logs/err.txt
    log_file=/Volumes/IDGenomics_NAS/COVID/daily_metadata/$current_date/logs/log.txt
    echo "$(date) : It is a new day! Time to get some metadata together" 2>> $err_file | tee -a $log_file
    echo "$(date) : metadata will be in /Volumes/IDGenomics_NAS/COVID/daily_metadata/$current_date/dripping_rock" 2>> $err_file | tee -a $log_file

    # comparing runs to json files
    ls /Volumes/NGS/Analysis/covidseq/UT*/covidseq_complete.txt | rev | cut -f 2 -d "/" | rev | \
      parallel ls /Volumes/IDGenomics_NAS/COVID/daily_metadata/json/{}.json 2>&1 | \
      grep "No such" | awk '{print $4}' | cut -d "/" -f 7  | cut -f 1 -d "." | \
      parallel python /home/Bioinformatics/Dripping_Rock/bin/fasta_to_json.py {}

    # comparing automatically created json files with working json files
    jsons=($(ls /Volumes/IDGenomics_NAS/COVID/daily_metadata/json/UT*.json | grep -v "missing.json" | rev | cut -f 1 -d "/" | rev))
    for json in ${jsons[@]}
    do
      if [ ! -f "/Volumes/IDGenomics_NAS/COVID/daily_metadata/working_json/$json" ]
      then
        cp /Volumes/IDGenomics_NAS/COVID/daily_metadata/json/$json /Volumes/IDGenomics_NAS/COVID/daily_metadata/working_json/.
      fi
    done

    # starting Dripping Rock
    cd /Volumes/IDGenomics_NAS/COVID/daily_metadata/$current_date
    echo "$(date) : Running Dripping_Rock to get the metadata together" 2>> $err_file | tee -a $log_file
    nextflow run /home/Bioinformatics/Dripping_Rock -with-tower 2>> $err_file | tee -a $log_file
    echo "$(date) : The metadata file should be at /Volumes/IDGenomics_NAS/COVID/daily_metadata/$current_date/dripping_rock/UPHL_metadata.csv" 2>> $err_file | tee -a $log_file

    if [ "$(date +%u)" -eq "7" ]
    then
      echo "$(date) : It's Sunday, time to get a new tree" 2>> $err_file | tee -a $log_file
      nextflow run /home/Bioinformatics/Dripping_Rock -with-tower -resume --msa true
    fi

  fi

  # print a slight QC output that compares runs to the jsons
  covidseq_runs=($(ls /Volumes/NGS/Analysis/covidseq/UT*/covidseq_complete.txt | rev | cut -f 2 -d "/" | rev))
  for run in ${covidseq_runs[@]}
  do
    if [ ! -f "/Volumes/IDGenomics_NAS/COVID/daily_metadata/working_json/$run.json" ]
    then
      echo "$(date) : $run was not included in the metadata file"
    fi
  done

  echo "$(date) : sleeping 4 hours"
  sleep 4h
done

echo "$(date) : FATAL : Something happened and this needs to be restarted"
