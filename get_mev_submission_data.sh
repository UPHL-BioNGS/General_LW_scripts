'''
Author: Robby Sainsbury

Description:
  This script will process the files that need to be submitted to NCBI, as well as renaming consensus files for Abbey to use
  It creates the necessary directory structure. Then it copies and renames consensus files, raw fastq files, and vadr output files to the proper locations
  Requires that the submission csv file exported from LW8 be placed in the run directory: /Volumes/NGS_2/measles/run_name-mev/
  Renamed consensus files end up here: /Volumes/NGS_2/measles/run_name-mev/renamed_consensus
  Renamed fastq files for submission to SRA: /Volumes/NGS_2/measles/submissions/submission_date/fastq
  Renamed vadr results for submission to GenBank end up here: /Volumes/NGS_2/measles/submissions/submission_date/fasta

EXAMPLE:
bash /General_LW_scripts/run_cecret_mev.sh <run name> <submission date formatted like: "2026-02-23">
'''

echo "$USAGE"
run_name=$1 #Run name 
export sub=$2 #submission_date
#get information from run name
run_date=$(echo $run_name | cut -f 3 -d "-")
run_instrument=$(echo $run_name | cut -f 2 -d "-")


#set run dir and analysis dir
run_dir="${run_name}-mev"
export analysis_dir="/Volumes/NGS_2/measles/${run_dir}"

lw8_export="${analysis_dir}/${run_name}_export.csv"

## Renaming Consensus files

export renamed_consensus_dir="${analysis_dir}/renamed_consensus"
mkdir ${renamed_consensus_dir}

export renaming_cons_subs_sed="${renamed_consensus_dir}/subs.sed"
#making subs.sed file for renaming consensus files using awk (skips the first line, then prints out the test ID column and the Sample ID column in the proper format)
awk -F',' 'NR > 1 {print "s/"$1"/"$10"/"}' ${lw8_export} > ${renaming_cons_subs_sed}

renaming_cons_samples_tsv="${renamed_consensus_dir}/samples.tsv"

#making samples.tsv for renaming consensus files using awk (skips the first line, then prints out the test ID column and the Sample ID column seperated by tabs)
awk -F',' 'NR > 1 {gsub(/"/, "");print $1"\t"$10}' ${lw8_export} > ${renaming_cons_samples_tsv}

#copying consensus files and changing their names
cat ${renaming_cons_samples_tsv} | cut -f 1,2 | xargs -n 2 sh -c  'cat ${analysis_dir}/cecret/consensus/"$0".consensus.fa | sed -f ${renaming_cons_subs_sed} >  ${renamed_consensus_dir}/"$1".consensus.fa'

#removing the subs.sed and samples.tsv
rm ${renaming_cons_subs_sed} && rm ${renaming_cons_samples_tsv}


## Making submission files

export sub_dir="/Volumes/NGS_2/measles/submissions/${sub}"

#making file strucuture 
mkdir -p ${sub_dir}/{fasta,fastq}

fastq_samples_tsv="${sub_dir}/samples.tsv"
#making samples.tsv for renaming fastq files using awk (skips the first line, then prints out the test ID column and the Submission ID column seperated by tabs)
awk -F',' 'NR > 1 {gsub(/"/, "");print $1"\t"$5}' ${lw8_export} > ${fastq_samples_tsv}

#copying fastq files over and renaming them
cat ${fastq_samples_tsv} | parallel --colsep "\t" cp ${analysis_dir}/reads/{1}*R1*fastq.gz ${sub_dir}/fastq/{2}_R1.fastq.gz
cat ${fastq_samples_tsv} | parallel --colsep "\t" cp ${analysis_dir}/reads/{1}*R2*fastq.gz ${sub_dir}/fastq/{2}_R2.fastq.gz

export fasta_subs_sed="${sub_dir}/fasta/subs.sed"
#making subs.sed file for renaming consensus files using awk (skips the first line, then prints out the test ID column and the Submission ID column in the proper format)
awk -F',' 'NR > 1 {gsub(/"/, "");print "s/"$1"/"$5"/"}' ${lw8_export} > ${fasta_subs_sed}

#copy vadr fasta file over and change ids in file to submission ids
cat ${analysis_dir}/cecret/vadr/vadr.vadr.pass.fa | sed -f ${fasta_subs_sed} > ${sub_dir}/fasta/ultimate.fa
cat ${analysis_dir}/cecret/vadr/vadr.vadr.pass.tbl | sed -f ${fasta_subs_sed} > ${sub_dir}/fasta/ultimate.tbl

#removing subs sed file because it is not longer needed
rm ${fasta_subs_sed}

echo "Done renaming consensus files and processing files for submisssion to NCBI for MeV clincial samples from run: ${run_name}"
echo "Renamed consensus files are located here: ${renamed_consensus_dir}"
echo "Renamed fastq files for submission to SRA: ${sub_dir}/fastq"
echo "Renamed vadr results for submission to GenBank end up here: ${sub_dir}/fasta"
