 #!/bin/bash
# if any errors, then exit
set -euxo pipefail

###########################
# Author: Pooja Gupta

USAGE="
Purpose: Bash script to run viralrecon bioinformatic pipeline with wastewater sequencing data.

Usage: run_viralrecon.sh <wastewater sequencing run_name>

Last updated on June 13,2022
"
###########################

echo $USAGE
run_name=$1

analysis_dir='/Volumes/IDGenomics_NAS/wastewater_sequencing'
mkdir -p /Volumes/IDGenomics_NAS/wastewater_sequencing/$run_name/analysis/viralrecon/work

#Creating required folders for analysis
ww_fastq=$analysis_dir/$run_name/raw_data
out_dir=$analysis_dir/$run_name/analysis/viralrecon
work_dir=$analysis_dir/$run_name/analysis/viralrecon/work
results=$analysis_dir/$run_name/results

infile=${run_name}_samplesheet.csv
log_file=$out_dir/${run_name}_viralrecon.log

echo "$(date) : Run Wastewater sample data with viralrecon for run $run_name"
echo "$(date) : First create input samplesheet for viralrecon pipeline"

if [ ! -f "$out_dir/${run_name}_samplesheet.csv" ]
    then
        echo "$(date) : $infile does not exist. Creating samplesheet required to run viralrecon"
        python /home/pgupta/pscripts/fastq_dir_to_samplesheet.py $ww_fastq $out_dir/$infile
        echo "$(date) : $infile Samplesheet generated" 
    else echo "$(date) : $infile already exists, starting viralrecon"
fi

#check R1 extension in the python script, if different from default

echo "$(date) : Running viralrecon"
#export SINGULARITY_CACHEDIR=/home/pgupta/singularity
#export NXF_SINGULARITY_CACHEDIR=/home/pgupta/singularity

#Use UPHL_viralrecon.config to update Pangolin container, if needed

nextflow run nf-core/viralrecon --input $out_dir/$infile \
                                --primer_set_version 4 \
                                --outdir $out_dir \
                                --nextclade_dataset /Volumes/IDGenomics_NAS/wastewater_sequencing/nextclade-data/20220504/sars-cov-2_MN908947 \
				                --nextclade_dataset_tag "2022-04-28T12:00:00Z" \
                                --multiqc_config /Volumes/IDGenomics_NAS/wastewater_sequencing/conf-files/new_multiqc_config.yaml \
                                -profile singularity \
                                -params-file /Volumes/IDGenomics_NAS/wastewater_sequencing/conf-files/UPHL_viralrecon_params.yml \
                                -c /Volumes/IDGenomics_NAS/wastewater_sequencing/conf-files/UPHL_viralrecon.config -w $work_dir
 
echo "$(date) : Copying variant long table result file to $results folder"
cp $out_dir/variants/ivar/variants_long_table.csv $results/${run_name}_variants_long_table.csv

echo "$(date) : Copying pangolin result files to the $results folder after merging individual pangolin result files" 
cat $out_dir/variants/ivar/consensus/bcftools/pangolin/*.csv | awk '!a[$0]++' > $results/${run_name}_viralrecon_lineage_report.csv

echo "$(date) : Copying multiqc result files to the results folder"
cp $out_dir/multiqc/multiqc_report.html $results/${run_name}_multiqc_report.html
cp $out_dir/multiqc/summary_variants_metrics_mqc.csv $results/${run_name}_summary_variants_metrics_mqc.csv


echo "$(date) : Cleaning up...removing the work directory"
rm -r $work_dir