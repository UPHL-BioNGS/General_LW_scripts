# General_LW_scripts
The scripts that UPHL uses to download things from basespace and run respective workflows

# USAGE

## daily_SARS-CoV-2_metadata.sh

daily_SARS-CoV-2_metadata.sh checks the date every 4 hours. If it is a new day, this script runs the Dripping Rock nextflow workflow to get the daily SARS-CoV-2 metadata file. On Sundays, it also takes the latest 20 runs and 10 random runs and creates a phylogenetic tree. This is a script that is run in a screen on the Production account.

## accession_for_clarity.py

accession_for_clarity.py is a script that creates an accessioning file for Clarity that has the new samples found in the Labware lims system that will be ready for the lab to process. The output of the script is a csv file, that must be saved as an excel file before Clarity will accept it. To be able to run the script you must have these two servers mounted on your computer; smb://172.16.109.9 and smb://168.180.220.43 or //LABWARE/ and ///DDCP/UPHL/. You also need to log into Clarity and download all samplesheets from projects with a name that starts with COVIDSeq, including the project COVIDSeq_From_TEST_DO_NOT_PUT_IN_WORKFLOW. Do this by going to the 'Projects and Samples' tab, choosing the correct project, and clicking the modify samples button. This will insure we do not place duplicates in Clarity which causes many issues.

![alt text](images/Clarity_projects_modify.png)

Files will be downloaded from clicking the modify samples button. 

Now to run the script ```python accession_for_clarity.py "path/to/files/fromclarity" "path/to/files/fromclarity.etc"``` ...

The csv file that the script creates will be saved to the directory that you are running the script from. You must open the file in excel and save it to the excel file. Now back in Clarity click the button 'Upload Sample List' and choose the excel file.

![alt text](images/Clarity_projects_to_workflow.png)

Now click select group for the samples you just uploaded. Then choose 'Covidseq v1.0' after clicking 'Assign to Workflow'. And finally you are done!

# Automation Scripts for ICA 
Currently written for Pulsenet/ARLN samples that typically run on Grandeur and Mycosnp. The scripts are structured to run sequentially; and can be triggered manually or by the previous script. Each script send notifications to the UPHL slack channel to help monitor the progress of the sequencing analysis. These scripts use the python package of logging to track these scripts usage and track errors that occur while running. All scripts write to a log located at /Volumes/IDGenomics_NAS/Bioinformatics/jarnn/analysis_for_run.log.
![alt text](images/ICA_automation.jpg)

## analysis_for_run.py
This script is written to run continuously on the Linux workstation on a screen. It's main purpose is to use the ```bs``` or "The BaseSpace Sequence Hub CLI tool" to look for new sequencing runs starting on any of the sequencers. It uses a .txt file called 'experiments_done.txt' to record which sequencing runs it has already seen. Once it has identified the new run; it will use the Clarity API to find which species are among the samples. The script will then open a new screen and start the next script ```screen_run.py```. If it was able to find the run on Clarity it will provide an argument for the run type; currently either mycosnp or grandeur. 

```
USAGE: Run this on a screen. It is an infinite loop and looks for new runs.

EXAMPLE: python3 analysis_for_run.py
```

## screen_run.py

This script is written to run on a screen named after a sequencing run and will end the screen once it has completed. This script can take two arguments. The first argument is the run name and is required. The second is the type of analysis, either mycosnp or grandeur, which is optional but limits the functionality of the script to only Slack messaging. The main purpose of this script is to monitor runs until they finish using ```bs``` or "The BaseSpace Sequence Hub CLI tool". If an analysis type is given it will call three other scripts that will download the reads ```download_reads.py```, start an anaylsis on ICA ```auto_mycosnp_ICA.py``` or ```auto_granduer_ICA.py```, monitor the run on ICA ```monitor_ica.py``` and download the analysis files from ICA.

```
EXAMPLE:
python screen_run.py UT-VH0770-220915 mycosnp
```

## download_reads.py

This script is written to download reads from BSSH into the NAS. It takes two required arguments. The first is the run name and the second is the analysis type. Depending on analysis type they will be downloaded into /WGS-serotyping/ or /fungal/. If a folder already exists this script will not run.

```
EXAMPLE:
python download_reads.py UT-VH0770-220915 mycosnp
```

## auto_mycosnp_ICA.py

This script will create a samplesheet, upload the samplesheet to ICA, collect needed ICA ids to start a pipeline analysis,
build the icav2 command to start, and then start the analysis. If analysis fails to start; use the icav2 arg that is created,
then use icav2 manually to troubleshoot issue. Most likely: icav2 config incorrectly; IDS incorrect; IDS not linked to project; syntax issue with command. An optional 2nd argument can be included that will add to the ICA User Reference for the analysis. It is recommended if an ICA analysis has already been tried. Having the same User Reference can give ICA problems.

```
EXAMPLE:
python auto_mycosnp_ICA.py UT-VH0770-220915
```

## auto_granduer_ICA.py

This script will collect needed ICA ids to start a pipeline analysis; build the icav2 command to start, and then start the analysis.
If analysis fails to start use the icav2 arg that is created, then use icav2 manually to troubleshoot issue.
Most likely: icav2 config incorrectly; IDS incorrect; IDS not linked to project; syntax issue with command. An optional 2nd argument can be included that will add to the ICA User Reference for the analysis. It is recommended if an ICA analysis has already been tried. Having the same User Reference can give ICA problems.

```
EXAMPLE:
python auto_mycosnp_ICA.py UT-VH0770-220915
```

## monitor_ica.py
The main purpose of this script is to monitor an ICA analysis until they finish using ```icav2``` or "Command line interface for the Illumina Connected Analytics". This script has two required arguments and one optional argument. The first argument is the run name, the second is the project on ICA which the analysis is running on, and the third is the the analysis type. If analysis type is given the script ```download_ica.py``` will be called when the run is finished.
 
```
EXAMPLE:
python monitor_ica.py UT-VH0770-220915 Testing mycosnp
```

## download_ica.py
This script is written to download analysis files from ICA to the NAS. It takes two required arguments. The first is the run name and the second is the analysis type. Depending on analysis type they will be downloaded into /WGS-serotyping/ or /fungal/. 

```
EXAMPLE:
python download_ica.py UT-VH0770-220915 mycosnp
```

## long_read_seq/Unicycler_ICA.sh

This script is to just run Unicycler on samples that have both Nanopore and Illumina reads. This script requires several things:
1. That icav2 is configured for the user
2. gnu parallel is installed and running
3. That the user is currently in the directory of the nanopore run
4. That the user has created a sample sheet file for Donut Falls

This script will enter ICA's Testing Project, upload nanopore and illumina reads to a directory specified by the first position, and manage files found in the sample sheet in the second position. It will then (hopefully) start Unicycler on ICA after the files are finished uploading.

```
EXAMPLE:
bash long_read_seq/Unicycler_ICA.sh UT-GXB02179-230317 sample_sheet.csv
```
