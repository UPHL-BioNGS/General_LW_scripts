#!/bin/bash
# if any errors, then exit
set -e

###########################
# Author: Pooja Gupta

USAGE="
Purpose:
1) Copy fastq files from CovidSeq analysis directory to wastewater sequencing analysis directory on NAS.
2) Setup directory structure for initiating Wastewater sequencing run analysis and any downstream analysis.
3) Generate ncbi submission folder that can be directly used for uploading files to NCBI.

Usage:
sh WWP_seq_initialize_analysis_manual.sh <wastewater sequencing run_name> | tee -a WWP_seq_initialize_analysis.log
Last updated on Jan 12,2023
"
###########################

echo "$USAGE"

run_name=$1
log_files=/Volumes/NGS/Analysis/covidseq/$run_name/covidseq_output/Logs_Intermediates

if [ ! -d "$log_files/VirusDetection" ]
then
    echo "$(date) : Fastq generation step is not yet completed for run $run_name"
    exit 1
fi
echo "$(date) : Fastq generation step is completed for run $run_name."

#Setting directory structure for the new WW run
analysis_dir='/Volumes/IDGenomics_NAS/wastewater_sequencing'
echo "$(date) : Analysis directory is $analysis_dir."

if [ -d "$analysis_dir/$run_name" ]
then
    echo "$(date) : $run_name run folder already exists in the $analysis_dir .. exiting"
    exit 1
fi

echo "$(date) : $run_name run folder was not found in the $analysis_dir"
echo "$(date) : Creating $run_name run folder and sub directories for storing raw fastq files and other downstream analysis"
mkdir -p $analysis_dir/$run_name/{raw_data,ncbi_submission,fasta,analysis,failed_samples,results}

#Output directory paths
#echo "$(date) : Raw fastq files will be stored in $analysis_dir/$run_name/raw_data"
#echo "$(date) : Fasta files will be stored in $analysis_dir/$run_name/fasta"
#echo "$(date) : Bioinformatics analysis will be stored in $analysis_dir/$run_name/analysis"

#Check if the run is completed and sample sheet exists for the run
sample_sheet="$(ls $log_files/SampleSheetValidation/SampleSheet_Intermediate.csv | head -n 1)"
if [ ! -f "$log_files/SampleSheetValidation/SampleSheet_Intermediate.csv" ]
then
    echo "$(date) : The sample sheet for run $run_name does not exist. Expected $sample_sheet"
    exit 1
fi
echo "$(date) : The sample sheet for run $run_name is $sample_sheet"

#Check whether sample sheet contains any wastewater samples. This will mostly be true.
if [[ -n $(grep -i 'Wastewater' $sample_sheet) ]]
then
    echo "$(date) : Some wastewater samples found in $run_name"
    else
        echo "$(date) : No wastewater samples found in $run_name .. exiting"
        exit 1
fi

#Get fastq files for each wastewater sample in the new run
echo "$(date) : Generating list of wastewater samples from the run sample sheet. Used to fetch matching fastq files in the next step"
grep -iq 'Wastewater' $sample_sheet | cut -f 2 -d ',' > $analysis_dir/$run_name/${run_name}_wastewater_sample_list.csv

#Fastq files directory source
fastq_dir=$log_files/FastqGeneration

#destination wastewater sequencing analysis directory
mkdir -p $analysis_dir/$run_name/raw_data/fastq
ww_fastq=$analysis_dir/$run_name/raw_data/fastq

echo "$(date) : Copying fastq files from $fastq_dir to wastewater sequencing analysis directory to run with viralrecon"
find $fastq_dir -type f -name '*.fastq.gz' -print0 | grep -zf $analysis_dir/$run_name/${run_name}_wastewater_sample_list.csv | parallel -0 "cp {} $ww_fastq/"
echo "$(date) : Fastq files copied successfully to $analysis_dir/$run_name/$ww_fastq"

#Samples that fail after the run are excluded from downstream analysis. This step is nececssary for running samples with viralrecon otherwise oftentimes, the pipeline fails

cd $ww_fastq

echo "$(date) : Moving failed samples from raw_data directory to another directory (failed_samples) based on file size < 2MB"
find $ww_fastq -type f -name "*.fastq.gz" -size -2M -print0 | parallel -0 mv {} $analysis_dir/$run_name/failed_samples/ 

# Copy fastq files to NCBI submission directory with shortened names and also rename fastq files in the raw-data directory that will be used for bioinformatics analysis.
echo "$(date) : Copy fastq files with cleaned IDs for NCBI submission and for downstream analysis"
ls $ww_fastq | parallel "cp {} $analysis_dir/$run_name/ncbi_submission/{=s/\-A01290.*//=}_R1.fastq.gz; mv {} {=s/\_.*//=}_R1_001.fastq.gz;" 
echo "$(date) : Fastq files ready for NCBI submission. Fastq filenames have been cleaned"

#Generating csv text file used later in Data-flo for creating NCBI submission template
echo "$(date) : Create a csv file with NCBI submission ID and associated fastq file names which gets uploaded to Data-flo for generating NCBI submission templates"
for file in $analysis_dir/$run_name/ncbi_submission/*.fastq.gz; 
do
    #echo ${file##*/}
    sample_id=$(basename "$file" _R1.fastq.gz)
    echo $sample_id
    #Generating a csv file with NCBI submission ID and associated fastq file names which gets uploaded to Data-flo for generating NCBI submission templates
    echo "${sample_id},${file##*/}" >> ${analysis_dir}/${run_name}/${run_name}_ncbi_submission_info.csv
done

echo "$(date) : Fastq files names are now cleaned. Folders and files are in place. You are now ready for downstream bioinformatics analysis and NCBI submission."   
