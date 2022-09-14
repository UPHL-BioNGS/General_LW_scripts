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
RCovidSummary.R should be run once the dragen-covid-pipeline.sh has finished on a SARS-CoV-2 covidseq run (runs on the dragen server), and pangolin has been run on the resultant fasta files. 
The script summarizes the run and generates two files in the $runpath/Rsumcovidseq directory: RunParameters-$date.csv (values that are the same for each sample) and RCovidseq_summary-$date.csv (values that are specific to each sample)
Rscript RCovidSummary.R UT-A01290-220901
