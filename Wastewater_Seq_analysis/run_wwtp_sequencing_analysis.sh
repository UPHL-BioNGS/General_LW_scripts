#!/bin/bash
# if any errors, then exit
set -e

###########################
# Author: Pooja Gupta

USAGE="
Purpose: Bash script to automate wastewater sequencing analysis. Consists of three individual scripts
1) WWP_seq_initialize_analysis.sh - Copy fastq files from CovidSeq directory and set up folders for analysis.
2) run_viralrecon.sh - Run viralrecon bioinformatic pipeline with wastewater sequencing data.
3) run_freyja_vrn_noBoot.sh - Run Freyja with BAM files from viralrecon

Usage: ./run_wwtp_sequencing_analysis.sh <wastewater sequencing run_name>

Last updated on August 08,2022
"
###########################

echo "$USAGE"
script_dir='/home/pgupta/General_LW_scripts/Wastewater_Seq_analysis/sub-workflows'
#script_dir='/home/Bioinformatics/General_LW_scripts/Wastewater_Seq_analysis/'
run_name=$1

#Set up wastewater sequencing analysis

$script_dir/WWP_seq_initialize_analysis.sh $run_name

#Run viralrecon
log_file2="/Volumes/IDGenomics_NAS/wastewater_sequencing/$run_name/viralrecon.log"
$script_dir/run_viralrecon.sh $run_name | tee -a $log_file2

echo "$(date) : Checking if the viralrecon pipeline completed successfully"
if
grep -riwq "Pipeline completed successfully" $log_file2
then
    echo "$(date) : Viralrecon pipeline completed successfully and BAM files are available for Freyja analysis"
else
    echo "$(date) : Oops .. something went wrong and pipeline stopped"
    exit 1
fi

#run Freyja
log_file3=/Volumes/IDGenomics_NAS/wastewater_sequencing/$run_name/freyja.log
$script_dir/run_freyja_vrn_noBoot.sh $run_name | tee -a $log_file3
