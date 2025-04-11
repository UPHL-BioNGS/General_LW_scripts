#!/usr/bin/env Rscript
# Author: OLP/01/2022
# Usage: sending results to Tracking/Finished tape
# Parameter: Run Name ;  i.e. Rscript ActualizingTrackingFinishedTap.R UT-VH077-230822
# last modified on 08-28-23

#library("easypackages");libraries("grid","data.table","progress","XML","xml2","seqinr","data.table","readr","gargle","googlesheets4")
library("grid")
library("data.table")
library("progress")
library("XML")
library("xml2")
library("seqinr")
library("data.table")
library("readr")
library("gargle")
library("googlesheets4")



   args = commandArgs(trailingOnly=T); 
   args[1]<-c("UT-VH00770-250214") # for testing
   runPath <-paste('/Volumes/NGS/Analysis/covidseq',args[1],sep="/")
   runPath
   sup <- suppressPackageStartupMessages; sup(library(lubridate)); sup(library(gargle));
   runPath <-paste('/Volumes/NGS/Analysis/covidseq',args[1],sep="/")
# getting the token
   tokenPar <- readRDS("/Volumes/NGS/Bioinformatics/Lin/secrets/7a6077d23f6776ccc63f8f70bc12b214_olinares-perdomo@utah.gov")
   gs4_auth(token = tokenPar)
 # accessing SASR-COV-2 NGS Tracking/Finished tab
   page<-"https://docs.google.com/spreadsheets/d/1N_d2V6XESUeGTlb-uJIe_yPkHBe5qqXLFWWXY86wJZU/edit#gid=572325282"
 
# Accessing results from Rsumcovidseq
   NGS_Tracking<-rownames(fileSnapshot(paste(runPath,"Rsumcovidseq/",sep="/"),
                                    pattern=glob2rx("NGS_Tracking*.csv"))$info[which.max(fileSnapshot(paste(runPath,"Rsumcovidseq/",sep="/"),
                                                                                                      pattern=glob2rx("NGS_Tracking*.csv"))$info$mtime),])
   
   NGS_Tracking
   head(NGS_Tracking)
   RunResults<-read.csv(paste(paste(runPath,"Rsumcovidseq/",sep="/"), NGS_Tracking,sep = "/"), header = T)
   head(RunResults)
   
   # need to add submisison id from clarity
   ####### new
   Clarity<-read.csv(paste("/Volumes/NGS/Analysis/covidseq/",args[1],"/",args[1],"Results.csv",sep =""))
   # paste("/Volumes/NGS/Analysis/covidseq/",args[1],"/",args[1],"Results.csv",sep ="")
   # paste("/Volumes/NGS/Analysis/covidseq/",args[1],"/",args[1],"Results.csv",sep ="")
   head(Clarity)
   #Clarityy<-data.frame(Clarity$LIMS_TEST_ID, Clarity$Submission.ID); 
   #head(Clarityy)
   
   #summary_Clarity<-merge(summary,Clarityy,by.x = "SampleNumber", by.y = "Clarity.LIMS_TEST_ID", all.x = T);
   #head(summary)
   
   #summary_Clarity$Sample_ID<-NULL
   #head(summary_Clarity,2)
   #ss<-summary_Clarity[c("SampleNumber","Clarity.Submission.ID","lineage","scorpio_call","sc2_amplicons","clade","collectionDate","num_actg","num_n","pass_fail","Nume_reads","Mean_Quality_Score","Run Name")]
   #colnames(ss)[colnames(ss) == "Clarity.submission.ID"]<-"Sample_ID"
   #summary<-ss;
   
   ####### end new
   
   
   
   ## adding coverage to the tracking system
   #Spike_coverage<-read.csv(paste(runPath,paste(args[1],"S-protein-meandepth_coverage.csv",sep="_"),sep  = "/")); 
   #head(Spike_coverage)
   #RunResults<-merge(RunResults,Spike_coverage, by.x="SampleNumber", by.y= "Sample", all.x=T)
   #RunResults <- RunResults[, -which(names(RunResults) == "X")]; 
head(RunResults)
head(Clarity)
Rresults<-merge(RunResults,Clarity,by.x = "SampleNumber", by.y = "LIMS_TEST_ID", all.x = T )    
head(Rresults)
#RunResults<-Rresults[,c("SampleNumber", "Submission.ID", "collectionDate","Run.Name.x","lineage","num_actg","clade")];head(Rresults2)

#summary_Clarity<-merge(summary,Clarityy,by.x = "SampleNumber", by.y = "Clarity.LIMS_TEST_ID", all.x = T);
 # col_names<-c("Lab ID","Submission ID","Collection Date","Sequencing run","Pangolin Lineage (updated 2021-08-10)","Number of non-ambiguous bases","Clade")
 #  colnames(RunResults)<-col_names;
 
# adding new data to SARS-CoV-2 NGS Tracking/Finished tap  
   sheet_id<-page
   sheet_append(sheet_id, data = RunResults)
   cat(crayon::bold(nrow(RunResults), "columns have been added to SARS-CoV-2 NGS Tracking/Finished sheet ralated to run",args[1],"\n"))

  
