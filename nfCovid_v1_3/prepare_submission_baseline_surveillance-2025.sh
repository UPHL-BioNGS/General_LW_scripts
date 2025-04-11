#!/bin/bash

# bash script to copy and rename fastas and fastqs for submission to SRA, GenBank and GISAID, including the fastas concatenation for GenBank and GISAID submissions

# Note 1 of 2: the submission file (submission.csv) must be created first.
# i.e: 
# bash /Volumes/NGS/Bioinformatics/Lin/prepare_submission_baseline_surveillance-2023.sh  /Volumes/NGS/Analysis/covidseq/UT-VH00770-230518/  /Volumes/NGS/Analysis/covidseq/UT-VH00770-230518/submission.csv

display_usage() {
	echo -e "Example usage: bash prepare_submission_baseline_surveillance-2023.sh /Volumes/NGS/Analysis/covidseq/UT-VH00770-231201"
	echo "Full path to project directory must be supplied."
	}

if [[ ( $# == "--help") ||  $# == "-h" ]]
  then
  echo -e "usage"
  display_usage
  	exit 0
fi

# user supplies project_path and submission.csv
  project_path=$1
  gsheet_csv=$2
echo $project_path
exec 3>&1 4>&2

# getting the run name
  run_name=$(echo $project_path  | tr '/' '\n' | grep 'UT')


# creating  submission folders  for SRA, GenBank and GISAID
  mkdir -p ${project_path}/submission_files1/genbank
  mkdir -p ${project_path}/submission_files1/gisaid
  mkdir -p ${project_path}/submission_files1/fastq-${run_name}



  tail -n+2 ${gsheet_csv} | while read line || [ -n "$line" ]; 
do
   accession=$(echo $line | awk -F','  '{print $1}'  )
   sub_id=$(echo $line | awk -F',' '{print $2}' )
   num_actg=$(echo $line | awk -F',' '{print $6}' )
   collection_date=$(echo $line | awk -F',' '{print $3}' )
   collection_year=$(echo ${collection_date} | awk -F'-' '{print $1}')
   num_actg="${num_actg//[$'\t\r\n ']}"
  
   echo ${accession}
   echo ${sub_id}
   echo ${num_actg}

   # Renaming the fastq for submission
   scp ${project_path}/covidseq_output/Logs_Intermediates/FastqGeneration/${accession}*/*_R1_*.fastq.gz ${project_path}/submission_files1/fastq-${run_name}/${sub_id}.R1_fastq.gz
   scp ${project_path}/covidseq_output/Logs_Intermediates/FastqGeneration/${accession}*/*_R2_*.fastq.gz ${project_path}/submission_files1/fastq-${run_name}/${sub_id}.R2_fastq.gz


   # Note 2 of 2:  Only HARD  fastas sequences can be submmitted to GenBank and GISAID DBs, that means the fasta files MUST be from the Sample_Analysis folder NOT from the ConsensusFastas folder!!!

   # GenBank. GenBank lower limit of 15K non-ambiguous
   if [ ${num_actg} -ge 15000 ]
     then
      # This header is required by GenBank platform
      genbank_head=$(echo '>'"${sub_id}"' [keyword=purposeofsampling:baselinesurveillance][Country=USA][Host=Human][Isolate=SARS-CoV-2/Human/USA/'"${sub_id}"'/'"2025"'][Collection-Date='"${collection_date}"']' )
        echo $genbank_head
        echo $genbank_head > ${project_path}/submission_files1/genbank/${sub_id}.fa
        tail -n+2 ${project_path}/covidseq_output/Sample_Analysis/${accession}*/*.fasta >> ${project_path}/submission_files1/genbank/${sub_id}.fa
     fi


   # GISAID. GISAID lower limit of 25K non-ambiguous for SARS-CoV-2 sequences
   if [ ${num_actg} -ge 25000 ]
    then
      gisaid_head=$(echo '>hCoV-19/USA/'"${sub_id}"'/'2025)
      echo $gisaid_head > ${project_path}/submission_files1/gisaid/${sub_id}.fa
      tail -n+2 ${project_path}/covidseq_output/Sample_Analysis/${accession}*/*.fasta >> ${project_path}/submission_files1/gisaid/${sub_id}.fa
    fi
done


# concatenating files for submission
 cat ${project_path}/submission_files1/genbank/*.fa > ${project_path}/submission_files1/genbank/GenBank_submission.fasta
 cat ${project_path}/submission_files1/gisaid/*.fa > ${project_path}/submission_files1/gisaid/GISAID_submission.fasta

# update permissions
# chmod -R ugo+rwx  ${project_path}/submission_files1
