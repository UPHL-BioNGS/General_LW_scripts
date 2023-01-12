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
sh WWP_seq_initialize_analysis.sh <wastewater sequencing run_name> | tee -a WWP_seq_initialize_analysis.log
Last updated on Jan 12,2023
"
###########################

echo "$USAGE"

run_name=$1

#Check if the fastq gen step is completed for the new WW run
if [ ! -f "/Volumes/IDGenomics_NAS/wastewater_sequencing/$run_name/fastqgen_complete.txt" ]
then
    echo "$(date) : Fastq generation step is not yet completed for run $run_name"
    exit 1
fi
echo "$(date) : Fastq generation step is completed for run $run_name."

#Setting directory structure for the new WW run
analysis_dir=/Volumes/IDGenomics_NAS/wastewater_sequencing/${run_name}
echo "$(date) : Analysis directory is $analysis_dir."

echo "$(date) : Creating sub directories for downstream analysis"
mkdir -p $analysis_dir/{ncbi_submission,analysis,failed_samples,results}

mkdir -p $analysis_dir/raw_data/fastq
#Output directory paths
#echo "$(date) : Raw fastq files will be stored in $analysis_dir/$run_name/raw_data"

#echo "$(date) : Bioinformatics analysis will be stored in $analysis_dir/$run_name/analysis"

#Check if the run is completed and sample sheet exists for the run
sample_sheet="$(ls $analysis_dir/*_wastewater.csv | head -n 1)"
echo "$(date) : The sample sheet for run $run_name is $sample_sheet"

#Verify whether sample sheet contains any wastewater samples. This will mostly be true.
#if [[ -n $(grep -i 'Wastewater' $sample_sheet) ]]
#then
#    echo "$(date) : Some wastewater samples found in $run_name"
#    else
#        echo "$(date) : No wastewater samples found in $run_name .. exiting"
#        exit 1
#fi

#Lane=$(grep -i 'Wastewater' $sample_sheet | cut -f 11 -d ',' | head -1)
#SetNo=$(grep -i 'Wastewater' $sample_sheet | cut -f 4 -d ',' | head -1)

#awk -F"," '$11 == 4 || $3 == "Wastewater" {print $2}' $sample_sheet

#Get fastq files for each wastewater sample in the new run
echo "$(date) : Generating list of wastewater samples from the run sample sheet. Used to fetch matching fastq files in the next step"
#grep -i 'Wastewater' $sample_sheet | cut -f 2 -d ',' > $analysis_dir/${run_name}_wastewater_sample_list.csv

#Currently doing this to avoid additional positive and negative controls to be included in the downstream analysis 
grep -i '$WWP' $sample_sheet | cut -f 2 -d ',' > $analysis_dir/${run_name}_wastewater_sample_list_edi.csv

#Fastq files directory source
fastq_dir=$analysis_dir/raw_data
#Fastq files directory destination
ww_fastq=$analysis_dir/raw_data/fastq

echo "$(date) : Copying fastq files from $fastq_dir to wastewater sequencing analysis directory to run with viralrecon or Cecret"
find $fastq_dir -type f -name '*.fastq.gz' -print0 | grep -zf $analysis_dir/${run_name}_wastewater_sample_list.csv | parallel -0 "cp {} $ww_fastq/"
echo "$(date) : Fastq files copied successfully to $analysis_dir/$run_name/raw_data"

#Samples that fail after the run are excluded from downstream analysis. This step is nececssary for running samples with viralrecon otherwise oftentimes, the pipeline fails

cd $ww_fastq

echo "$(date) : Moving failed samples from raw_data directory to another directory (failed_samples) based on file size < 2MB"
find $ww_fastq -type f -name "*.fastq.gz" -size -2M -print0 | parallel -0 mv {} $analysis_dir/failed_samples/ 

# Copy fastq files to NCBI submission directory with shortened names and also rename fastq files in the raw-data directory that will be used for bioinformatics analysis.
echo "$(date) : Copy fastq files with cleaned IDs for NCBI submission and for downstream analysis"
ls $ww_fastq | parallel "cp {} $analysis_dir/ncbi_submission/{=s/\-A01290.*//=}_R1.fastq.gz; mv {} {=s/\_.*//=}_R1_001.fastq.gz;" 

echo "$(date) : Fastq files ready for NCBI submission. Fastq filenames have been cleaned"

#Generating csv text file used later in Data-flo for creating NCBI submission template
echo "$(date) : Create a csv file with NCBI submission ID and associated fastq file names which gets uploaded to Data-flo for generating NCBI submission templates"
for file in $analysis_dir/ncbi_submission/*.fastq.gz; 
do
    #echo ${file##*/}
    sample_id=$(basename "$file" _R1.fastq.gz)
    echo $sample_id
    #Generating a csv file with NCBI submission ID and associated fastq file names which gets uploaded to Data-flo for generating NCBI submission templates
    echo "${sample_id},${file##*/}" >> ${analysis_dir}/${run_name}_ncbi_submission_info.csv
done

echo "$(date) : Fastq files names are now cleaned. Folders and files are in place. You are now ready for downstream bioinformatics analysis and NCBI submission."   
