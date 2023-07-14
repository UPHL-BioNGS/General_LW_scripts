#!/bin/bash

##############################################
# written by Erin Young                      #
# for uploading samples to ICA for unicycler #
# updated : March 23, 2023                   #
##############################################

USAGE="""
To put the appropriate nanopore and illumina files
into ICA to run Unicycler on them. Requires a run
name which is used as the upload destination on ICA
as well as the sample_sheet that is used for 
Donut Falls (a csv file with columns for the id,
nanopore, and both fastq files for a paired run: 
sample,fastq,fastq_1,fastq_2)

The expected run time in ~2 hours  

# to download from github
Unicycler_ICA.sh run sample_sheet.csv
"""

echo $USAGE

run=$1
sample_sheet=$2

if [ -z "$run" ] || [ -z "$sample_sheet" ]; then echo "$(date): FATAL: Inputs are missing." ; echo $USAGE ; exit ; fi

if [ -z "$(which parallel)" ] ; then echo "$(date): FATAL: parallel is missing" ; exit 1; fi

mkdir -p nanopore_ica illumina_ica

echo "$(date): moving files for easy upload to ICA for $run"
cat $sample_sheet | grep -v fastq_1, | parallel --colsep "," "cp {2} nanopore_ica/{1}.fastq.gz ; cp {3} illumina_ica/{1}_R1.fastq.gz ; cp {4} illumina_ica/{1}_R2.fastq.gz"

echo "$(date): entering Testing project on ICA"
icav2 projects enter Testing || ( echo "$(date): FATAL : Could not enter Testing on ICA" ; exit 1)

echo "$(date): uploading nanopore reads for $run"
icav2 projectdata upload nanopore_ica /$run/ | tee -a nanopore_ica_upload.log
nanopore_upload_complete=0
test_nanopore_upload=$(tail -n 1 nanopore_ica_upload.log)
echo "$(date): determining if upload complete"
while [ "$nanopore_upload_complete" -eq 0 ]
do
    echo "$(date): Testing upload completeness with \"$test_nanopore_upload\""
    nanopore_upload_test=$(eval $test_nanopore_upload | grep "COMPLETED" )
    eval $test_nanopore_upload
    if [ -n "$nanopore_upload_test" ]
    then 
        nanopore_upload_complete=2
    else
        echo "$(date): upload not yet complete. Sleeping 1 min and trying again."
        sleep 1m
    fi
done
echo "$(date): uploading nanopore reads is complete for $run"

echo "$(date): uploading illumina reads for $run"
icav2 projectdata upload illumina_ica /$run/ | tee -a illumina_ica_upload.log
illumina_upload_complete=0
test_illumina_upload=$(tail -n 1 illumina_ica_upload.log)
echo "$(date): determining if upload complete"
while [ "$illumina_upload_complete" -eq 0 ]
do
    echo "$(date): Testing upload completeness with \"$test_illumina_upload\""
    eval $test_illumina_upload
    illumina_upload_test=$(eval $test_illumina_upload | grep "COMPLETED" )
    if [ -n "$illumina_upload_test" ]
    then 
        illumina_upload_complete=2
    else
        echo "$(date): upload not yet complete. Sleeping 1 min and trying again."
        sleep 1m
    fi
done
echo "$(date): uploading illumina reads is complete for $run"
wait

echo "$(date): starting Unicycler on ICA for each sample in $run"
for sample in $(cut -f 1 -d "," $sample_sheet )
do
    echo "$(date): Getting id for $sample"
    nanopore_id=$(icav2 projectdata list /$run/nanopore_ica/$sample.fastq.gz      | grep $sample | awk '{print $5}' )
    echo "$(date): Id for nanopore reads : $nanopore_id"
    illum_R1_id=$(icav2 projectdata list /$run/illumina_ica/${sample}_R1.fastq.gz | grep $sample | awk '{print $5}' )
    echo "$(date): Id for Illumina R1 reads : $illum_R1_id"
    illum_R2_id=$(icav2 projectdata list /$run/illumina_ica/${sample}_R2.fastq.gz | grep $sample | awk '{print $5}' )
    echo "$(date): Id for Illumina R2 reads : $illum_R2_id"
    if [ -n "$nanopore_id" ] && [ -n "$illum_R2_id" ] && [ -n "$illum_R2_id" ]
    then
        echo "$(date): Staring Unicycler on ICA for $sample"
        icav2 projectpipelines start nextflow Unicycler --input short_reads_1:$illum_R1_id --input short_reads_2:$illum_R2_id --input long_reads:$nanopore_id --user-reference ${run}-Unicycler-${sample}
    else
        echo "$(date): Unicycler could not start for $sample because one or more files were missing."
    fi
done

echo "$(date): Upload to ICA complete!"

