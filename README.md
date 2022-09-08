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

 
## RCovidSummary.R

This script shold be run after the analytics phase and the pangolin-lineage are completed. The script summaryzes the run and generated two files: RunParameters and RCovidseq_summary, that will be stored at the runpath/Rsumcovidseq folder. 

RunParameters: Is the collection of the run static parameters: Wetlab assay, instrument type, software, pangolin version, Read Type, Number of Samples, number of Lanes, Chemistry , index adapters and the date of the run.

Rcovidseq_summary: Is the collecton of the dynamic variables: sample_IDs, lineage, scorpion_call, num_actg, num_n, pass/fail.
