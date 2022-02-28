#!/bin/bash

USAGE="
Usage:
For creating the daily metadata file

bash daily_metadata_file.sh

Version: 2022-02-28
"

echo "$USAGE"

while [ -d "/Volumes/IDGenomics_NAS/NextStrain" ]
do
  current_date=$(date +"%Y-%m-%d")
  echo "$(date) : the current date is $current_date"

  if [ ! -d "/Volumes/IDGenomics_NAS/NextStrain/$current_date" ]
  then

    # copy over jsons that haven't been copied over : ls /Volumes/IDGenomics_NAS/NextStrain/jsons/UT*json | grep -v "missing" | rev | cut -f 1 -d "/" | rev | cut -f 1 -d "." | parallel ls /Volumes/IDGenomics_NAS/NextStrain/working_json/{}.json
    mkdir -p /Volumes/IDGenomics_NAS/NextStrain/$current_date/logs
    err_file=/Volumes/IDGenomics_NAS/NextStrain/$current_date/logs/err.txt
    log_file=/Volumes/IDGenomics_NAS/NextStrain/$current_date/logs/log.txt
    echo "$(date) : It is a new day! Time to get some metadata together" 2>> $err_file | tee -a $log_file
    echo "$(date) : metadata will be in /Volumes/IDGenomics_NAS/NextStrain/$current_date" 2>> $err_file | tee -a $log_file

    ls /Volumes/NGS/Analysis/covidseq/UT* -d | rev | cut -f 1 -d "/" | rev | parallel ls /Volumes/IDGenomics_NAS/NextStrain/jsons/{}.json 2>&1 | grep "No such" | awk '{print $4}' | cut -d "/" -f 6  | cut -f 1 -d "." | parallel /home/Bioinformatics/Dripping_Rock/metadata/fasta_to_json.py {}
    jsons=($(ls /Volumes/IDGenomics_NAS/NextStrain/jsons/UT*.json | grep -v "missing.json" | rev | cut -f 1 -d "/" | rev))
    for json in ${jsons[@]}
    do
      if [ ! -f "/Volumes/IDGenomics_NAS/NextStrain/working_json/$json" ]
      then
        cp /Volumes/IDGenomics_NAS/NextStrain/jsons/$json /Volumes/IDGenomics_NAS/NextStrain/working_json/.
      fi
    done

    cd /Volumes/IDGenomics_NAS/NextStrain/$current_date
    echo "$(date) : Running Dripping_Rock to get the metadata together" 2>> $err_file | tee -a $log_file
    nextflow /home/Bioinformatics/Dripping_Rock/metadata/nextstrain_metadata.nf -with-tower 2>> $err_file | tee -a $log_file
    echo "$(date) : The metadata file should be at /Volumes/IDGenomics_NAS/NextStrain/$current_date/Dripping_Rock/UPHL_metadata.csv" 2>> $err_file | tee -a $log_file

    if [ "$(date +%u)" -eq "7" ]
    then
      echo "$(date) : It's Sunday, time to get a new tree" 2>> $err_file | tee -a $log_file
      nextflow /home/Bioinformatics/Dripping_Rock/metadata/nextstrain_metadata.nf -with-tower -resume --msa true
    fi

  fi

  covidseq_runs=($(ls /Volumes/NGS/Analysis/covidseq/UT-* -d | grep -v " " | rev | cut -f 1 -d "/" | rev))
  for run in ${covidseq_runs[@]}
  do
    if [ ! -f "/Volumes/IDGenomics_NAS/NextStrain/working_json/$run.json" ]
    then
      echo "$(date) : $run cannot be included in the metadata file"
    fi
  done

  echo "$(date) : sleeping 4 hours"
  sleep 4h
done

echo "$(date) : FATAL : Something happened and this needs to be restarted"
