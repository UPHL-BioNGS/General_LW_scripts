# ICA Automation Scripts
These scripts are intened to make the running of analyses on ICA for production purposes automated as well as downloading the most common files that need to be reviewed by human eyes. Each is written in python and uses the icav2 command line tool provided by Illumina. These are intened to run on screens on the linux work station but whereever they are ran icav2 must already be installed and configured on that system.

# mycosnp
Currently this pipeline is only ran on C. auris sampels. These samples are usually uploaded directly by the Illumia instrument after BSSH calls the reads into ICA.
The automation script runs each time these file make there way to ICA. It produces the samplesheet, including control samples, needed for the analysis and uploads it to ICA. It then starts the anaylsis

# Grandeur
We currently upload sequncing runs that use granduer using the General_LW_scripts/MiSeq_runs_basespace.sh. This script looks for those uploads then sees if they have already had anaylsis preformed on ICA. If not they start that anaylsis.

# Known Issues
1. Sometimes analyses fail on ICA and I need to work out the best way to restart these runs. This most likly intells releasing pipelines on ICA and moving each scrip from running in Testing to Production projects; which should only happen after we have some evaulation of these scripts.
2. Currently no downloading has been automated in the scripts. I need to clarify with bioinformaticains what needs to be downloaded and I think version control would be easier with creating scripts that are different then the ones starting analyses.
