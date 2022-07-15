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
We are currently uploading sequencing runs that use granduer using the General_LW_scripts/MiSeq_runs_basespace.sh. This script looks for those uploads then sees if they have already had analysis preformed on ICA. If not they start that anaylsis.

### Alternatives if Scripts Fail

#### Manually Starting Anaylsis Using icav2 CLI
This is the basic command for starting an analysis with icav2: ```icav2 projectpipelines start nextflow [pipeline id] or [code] [flags] ```. The pipeline is the name of the pipeline, i.e. UPHL-BioNGS_Granduer_V2. Then you must provide the inputs with this syntax ```--input parametercode:dataId,dataId,dataId,... ``` Finally you must provide a name ```--user reference $SEQUENCING_RUN_PIPELINE_Analysis```
To find data Ids use ```icav2 projectdata list ```.
##### mycosnp
To hard without scripting.

##### Grandeur
Find the data id for the sequecning run, i.e UT-M70330-220712. Use ```icav2 projectdata list --parent-folder /$SEQUENCING_RUN/``` this will output a table with the data id for the /Raw/ folder for the run. This will be used in the command to start the run ```--input reads:fol.a27c13293768402b295f08da58d44868 ``` Then use ```icav2 projectdata list --parent-folder /Grandeur_for_ICA_pods/``` then take all the ids found in that folder. ```--input project_dirs:fol.a27c13293768402b295f08da58d44868,fol.a27c13293768402b295f08da58d44868,...``` Then follow the syntax explained above to start the run.
#### Manually Starting Anaylsis Using ICA Website and UI
##### mycosnp
Because of how the samples are stored from BSSH, in many nested trees, it is inpractical to start runs manually. It would take an hour and errors would be common. UI should only be used to determine and resolve errors.
##### Grandeur
MiSeq_runs_basespace.sh uploads data into ICA; so if the script fails you need to know the name of the sequecning run, i.e UT-M70330-220712. Log into ICA and go to the Testing project (once the script runs around 5 times, we should move this to the Production project). Navigate to the Flow dropdown found on the left of the UI, then click pipelines. Click to highlight "UPHL-BioNGS_Granduer_V2", then click the purple "Start New Analysis" above. Provide the user reference as the sequecning run plus '_Granduer_Analysis', i.e. UT-M70330-220712_Granduer_Analysis. Then under "Input Files" click the purple select button under "Reads". Then find and select the sequecning run name then go one directory down to Raw. As an example path this would be "/UT-M70330-220712/Raw". Then under "PROJECT_DIRS FROM EDITED GIT REPO" click select, then you will click the folder "Grandeur_for_ICA_pods". Then select all folders in this directory; subworkflows, data, moduals, and configs. You also need to reclick the select button and include the directories blast_db_refseq and kraken2_db. Now you can start the run by clicking in the upper right the purple box that says "Start Analysis". To check on the progress of Analyses navigate to the flow dropdown found on the left of the UI, then click Analyses.


### Known Issues
1. Sometimes analyses fail on ICA and I need to work out the best way to restart these runs. This most likly intells releasing pipelines on ICA and moving each scrip from running in Testing to Production projects; which should only happen after we have some evaulation of these scripts.
2. Currently no downloading has been automated in the scripts. I need to clarify with bioinformaticains what needs to be downloaded and I think version control would be easier with creating scripts that are different then the ones starting analyses.
