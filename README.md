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

## ICA Automation Scripts
These scripts are intened to make the running of analyses on ICA for production purposes automated as well as downloading the most common files that need to be reviewed by human eyes. Each is written in python and uses the icav2 command line tool provided by Illumina. These are intened to run on screens on the linux work station but whereever they are ran icav2 must already be installed and configured on that system.

### Usage
These scripts run on infinite loops that should be ran on a screen in the background.
```
python auto_Granduer_ICA.py
```
```
python auto_mycosnp_ICA.py
```

### mycosnp
Currently this pipeline is only ran on C. auris samples. These samples are usually uploaded directly by the Illumia instrument after BSSH calls the reads into ICA.
The automation script runs each time these file make there way to ICA. It produces the samplesheet, including control samples, needed for the analysis and uploads it to ICA. It then starts the anaylsis

### Grandeur
We currently upload sequencing runs that use granduer using the General_LW_scripts/MiSeq_runs_basespace.sh. This script looks for those uploads then sees if they have already had anaylsis preformed on ICA. If not they start that anaylsis.

### Manually Starting Anaylsis Using icav2 CLI
#### mycosnp
#### Grandeur

### Manually Starting Anaylsis Using ICA Website and UI
#### mycosnp
Because of how the samples are stored from BSSH, many nested trees, it is inpractical to start runs manually. It would take an hour and errors would be common. UI can be used to determine and resolves errors.
#### Grandeur


### Known Issues
1. Sometimes analyses fail on ICA and I need to work out the best way to restart these runs. This most likly intells releasing pipelines on ICA and moving each scrip from running in Testing to Production projects; which should only happen after we have some evaulation of these scripts.
2. Currently no downloading has been automated in the scripts. I need to clarify with bioinformaticains what needs to be downloaded and I think version control would be easier with creating scripts that are different then the ones starting analyses.
