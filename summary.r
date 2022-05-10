#!/usr/bin/env Rscript
# Author: OLP/2022
# Usage: summary for SARS-CoV-2 run, only for PatientSamples, input: one parameter
# ie. Rscript /. . . ./summary.r UT-A01290-220416
library("plyr", warn.conflicts = F)
library("dplyr", warn.conflicts = F)
library("rbin")#
library("tidyverse")
library("lubridate", warn.conflicts = F)
library("tibble")
library("stringr") 
require("seqinr"); 
library("XML")
#===============================================
args = commandArgs(trailingOnly=T)
# args[1]<-c('UT-A01290-220416'); # only to works on script preparation
date<-ymd(substr(args[1], 11, 16));runPath <-paste('/Volumes/NGS/Analysis/covidseq',args[1],sep="/"); head(date)

#=============================================
ss1 = paste(runPath,"covidseq_output/SampleSheet_Intermediate.csv",sep ="/"); 
ss2 = paste(runPath,"covidseq_output/lineage/combined_lineage_report.csv",sep ="/"); 
ss3 = paste(runPath,"covidseq_output/Logs_Intermediates/VirusDetection/kmer/Summary.tsv",sep ="/");
ss5 = paste(runPath,"covidseq_output/Logs_Intermediates/FastqGeneration/Reports/RunInfo.xml",sep ="/");
df1 = read.csv(ss1); # SampleSheet
df2 = read.csv(ss2); # combined_llineage_report
df3 = read.table(file = ss3, sep = '\t', header = T); # sc2_amplicons 

#=============================================
# collectin basic info from samplesheet
t<-.5;
instrument_type<-df1[4,2];cat("instrument_type:", instrument_type,"\n");Sys.sleep(t)
wetlab_assay<-df1[5,2]; cat("wetlab_assay:", wetlab_assay,"\n");Sys.sleep(t)
pangolin_version<-df2[1,9];cat("pangolin_version :",pangolin_version,"\n");Sys.sleep(t)
pangoLEARNversion<-df2[1,8];cat("pangoLEARNversion :",pangoLEARNversion,"\n");Sys.sleep(t)
software = "Illumina DRAGEN COVID pipeline (R.U.O.), vs. 1.0.1"; cat("software: ",software,"\n");Sys.sleep(t)
lineage_tools = "Dragen-covid-lineage-tools, vs. 1.1.0.0"; cat ("Lineage tools: ",lineage_tools,"\n");Sys.sleep(t)

#=============================================
# selecting sample type: PatientSample
df1<-tail(df1,-13);
df1<-df1[,c(1,3)]; 
colnames(df1) <- c("Sample_Accession","Sample_Type");
df1<-filter(df1, Sample_Type == "PatientSample"); 
n<-length(df1$Sample_Type); cat("Number of PatientSamples",n,"\n");Sys.sleep(t)

#=========================================
# Random number for the Sample_ID
RNG<-paste(floor(runif(n, min=99, max=1000)),floor(runif(n, min=99, max=1000)),sep =""); 
IDD<-paste("UT-UPHL",substr(args[1], 11, 16),sep="-");
Sample_ID<-paste(IDD,RNG,sep=""); 
summary1<-cbind(df1,Sample_ID);
#============================================
#left join SampleSheet and Combined Lineage Report
var <-paste('',args[1],sep='-'); head(var)
df2 <-df2 %>% mutate_at("taxon", str_replace, var, "")
df2<-df2[,c("taxon","lineage","scorpio_call")]
head(df2); #Taxon, lineage, scorpio_call
df3 = read.table(file = ss3, sep = '\t', header = TRUE); # 
df3<-df3 %>% mutate_at("Sample", str_replace, var, ""); head(df3)
df3<-df3[,c("Sample","nTargetsDetected.SARS.CoV2")]; 
colnames(df3)[2] <- 'sc2_amplicons';#
summary1<-merge(summary1,df2, by.x="Sample_Accession", by.y= "taxon", all.x=TRUE); 
head(summary1)
summary1<-merge(summary1,df3, by.x="Sample_Accession", by.y= "Sample", all.x=TRUE);
head(summary1)
#==========================================
# adding basic information: 
summary1<-cbind(summary1,'wetlab_assay'= wetlab_assay,"instrument_type"=instrument_type,"software"=software,"lineage_tools"=lineage_tools,
                "pangolin_version"=pangolin_version)

#========================================
# computing num of actg and num of n
num_actgx<-vector();num_nx<-vector(); 
runPath1 = paste(runPath,"covidseq_output/Sample_Analysis/",sep ="/"); 
num_actgx = 0; num_nx = 0;
for (i in 1:n){ ## n : number of samples
     sample=summary1$Sample_Accession[i]; 
     amplicons=summary1$sc2_amplicons[i];#amplicons
      if(amplicons >=50)
      { 
        Lyapunovv<- Sys.glob(paste(runPath1,sample,"*/*.fasta",sep = ""),dirmark = TRUE); 
        a =  str_count(read.fasta(Lyapunovv, as.string = T, forceDNAtolower = T), pattern = "a|c|t|g");num_actgx[i] = a;
        b =  str_count(read.fasta(Lyapunovv, as.string = T, forceDNAtolower = T))-a; num_nx[i] = b;
      }
   else { # AmpliconThereshold <50, no fasta file
         a = b =0;
         num_actgx[i] = 0; num_nx[i] = 0; 
        }
    i = i+1;
    cat(sample," \t",a,"\t",b,"\n")
    }

df_new <- cbind(as.character(num_actgx), as.character(num_nx)); 
summary<-cbind(summary1,df_new); 
colnames(summary)[12]<-("num_actg");colnames(summary)[13]<-("num_n")

d=paste(runPath,'R-sumcovidseq',sep="/");
dir.create(file.path(d), recursive = TRUE)
write.csv(summary,paste(d,'covidseq_summary.csv',sep="/"),row.names=FALSE)
