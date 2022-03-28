#!/bin/bash

USAGE="
Purpose:
1) finds new completed runs from basespace cli:
\tbs list runs | grep {instrument} | grep \"Complete\"
2) downloads the sample sheet for that run
\tbs run download --output={run}/Sequencing_reads --id={run_id} --extension=csv
3) retrieves ids from each sample in the run
\tbs list dataset --input-run={run_id} --terse
4) downloads the fastq files
\tbs download dataset -i {biosample_id} -o {run}/Sequencing_reads/Raw
5) run grandeur

Usage:
new_runs_basespace_cli.sh

Version: 20220325
"

scriptdir=$(dirname $0)
configuration=("kelly" "uphl_ngs" "ica" "bioinfo")

date
echo -e "$USAGE"

while [ -d "/Volumes/IDGenomics_NAS/WGS_Serotyping" ]
do
  for user in ${configuration[@]}
  do
    echo "$(date) : Current completed MiSeq runs and user $user"
    bs list --config=$user runs | grep -e M07101 -e M70330 -e M03999 | grep "Complete"
    bs_runs=($(bs list --config=$user runs | grep -e M07101 -e M70330 -e M03999 | grep "Complete" | awk '{ print $4 ":" $6 }' ))
    for run in ${bs_runs[@]}
    do
      run_id=$(echo $run | cut -f 1 -d ":")
      run_name=$(echo $run | cut -f 2 -d ":")
      if [ ! -d "/Volumes/IDGenomics_NAS/WGS_Serotyping/$run_name" ]
      then
        echo "$(date) : New sequencing run has completed : $run_name"
        mkdir -p /Volumes/IDGenomics_NAS/WGS_Serotyping/$run_name/{logs,Sequencing_reads/Raw}
        log_dir=/Volumes/IDGenomics_NAS/WGS_Serotyping/$run_name/logs

        if [ ! -d "/Volumes/IDGenomics_NAS/WGS_Serotyping/$run_name" ] ; then echo "Error: Could not make directory /Volumes/IDGenomics_NAS/WGS_Serotyping/$run_name :(" ; exit 1 ; fi

        basespace_log=$log_dir/basespace_cli
        grandeur_log=$log_dir/grandeur

        cd /Volumes/IDGenomics_NAS/WGS_Serotyping/$run_name
        echo "$(date) : Copying SampleSheet.csv to /Volumes/IDGenomics_NAS/WGS_Serotyping/$run_name/Sequencing_reads" | tee -a $basespace_log.log
        bs run download --config=$user \
          --output="/Volumes/IDGenomics_NAS/WGS_Serotyping/$run_name/Sequencing_reads" \
          --id=$run_id \
          --extension=csv \
          --log=$basespace_log.$run_id.log

        echo "$(date) : Copying fastq.gz files to /Volumes/IDGenomics_NAS/WGS_Serotyping/$run_name/Sequencing_reads/Raw" | tee -a $basespace_log.log
        echo "$(date) : Listing the dataset for --input-run of $run_id : "
        bs list dataset --config=$user --input-run=$run_id | tee $basespace_log.list
        sample_ids=($(bs list dataset --config=$user --input-run=$run_id | grep "illumina.fastq" | grep -v "Undetermined" | grep -v "Name" | grep -v "+" | awk '{ print $4 }' | sort | uniq ))
        for sample in ${sample_ids[@]}
        do
          (
          echo "$(date) : Downloading sample $sample from $run_name : $run_id" | tee -a $basespace_log.log
          bs download dataset \
            --config=$user \
            --id=$sample \
            --output="/Volumes/IDGenomics_NAS/WGS_Serotyping/$run_name/Sequencing_reads/Raw" \
            --log=$basespace_log.$sample.log \
            --retry
          ) &
          [ $( jobs | wc -l ) -ge $( nproc ) ] && wait
        done
        wait

        echo "$(date) : Now starting Grandeur" | tee -a $grandeur_log.log
        cd /Volumes/IDGenomics_NAS/WGS_Serotyping/$run_name
        nextflow run UPHL-BioNGS/Grandeur \
          -profile uphl \
          --reads /Volumes/IDGenomics_NAS/WGS_Serotyping/$run_name/Sequencing_reads/Raw \
          -r main \
          -with-tower \
          2>> $grandeur_log.err | tee -a $grandeur_log.log

        nextflow run UPHL-BioNGS/Grandeur \
          -profile uphl \
          --reads /Volumes/IDGenomics_NAS/WGS_Serotyping/$run_name/Sequencing_reads/Raw \
          -r main \
          -resume \
          --shigatyper true \
          2>> $grandeur_log.err | tee -a $grandeur_log.log
      fi
    done
  done
  echo "$(date) : Sleeping for 20 minutes"
  sleep 20m
done

echo "$(date) : Something happened and the loop ended! :("
