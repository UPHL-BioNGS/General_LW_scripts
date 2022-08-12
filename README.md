# General_LW_scripts
The scripts that UPHL uses to download things from basespace and run respective workflows
### ICA Automation Scripts
These scripts are intended to make the running of analyses on ICA for production purposes automated as well as downloading the most common files that need to be reviewed by human eyes. Each is written in python and uses the icav2 command line tool provided by Illumina. These are intended to run on screens on the linux work station but wherever they are ran icav2 must already be installed and configured on that system.

## USAGE

### MiSeq_runs_basespace.sh

MiSeq_runs_basespace.sh checks basespace every 20 minutes for a new MiSeq sequencing run. This is the script that is run in a screen on the Production account.

```
MiSeq_runs_basespace.sh
```
The commands included in this script
```
# getting a list of all the completed runs (including the run id)
bs list --config=$user runs

# checking if that run is already in `/Volumes/IDGenomics_NAS/WGS_Serotyping/$run_name`

# listing all the files for this run
bs list dataset --config=$user --input-run=$run_id

# downloading these files with bs-cli (can also be done on the basespace website)
bs download dataset --config=$user --id=$sample --output="/Volumes/IDGenomics_NAS/WGS_Serotyping/$run_name/Sequencing_reads/Raw" --retry

# uploads these fastq files to ICA
icav2 projects enter Testing 
echo y | icav2 projectdata upload /Volumes/IDGenomics_NAS/WGS_Serotyping/$run_name/Sequencing_reads/Raw /$run_name/

# running Grandeur
nextflow run UPHL-BioNGS/Grandeur -profile uphl --reads /Volumes/IDGenomics_NAS/WGS_Serotyping/$run_name/Sequencing_reads/Raw -r main -with-tower -dsl1
```

### daily_SARS-CoV-2_metadata.sh

daily_SARS-CoV-2_metadata.sh checks the date every 4 hours. If it is a new day, this script runs the Dripping Rock nextflow workflow to get the daily SARS-CoV-2 metadata file. On Sundays, it also takes the latest 20 runs and 10 random runs and creates a phylogenetic tree. This is a script that is run in a screen on the Production account.

```
daily_SARS-CoV-2_metadata.sh
```

The commands included in this script
```
# creating a new directory and entering that directory
mkdir /Volumes/IDGenomics_NAS/NextStrain/$current_date
cd /Volumes/IDGenomics_NAS/NextStrain/$current_date

# running dripping rock
nextflow /home/Bioinformatics/Dripping_Rock/metadata/nextstrain_metadata.nf -with-tower -dsl1

# Sunday
nextflow /home/Bioinformatics/Dripping_Rock/metadata/nextstrain_metadata.nf -with-tower -resume --msa true -dsl1
```

### auto_Granduer_ICA.py
auto_Granduer_ICA.py 

```
python auto_Granduer_ICA.py
```
The commands included in this script
```
# starting ICA
icav2 projects enter Testing
# observing what is already there
icav2 projectdata list --file-name UT-M03999-,UT-M07101-,UT-M70330-,UT-FS10001397-  --parent-folder / --match-mode FUZZY
# starting grandeur on ICA
icav2 projectpipelines start nextflow UPHL-BioNGS_Granduer_V2 --input reads:$ica_id \
  --input project_dirs:fol.fb0091ef9e4d4e515b6408da63045a75,fol.90b6b7865bc7434384e408da6377c840,fol.8802646a4148485884df08da6377c840,fol.17212ac619d44b68296008da58d44868,fol.ae742e54d4a54a8acb9c08da64f9d308,fol.97c3321c555a4b1c672f08da58d44868 \
  --user-reference %s_Granduer_Analysis" % run_name
```

Note: MiSeq_runs_basespace.sh uploads data into ICA; so if the script fails you need to know the name of the sequencing run, i.e UT-M70330-220712. Log into ICA and go to the Testing project (once the script runs around 5 times, we should move this to the Production project). Navigate to the Flow dropdown found on the left of the UI, then click pipelines. Click to highlight "UPHL-BioNGS_Granduer_V2", then click the purple "Start New Analysis" above. Provide the user reference as the sequecning run plus '_Granduer_Analysis', i.e. UT-M70330-220712_Granduer_Analysis. Then under "Input Files" click the purple select button under "Reads". Then find and select the sequencing run name then go one directory down to Raw. As an example path this would be "/UT-M70330-220712/Raw". Then under "PROJECT_DIRS FROM EDITED GIT REPO" click select, then you will click the folder "Grandeur_for_ICA_pods". Then select all folders in this directory; subworkflows, data, modules, and configs. You also need to reclick the select button and include the directories blast_db_refseq and kraken2_db. Now you can start the run by clicking in the upper right the purple box that says "Start Analysis". To check on the progress of Analyses navigate to the flow dropdown found on the left of the UI, then click Analyses.

### auto_mycosnp_ICA.py
auto_mycosnp_ICA.py takes the fastq files from the Illumina after BSSH creates FASTQ files. The automation script runs each time these files make their way to ICA. It produces the samplesheet, including control samples, needed for the analysis and uploads it to ICA. It then starts the analysis.
```
python auto_mycosnp_ICA.py
```
The commands included in this script
```
# finding completed runs
icav2 projectdata list --data-type FOLDER --file-name app.* --match-mode FUZZY
# download the json for this run
icav2 projectdata list --data-type FILE --parent-folder %s --file-name bsshinput.json" % (run)
icav2 projectdata download %s" % download
# create a sample sheet
TBA
# setting up ICA
icav2 projects enter Testing
# estabilishing the C. auris controls
TBA
# link samples to the project
icav2 projectdata link %s" % sams.split(',')[i]
# upload the sample sheet
icav2 projectdata upload ./%s_samplesheet
icav2 projectdata list --data-type FILE --parent-folder /%s_samplesheet/ --file-name samplesheet.csv
# something with ICA (please change)
icav2 projectdata list --parent-folder /Candida_auris_clade_controls/Raw/
icav2 projectpipelines start nextflow CDC_mycosnp_V1_3 --input input_samples: \
.... insert what this command looks like ...
  --input input_csv:samplesheet \
  --input modules_json:fil.59d555e385bc44373e0508da602cff6c --input schema_json:fil.67a59465102f49653e0b08da602cff6c --input project_dirs:fol.9f7bb648f8b14ad1bd5908da602d9944,fol.1c6b76e2679e46a5bd5708da602d9944,fol.4c3975313355455e3e0708da602cff6c,fol.df431f633c8a405b3db608da602cff6c,fol.a0755943991b4b713d9f08da602cff6c,fol.287f4196a2574a77346f08da603e530e,fol.de2553cf82f74a103d8c08da602cff6c,fol.8bb8690a65d8459e3d5608da602cff6c,fol.08cbd7c3121a4b503dd008da602cff6c --input fasta:fil.a582dffcf93846d6f72908da19bdaa25 \
   --user-reference CDC_mycosnp_V1_3_%s_update
```

### Known Issues
1. Sometimes analyses fail on ICA and I need to work out the best way to restart these runs. This most likely in-tells releasing pipelines on ICA and moving each scrip from running in Testing to Production projects; which should only happen after we have some evaluation of these scripts.
2. Currently no downloading has been automated in the scripts. I need to clarify with bioinformaticians what needs to be downloaded and I think version control would be easier with creating scripts that are different then the ones starting analyses.
