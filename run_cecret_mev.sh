'''
Author: Robby Sainsbury

Description:
  This script will run Cecret on the clinical measles samples from the run name given.
  It creates the necessary directory structure, copies raw fastq files, creates a samplesheet for Cecret to use, then runs Cecret. 
  The Cecret results can be found here after completetion: /Volumes/NGS_2/measles/"runName"-mev/cecret

EXAMPLE:
bash /General_LW_scripts/run_cecret_mev.sh <run name>
'''


echo "$USAGE"
run_name=$1 #Run name 

#get information from run name
run_date=$(echo $run_name | cut -f 3 -d "-")
run_instrument=$(echo $run_name | cut -f 2 -d "-")

#find raw output dir
raw_output_dir=$(find /Volumes/NGS/Output/$run_instrument -maxdepth 1 -type d -name "$run_date*")

run_dir="$run_name-mev"


# Checking to see if this run is in the output directory
    
    sample_sheet="$raw_output_dir/SampleSheet.csv"

    # Checking for sample sheet, CopyComplete, and RTAComplete
    if [ -n "$sample_sheet" ]
    then
      echo "$(date) : The sample sheet for $raw_output_dir is $sample_sheet"
    else
      echo "$(date) : FATAL : SampleSheet.csv is missing. Analysis cannot continue."
    fi

# Checking for mev clinical samples
    mev_check="$(grep -iE 'Measles-2' "$sample_sheet" | head -n 1 || true)" # SS for clinical

 # Checking to see if the analysis has already been run for clinical samples
if [ ! -d "/Volumes/NGS_2/measles/$run_dir" ] && [ -n "$mev_check" ]
  then
      echo "$(date) : MeV clinical samples were found for $run_dir in $sample_sheet, proceed with MeV clinical analysis"

    #set directory structure/paths for the new mev run
    mkdir /Volumes/NGS_2/measles/${run_dir}
    analysis_dir=/Volumes/NGS_2/measles/${run_dir}
    echo "$(date) : Analysis directory is $analysis_dir."

    # Copying sample sheet from output run directory to wastewater directory
    cp $sample_sheet $analysis_dir/instrumentsamplesheet.csv

    # Getting fastq files from Output dir
    # Fastq files directory source 
    export old_fastq_dir=${raw_output_dir}/Analysis/1/Data/fastq
    # Fastq files directory destination
    export new_fastq_dir=$analysis_dir/reads

    #copying raw fastq files
    echo "$(date) : Copying raw fastq files to $new_fastq_dir"
    mkdir $new_fastq_dir
    grep ",Measles-2" $analysis_dir/instrumentsamplesheet.csv | cut -d ',' -f 1 | xargs -n 1 sh -c 'cp ${old_fastq_dir}/"$0"*fastq.gz ${new_fastq_dir}/'
    
    #creating Cecret samplesheet
    echo "$(date) : Creating Cecret samplesheet"
    find /Volumes/NGS_2/measles/${run_dir}/reads -name "*_R[12]_001.fastq.gz" | sort | paste - - | awk 'BEGIN{print "sample,fastq_1,fastq_2"}{print gensub(/\/Volumes.*\/reads\/|_S[0-9]*_R[12]_001.fastq.gz/, "","g", $1)","$1","$2}' > $analysis_dir/cecretsamplesheet.csv

    # ---------------------------------
    # Run Cecret analysis
    # ---------------------------------

    # Set directory structure/paths for Cecret analysis

    out_dir=/Volumes/NGS_2/measles/$run_dir/Cecret/
    echo "$(date) : Runing Cecret, output will go here: $out_dir"

    cd $analysis_dir

    # Run cecret with fastqs 

    nextflow run UPHL-BioNGS/Cecret \
      -profile uphl,slurm,mev \
      --sample_sheet cecretsamplesheet.csv \
      --reference_genome /Volumes/NGS_2/measles/references/NC_001498.1.fasta \
      --primer_bed /Volumes/NGS_2/measles/references/NC_001498.1_primal_tiling_primer.bed  \
      --samtools_ampliconstats false

    echo "$(date) : Cecret analysis complete!!!"

elif [! -d "/Volumes/NGS_2/measles/$run_dir" ]
  then
    echo "$(date) : MeV clinical samples were NOT found for $run_dir in $sample_sheet, cannot proceed with MeV clinical analysis"
elif [ -n "$mev_check" ]
  then
    echo "$(date) : $run_dir already exists, the analysis has likely been completed already"

fi
