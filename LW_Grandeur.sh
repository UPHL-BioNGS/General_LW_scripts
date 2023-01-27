#!/bin/bash

USAGE="
Purpose:
Given a run name,
1) get the run id for the run
2) check if run is complete according to the basespace cli
2) download the sample sheet for that run
3) retrieve ids from each sample in the run
4) download fastq files
5) run grandeur

Usage:
LW_Grandeur.sh run_name

Version: 20230127
"

scriptdir=$(dirname $0)
configuration=("kelly" "uphl_ngs" "ica" "bioinfo")

echo -e "$USAGE"

if [ -z "$1" ]
then 
    echo "$(date): FATAL : run name is not specified"
    exit 1
else
    run=$1
    out=/Volumes/IDGenomics_NAS/pulsenet_and_arln/$run
fi

bs_user=""
bs_run_id=""
bs_complete=""

# checking if results for the run already exist
if [ -d "$out" ] 
then
    echo "$(date) : FATAL : Final analysis directory for $run already exists at $out"
    exit 1
fi

# getting the run id
while [ -z "$bs_run_id" ]
do
    for user in ${configuration[@]}
    do
        bs_run_status="$(bs list --config=$user runs | grep $run )"
        if [ -n "$bs_run_status" ]
        then
            bs_user=$user
            bs_run_id=$(echo $bs_run_status | awk '{print $4}' )
            echo "$(date): $run was sequenced under basespace user $bs_user with a run id of $bs_run_id"
            break
        fi 
    done

    if [ -z "$bs_run_id" ]
    then
        echo "$(date): $run was not found. Sleeping for 20 minutes."
        sleep 20m
    fi
done

# wait here until the run is complete
while [ -z "$bs_complete" ]
do
    bs_complete="$(bs list --config=$user runs | grep $bs_run_id | grep Complete | head -n 1)"

    if [ -z "$bs_complete" ]
    then
        echo "$(date): Sequencing not yet complete for $run. Sleeping 20 minutes."
        sleep 20m
    else
        echo "$(date): Sequencing is complete for $run."
    fi
done

# preping directory for analysis
mkdir -p $out/{reads,logs}
logdir = $out/logs

if [ ! -d "$out" ] ; then echo "Error: Could not make directory $out :(" ; exit 1 ; fi

# downloading the sample sheet
cd $out
echo "$(date) : Copying SampleSheet.csv to $out" | tee -a $logdir/basespace.log

bs run download \
    --config=$bs_user \
    --output="$out" \
    --id=$bs_run_id \
    --extension=csv \
    --log=$logdir/illumina.samplesheet.$bs_run_id.log

# downloading the reads
echo "$(date) : Copying fastq.gz files to $out/reads" | tee -a $logdir/illumina.fastq.log
echo "$(date) : Listing the dataset for --input-run of $run_id : "
bs list dataset --config=$bs_user --input-run=$bs_run_id | tee $logdir/illumina.list.log

sample_ids=($(bs list dataset --config=$bs_user --input-run=$bs_run_id | grep "illumina.fastq" | grep -v "Undetermined" | grep -v "Name" | grep -v "+" | awk '{ print $4 }' | sort | uniq ))
for sample in ${sample_ids[@]}
do
    (
    echo "$(date) : Downloading sample $sample from $run : $bs_run_id" | tee -a $logdir/illumina.fastq.log
    bs download dataset \
        --config=$bs_user \
        --id=$sample \
        --output="$out/reads" \
        --log=$logdir/illumina.$sample.log \
        --retry
        ) &
        [ $( jobs | wc -l ) -ge $( nproc ) ] && wait
    done
    wait
done
wait

echo "Download complete! Creating trace file confirming download!"
touch $out/download_complete.txt

echo "$(date) : Now starting Grandeur" | tee $logdir/grandeur.log
nextflow run UPHL-BioNGS/Grandeur \
    -profile uphl \
    -r 3.0.20230120 \
    --reads $out/reads \
    -with-tower \
    2>> $logdir/grandeur.err | tee -a $logdir/grandeur.log

echo "$(date) : Putting together the result files"
python3 $scriptdir/grandeur/results.py $out

echo "$(date) : Fin"
exit 0