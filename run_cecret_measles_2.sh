echo "$USAGE"
raw_run=$1 #Output folder name

# Check if the fastq gen step is completed for the new run
run_date=$(echo $raw_run | rev | cut -f 2 -d "/" | rev | cut -f 1 -d "_")
run_instrument=$(echo $raw_run | rev | cut -f 2 -d "/" | rev | cut -f 2 -d "_")
run_name="UT-$run_instrument-$run_date-WW"
echo $run_name


# Checking to see if this run is in the output directory
    
    sample_sheet="/Volumes/NGS/Output/${run_instrument}/$raw_run/SampleSheet.csv"

    # Checking for sample sheet, CopyComplete, and RTAComplete
    if [ -n "$sample_sheet" ]
    then
      echo "$(date) : The sample sheet for $raw_run is $sample_sheet"
    else
      echo "$(date) : FATAL : SampleSheet.csv is missing. Analysis cannot continue."
    fi

# Checking for covid samples: patients and/or wastewater samples
    wastewater_check="$(grep -iE 'Measles[[:space:]]*WW|CPC|NTC|wastewater' "$sample_sheet" | head -n 1 || true)" # SS for wastewater
    patient_check=$(grep -i patient $sample_sheet | head -n 1)       # SS  for patients

 # Checking to see if the analysis has already been run for wastewater samples
if [ ! -d "/Volumes/NGS_2/measles/$run_name" ] && [ -n "$wastewater_check" ]
  then
      echo "$(date) : Wastewater samples were found for $run_name in $sample_sheet, proceed with wastewater analysis"

    #creating log files and set directory structure/paths for the new WW run
    mkdir /Volumes/NGS_2/measles/${run_name}
    analysis_dir=/Volumes/NGS_2/measles/${run_name}
    echo "$(date) : Analysis directory is $analysis_dir."
    mkdir -p /Volumes/NGS_2/measles/$run_name/logs

    # Copying sample sheet from Output run directory to wastewater directory
    cp $sample_sheet $analysis_dir/${run_name}_Samplesheet.csv

    echo "$(date) : Generating list of wastewater samples from the run sample sheet. Used to fetch matching fastq files in the next step"
    grep -iE 'Measles WW|CPC|NTC' $sample_sheet | cut -f 1 -d ',' > $analysis_dir/${run_name}_measles_ww_sample_list.csv

    # Getting a list of all clinical (covid and flu) samples, used to generate wastewater sample sheet
    # grep -iE  'patient|covidseq|flu|influenza|RSV|wastewater' $sample_sheet | cut -f 1 -d ',' > $analysis_dir/${run_name}_other_sample_list.txt

    # Getting a wastewater measles sample sheet
    # grep -Ff $analysis_dir/${run_name}_other_sample_list.txt -v $sample_sheet > $analysis_dir/${run_name}_Samplesheet_measles_ww.csv

    # Getting list of all wastewater samples. Used to fetch matching fastq files in the next steps. 
    # awk -F, '/^\[Cloud_Data\]/,EOF { if ($1 != "Sample_ID" && $1 !~ /^\[/) print $1 }' \
                                         #   $analysis_dir/${run_name}_Samplesheet_ww.csv > $analysis_dir/tmp_ww_list_raw.txt

    # Remove any empty rows
    # grep -v '^[[:space:]]*$' $analysis_dir/tmp_ww_list_raw.txt > $analysis_dir/${run_name}_wastewater_sample_list.csv

    # Set directory structure/paths for the fastq files
    mkdir -p $analysis_dir/fastq
    # Output directory paths
    echo "$(date) : Raw fastq files will be stored in $analysis_dir/$run_name/fastq"
    echo "$(date) : Bioinformatics analysis will be stored in $analysis_dir/analysis"


    # Getting fastq files from NextSeq Output dir
    # Fastq files directory source is $fastq_dir
    fastq_dir=/Volumes/NGS/Output/${run_instrument}/${raw_run}/Analysis/1/Data/fastq
    # Fastq files directory destination
    ww_fastq=$analysis_dir/fastq

    echo "$(date) : Copying fastq files from $fastq_dir to $ww_fastq directory to run with viralrecon"
    find $fastq_dir -type f -name '*.fastq.gz' -print0 | grep -zf $analysis_dir/${run_name}_measles_ww_sample_list.csv| parallel -0 "cp {} $ww_fastq/"

    echo "$(date) : Fastq files copied successfully to $ww_fastq"

    cp $fastq_dir/*CPC*.fastq.gz $ww_fastq/
    cp $fastq_dir/*NTC*.fastq.gz $ww_fastq/


# ---------------------------------
# Run Cecret analysis
# ---------------------------------

# Set directory structure/paths for Cecret analysis

new_fastq_dir=/Volumes/NGS_2/measles/$run_name/fastq
out_dir=/Volumes/NGS_2/measles/$run_name/Cecret/

cd $out_dir

 echo "$(date) : First create input samplesheet for viralrecon pipeline"
 python /Volumes/NGS/Bioinformatics/dragen_scripts/fastq_dir_to_samplesheet.py $new_fastq_dir $out_dir/${run_name}_samplesheet_cecret.csv

# Run cecret with fastqs (Erin needs to update the github version so we are running the local version for now as mentioned below)

nextflow run UPHL-BioNGS/Cecret \
    -profile uphl,slurm,mev \
    --sample_sheet /Volumes/NGS_2/measles/$run_name/Cecret/${run_name}_samplesheet_cecret.csv \
    --reference_genome /Volumes/NGS_2/measles/references/NC_001498.1.fasta \
    --primer_bed /Volumes/NGS_2/measles/references/NC_001498.1_primal_tiling_primer.bed \
    --outdir $out_dir

echo "$(date) : Cecret analysis complete!!!"

fi

