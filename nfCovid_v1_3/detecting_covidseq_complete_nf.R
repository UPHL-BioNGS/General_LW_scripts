#!/usr/bin/env Rscript
# Author: OLP/12/2023
# Usage: Trigger the Dripping_Rock work flow.
# last modified on 23/12/28 "YY-MM-DD"

setwd("/Volumes/NGS")library(stringr)
while(TRUE) {
path1<-"/Volumes/NGS/Analysis/covidseq"
Lyapunovv<- Sys.glob(paste(path1,"*/covidseq_complete_nf.txt",sep = "/"),dirmark = TRUE); Lyapunovv
if(length(Lyapunovv) ==0){ Lyapunovv<-"Chaos_Theory"}
Lyapunovv
if (file.exists(Lyapunovv)) {
   select_part <- str_extract_all(Lyapunovv, "(?<=/)[^/]+")[[1]];  covid_run<-select_part[5]; 
   cat("The analysis phase for run",covid_run, "has ended, the nfCovid workflow will be triggered", "\n")
   nextflow_script<- paste("nextflow run","/Volumes/IDGenomics_NAS/Bioinformatics/olinto/testing_nfCovid/nfCovidFiles/nfCovid.nf"," --paramito",covid_run ,sep =" ")
   system(nextflow_script)

   # Rename the trigger  file: covidseq_completed_nf.txt to nfCovid_workflow_complete.txt"
    Lyapunovv2<-paste("/Volumes/NGS/Analysis/covidseq",covid_run,"nfcovid_workflow_completed.txt",sep="/");
    file.rename(Lyapunovv, Lyapunovv2)
   
  } else {

cat('\n')
cat("\033[1mRunning nfCovid.nf in the background: Everything is completed, nothing to do for now\033[0m\n")
  

}

cat("\033[1;31mSleeping for 2 minutes...\033[0m\n")
Sys.sleep(2*60)
}

