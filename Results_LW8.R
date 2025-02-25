#!/usr/bin/env Rscript
# Author: OLinares-Perdomo
# Usage: Results.txt file for LW8 (The ParFastas script and Cecret-wf must be executed before)
# Parameter: Run Name ;  i.e. Combining_Results.R UT-VH0770-250110
# last modified on 2025-01-15

library("data.table");library("dplyr");library("utils");
library("lubridate");find("read.table");library("readr"); 

config<-read_yaml("config.yml")
base_path<-config$paths$covidseq_base
base_path
    args = commandArgs(trailingOnly=T);
# detecting sequencer type (VH00770, VH01885 or A01290)
    if(nchar(args[1])==17){date<-ymd(substr(args[1], 12, 17))} else{date<-ymd(substr(args[1], 11, 16))};
    runPath <-paste(base_path,args[1],sep="/");

  # reading the SampleSheat
    df1 = read.csv(paste(runPath,"covidseq_output/Logs_Intermediates/SampleSheetValidation/SampleSheet_Intermediate.csv" ,sep = "/"));
    x = apply(df1,1, function(x) {any(grepl(x, pattern = "Patient")|grepl(x, pattern = "UT-UPHL")) });
    Matrix1<-as.data.frame(cbind((cbind(df1[x, ][,c(1)],df1[x, ][,c(3)])),"run name"=args[1]));
# getting results from Cecret wf
    Matrix2<-read.csv(paste(runPath,"CecretPangolin/cecret_results.csv",sep ="/"))[,c("sample","pangolin_lineage","nextclade_clade","num_total")]
# Merging ss and resuts from Cecret
    results<-merge(Matrix1,Matrix2, by.x="V1", by.y= "sample", all.x=T);
    colnames(results)<-c("LIMS_TEST_ID","Submission ID","Run Name","Lineage","Nextclade clade","Non-Ambiguous Bases");
    results$Lineage[is.na(results$Lineage)]= "Not able to be sequenced"
    results$"Nextclade clade"[is.na(results$"Nextclade clade")]= "Clade not detected"
    results$"Non-Ambiguous Bases"[is.na(results$"Non-Ambiguous Bases")]= "0"
# ordering
    results<-results %>%  select(LIMS_TEST_ID, "Run Name","Submission ID","Non-Ambiguous Bases","Nextclade clade","Lineage"); 
# saving results
    write.table(results,paste("/Volumes/NGS/Analysis/covidseq/",args[1],"/",args[1],
                           "FinalResults.txt",sep=""), sep = ',', row.names = F, col.names = T, eol="\r\n", quote = F)
  
   write.table(results,paste("/Volumes/NGS/Analysis/covidseq/",args[1],"/",args[1],
                            "FinalResults.csv",sep=""), sep = ',', row.names = F, col.names = T, eol="\r\n", quote = F)

