# General_LW_scripts
The scripts that UPHL uses to download things from basespace and run respective workflows

# USAGE


## MiSeq_runs_basespace.sh

MiSeq_runs_basespace.sh checks basespace every 20 minutes for a new MiSeq sequencing run. This is the script that is run in a screen on the Production account.

Currently only runs Grandeur.

```
MiSeq_runs_basespace.sh
```

## daily_SARS-CoV-2_metadata.sh

daily_SARS-CoV-2_metadata.sh checks the date every 4 hours. If it is a new day, this script runs the Dripping Rock nextflow workflow to get the daily SARS-CoV-2 metadata file. On Sundays, it also takes the latest 20 runs and 10 random runs and creates a phylogenetic tree. This is a script that is run in a screen on the Production account.

## upload_BS_to_ICA.sh

upload_BS_to_ICA.sh starts when it finds a download_comlete.txt file created by MiSeq_runs_basespace.sh; then uploads the fastq files to ICA so that pipeline can be started there. This script should be ran on a screen and icav2 needs to be installed and configured to work. 

```
upload_BS_to_ICA.sh
```
