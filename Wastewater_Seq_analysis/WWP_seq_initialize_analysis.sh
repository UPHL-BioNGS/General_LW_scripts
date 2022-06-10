#!/bin/bash
# if any errors, then exit
set -e

###########################
# Purpose: Bash script to setup and initiate Wastewater sequencing run analysis
# Author: Pooja Gupta
# Usage: sh WWP_seq_initialize_analysis.sh <run_name> | tee -a WWP_seq_initialize_analysis_log.txt
# Last updated on 9 June,2022
###########################

run_name=$1
log_files=/Volumes/NGS/Analysis/covidseq/$run_name/covidseq_output/Logs_Intermediates

if [ -d "$log_files/VirusDetection" ]
then
    echo "$(date) : Fastq generation step is completed for run $run_name."
    sample_sheet=$(ls $log_files/SampleSheetValidation/SampleSheet_Intermediate.csv | head -n 1)
        if [ -n "$sample_sheet" ] && [ -d "$log_files/VirusDetection" ]
        then
            echo "$(date) : The sample sheet for run $run_name is $sample_sheet"
            if grep -n -q -i 'Wastewater' $sample_sheet
            then
                echo "$(date) : Some wastewater samples found in $run_name"
                analysis_dir='/Volumes/IDGenomics_NAS/wastewater_sequencing'
                echo "$(date) : Analysis directory is $analysis_dir."
                if [ ! -d "$analysis_dir/$run_name" ]
                then
                    echo "$(date) : $run_name run folder was not found in the $analysis_dir"
                    echo "$(date) : Creating $run_name run folder and sub directories for storing raw fastq files and other downstream analysis"
                    mkdir -p $analysis_dir/$run_name/{raw_data,ncbi_submission,fasta,analysis,failed_samples,results}
                    echo "$(date) : Raw fastq files will be stored in $analysis_dir/$run_name/raw_data"
                    echo "$(date) : Fasta files will be stored in $analysis_dir/$run_name/fasta"
                    echo "$(date) : Bioinformatics analysis will be stored in $analysis_dir/$run_name/analysis"
                    echo "$(date) : Generating list of wastewater samples from the run sample sheet as a csv output. Used to fetch matching fastq files in the next step."
                    grep -n -i 'Wastewater' $sample_sheet | cut -f 2 -d ',' > $analysis_dir/$run_name/${run_name}_wastewater_sample_list.csv
                    fastq_dir=$log_files/FastqGeneration
                    echo "$(date) : Copying fastq files from $fastq_dir to wastewater sequencing analysis directory to run with viralrecon or Cecret"

                    find $fastq_dir -type f -name '*.fastq.gz' -print0 | grep -zf $analysis_dir/$run_name/${run_name}_wastewater_sample_list.csv | xargs -r0 cp -t $analysis_dir/$run_name/raw_data
                    echo "$(date) : Fastq files copied successfully"

                    echo "$(date) : Cleaning up fastq filenames"
                    ww_fastq=$analysis_dir/$run_name/raw_data

                    for file in "$ww_fastq"/*_R1_001.fastq.gz; do
                    mv "$file" "${file/_S*/_R1_001.fastq.gz}"
                    echo "$(date) : Fastq filenames have been cleaned"
                    done

                    for newfile in "$ww_fastq"/*_R1_001.fastq.gz; do
                    filename=$(basename "$newfile" _R1_001.fastq.gz)
                    echo $filename
                    new_name="${filename%-A01290*}_R1.fastq.gz"
                    echo $new_name
                    sample_id=$(basename "$new_name" _R1.fastq.gz)
                    echo $sample_id
                    echo "$(date) : Copying $newfile from fastq to submission directory as $new_name"
                    cp "$newfile" "$analysis_dir/$run_name/ncbi_submission/$new_name"

                    echo "$(date) : Generating ncbi submission ID and associated fastq file names"
                    echo "sample_name,filename" > ${analysis_dir}/${run_name}/${run_name}_ncbi_submission_info.csv
                    echo "${sample_id},${new_name}" >> ${analysis_dir}/${run_name}/${run_name}_ncbi_submission_info.csv
                    #var=$(paste -d, <(echo "$sample_id") <(echo "$new_name"))
                    #echo "$var" >> ${dir2}/output.csv
                    #
                    #sed '1i sample_name,filename' ncbi_submission_info.csv >> ncbi_submission_info.csv
                    done

                    #Samples that fail after the run are excluded from downstream analysis. This step is nececssary for running samples with viralrecon otherwise oftentimes, the pipeline fails
                    echo "$(date) : Moving failed samples from raw_data directory to another directory based on file size < 2MB"
                    cd /Volumes/IDGenomics_NAS/wastewater_sequencing/$run_name/raw_data/
                    find $ww_fastq -name "*_R1_001.fastq.gz" -type f -size -2M -exec mv "{}" $analysis_dir/$run_name/failed_samples/ \; 
                    find $ww_fastq -name "*_R2_001.fastq.gz" -type f -size -2M -exec mv "{}" $analysis_dir/$run_name/failed_samples/ \;
 
                    echo "$(date) : Fastq files names are now shortened. Folders and files are in place. You are now ready for downstream bioinformatics analysis"
                else
                    echo "$(date) : $run_name run folder already exists in the $analysis_dir, exiting"
                fi
            else echo "$(date) : No wastewater samples found in $run_name"
            fi
        fi
else
    echo "$(date) : Fastq generation step is not yet completed for run $run_name." 
fi
