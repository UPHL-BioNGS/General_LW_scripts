# General_LW_scripts
The scripts that UPHL uses to download things from basespace and run respective workflows

# USAGE


## MiSeq_runs_basespace.sh

MiSeq_runs_basespace.sh checks basespace every 20 minutes for a new MiSeq sequencing run. This is the script that is run in a screen on the Production account.

Script downloads run data to IDGenomics_NAS and also uploads to ICA. icav2 needs to be installed and configured to work. 

Currently only runs Grandeur.

```
MiSeq_runs_basespace.sh
```

## daily_SARS-CoV-2_metadata.sh

daily_SARS-CoV-2_metadata.sh checks the date every 4 hours. If it is a new day, this script runs the Dripping Rock nextflow workflow to get the daily SARS-CoV-2 metadata file. On Sundays, it also takes the latest 20 runs and 10 random runs and creates a phylogenetic tree. This is a script that is run in a screen on the Production account.

## summary_v2.R
This creates the sumcovidseq file for SARS_CoV-2 for PatientSamples.
The sumcovidseq file will contain information about the sequencer variables (readType/readLength/sofware, instrument type, wetLab, etc),and information about the samples (number of amplicons, nucleotides counts (actg,n),
Pangolin lineage,pangolin version, sample_ID, etc).

Note: The sample_ID is composed, among other things, for two random numbers (three digits each), that means if the script runs again the sample_ID will be different. (example: UT-UPHL-220416randomNumber1randomNumber2)

Arguments: runName
Example: Rscript / . ./ . . /summary_v2.R UT-A01290-220416

