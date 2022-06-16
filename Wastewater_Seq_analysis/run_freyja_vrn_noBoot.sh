#! /bin/bash
# if any errors, then exit
set -euxo pipefail

###########################
# Author: Pooja Gupta

USAGE="
Purpose:
1) Run Freyja tool with wastewater sequencing data. 
2) Retrieve BAM files for each sample generated by Viralrecon
3) The input data are the bam files after ivar primer trimming step.
Usage:
run_freyja_vrn_noBoot.sh <wastewater sequencing run_name>
Last updated on: June 13,2022
"
###########################

echo $USAGE

#Get Freyja tool (need to replace with Freyja's docker container)
source /home/pgupta/miniconda3/etc/profile.d/conda.sh
conda activate /home/pgupta/miniconda3/envs/freyja-lin

run_name=$1
analysis_dir=/Volumes/IDGenomics_NAS/wastewater_sequencing
#creating required folders for analysis

mkdir -p /Volumes/IDGenomics_NAS/wastewater_sequencing/$run_name/analysis/freyja/lineage_out
workdir=$analysis_dir/$run_name/analysis/freyja
in_dir=$analysis_dir/$run_name/analysis/viralrecon/variants/bowtie2  #using bam files from viralrecon instead of Cecret
outdir=$workdir/lineage_out/
results=$analysis_dir/$run_name/results

scov2=$analysis_dir/covidseq_ref/MN908947.3.fasta

echo "$(date): Starting Freyja" 
echo "$(date): Getting the input varaints and depth file from bam files for Freyja analysis"
for bam in ${in_dir}/*_trim.sorted.bam;
do 
    infile=${bam##*/}; echo "$(date): input file name is $infile"
    sample=${infile%_UT*}; echo "$(date): base name is $sample" 
    echo "$(date): Freyja running for $sample"  
    freyja variants ${bam} --variants $workdir/${sample}_out_variants --depths $workdir/${sample}_out_depths --ref $scov2;
done

echo "$(date): Running Demultiplexing step in Freyja"

echo "$(date): Demultiplexing results will be stored in $outdir"

for file in ${workdir}/*.tsv;
do
    sample=$(basename $file _out_variants.tsv)
    echo "base name is $sample"
    depth=${sample}_out_depths
    var=${sample}_out_variants.tsv

    echo "$(date): Freyja demultiplexing step running for $sample"
    
    freyja demix $workdir/${var} $workdir/${depth} --eps 0.01 --covcut 10 --confirmedonly --output $outdir${sample}_lin_out.tsv

#echo "$(date): Boostrap analysis step running for $sample" | tee -a $log_file
#freyja boot $workdir/${var} $workdir/${depth} --nt 8 --nb 500 --eps 0.01 --output_base $outdir${sample}_boot.tsv
done

echo "$(date): Running lineage aggregation step in Freyja"
cd $outdir
freyja aggregate $outdir --output ${run_name}_lineages_aggregate.tsv --ext tsv
echo "$(date): Lineage aggregration completed and aggregrated tsv is stored in $outdir"

echo "$(date): Plotting lineage aggregate output from Frejya"
freyja plot ${outdir}${run_name}_lineages_aggregate.tsv --output ${run_name}_lineages_aggregate_plot.png --lineages

echo "$(date): Freyja analysis completed"

echo "$(date): Extracting freyja lineage dictionary results and converting it to a long dataframe for downstream processing using the python script freyja_lin_agg_to_dict_long_df_20220603.py"
    
python /Volumes/IDGenomics_NAS/wastewater_sequencing/wwtp_pscripts/freyja_lin_agg_to_dict_long_df_20220603.py ${run_name}

#Copying output files to results directory
echo "$(date) : Copying Freyja aggregate lineage results and long dataframe to $results"
cp *lineages_aggregate.tsv $results
cp *_lin_dict_long_df_lingrps_final.csv $results
    
echo "$(date): Freyja analysis post-processing completed. The lin_dict_long_df can now be uploaded to Data-flo for visualization in Microreact"