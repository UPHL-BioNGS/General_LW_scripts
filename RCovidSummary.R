#!/usr/bin/env Rscript
# Author: JLinares/2022
# Usage: 1. analysis summary for PatientSamples: Two files are generated: Summary and RunParameters
#        2. Arguments: run name
#        3. Example: Rscript RCovidSummary.R UT-A01290-220901
#        4. Connditions/precautions:
#           a: Analysis completed and Cecret/Lineage_report.csv completed before running this script
#           b: The samplesIds, generated using a Randon Number Generator, will be differents everytime this sctript is ran.
#        5. The two generated files will be stored at the runPath/Rsumcovidseq folder. ie: /Volumes/NGS/Analysis/covidseq/runName/Rsumcovidseq

library("easypackages");libraries("XML","xml2","seqinr","data.table")
sup <- suppressPackageStartupMessages
sup(library(lubridate))
sup(library(tidyverse))

args = commandArgs(trailingOnly=T)
date<-ymd(substr(args[1], 11, 16));runPath <-paste('/Volumes/NGS/Analysis/covidseq',args[1],sep="/")
df1 = read.csv(paste(runPath,"covidseq_output/SampleSheet_Intermediate.csv",sep ="/"))
df2 = read.csv(paste(runPath,"CecretPangolin/pangolin/lineage_report.csv",sep ="/"))
df3 = read.table(file = paste(runPath,"covidseq_output/Logs_Intermediates/VirusDetection/kmer/Summary.tsv",sep ="/"), sep = '\t', header = T); 
#=============================================
# Info parameters about the run:
Sequencer <-substr(args[1], 4, 4); dat<-substr(args[1], 11, 16);
if (Sequencer =="A"){ TypeOfSequencer<-"NovaSeq";Pt<-"A01290"} else {TypeOfSequencer<-"NextSeq";Pt<-"NB551133"};
instrument_type<-df1[4,2];chemistry<-df1[7,2];index_adapters<-df1[6,2];wetlab_assay<-df1[5,2];pangolin_version<-df2[1,10]
software = "Illumina DRAGEN COVID pipeline (R.U.O.) version 1.0.1";# <===Where can it be found
pathOutput <-paste("/Volumes/NGS/Output/",Pt,"/",dat,"*/RunParameters.xml",sep='')

fileName<-Sys.glob(pathOutput,dirmark = TRUE);
ReadType<-xmlToDataFrame(nodes=getNodeSet(xmlParse(read_xml(fileName)),"//ReadType"))
ReadLength<-xmlToDataFrame(nodes=getNodeSet(xmlParse(read_xml(fileName)),"//Read1NumberOfCycles"))
df1<-tail(df1,-13);df1<-df1[,c(1,3,12)];colnames(df1) <- c("Sample_Accession","Sample_Type","lanes");Nlanes<-length(unique(df1[3])$lanes)
df1<-filter(df1, Sample_Type == "PatientSample"); n<-length(df1$Sample_Type)
#=============================================
# Run parameters
RunPar <- data.frame("","");colnames(RunPar)<-c("Parameters","Info");
RunPar[1,1]<-"Wetlab assay";RunPar[2,1]<-"Instrument type";RunPar[3,1]<-"Software";RunPar[4,1]<-"Pangolin version";RunPar[5,1]<-"Read type";
RunPar[6,1]<-"Read length";RunPar[6,1]<-"Number of samples";RunPar[7,1]<-"Number of lanes";RunPar[8,1]<-"Chemistry";RunPar[9,1]<-"index adapters";
RunPar[10,1]<-"Date of the run"
RunPar[1,2]<-wetlab_assay;RunPar[2,2]<-instrument_type;RunPar[3,2]<-software;RunPar[4,2]<-pangolin_version;
RunPar[5,2]<-ReadType;RunPar[6,2]<-n;RunPar[7,2]<-Nlanes;RunPar[8,2]<-chemistry;RunPar[9,2]<-index_adapters;RunPar[10,2]<-as.character(date)
RunPar
#=============================================
# Random Number Generator for Sample_IDs
RNG<-paste(floor(runif(n, min=99, max=1000)),floor(runif(n, min=99, max=1000)),sep ="")
# Checking for duplicates in RNG
while(length(RNG)!= length(unique(RNG)))
     { RNG<-paste(floor(runif(n, min=99, max=1000)),floor(runif(n, min=99, max=1000)),sep ="");}
IDD<-paste("UT-UPHL",substr(args[1], 11, 16),sep="-")
Sample_ID<-paste(IDD,RNG,sep="")
summary1<-cbind(df1,Sample_ID)

#============================================
#join tables: SampleSheet & Combined Lineage Report
var <-paste('',args[1],sep='-');
df2 <-df2 %>% mutate_at("taxon", str_replace, var, "")
df2<-df2[,c("taxon","lineage","scorpio_call")]
df3<-df3 %>% mutate_at("Sample", str_replace, var, "")
df3<-df3[,c("Sample","nTargetsDetected.SARS.CoV2")]
colnames(df3)[2] <- 'sc2_amplicons';#
summary1<-merge(summary1,df2, by.x="Sample_Accession", by.y= "taxon", all.x=TRUE)
summary1<-merge(summary1,df3, by.x="Sample_Accession", by.y= "Sample", all.x=TRUE)

#==========================================
# Nucleotides count: (actg & n)
num_actgx<-vector();num_nx<-vector(); pass_fail<-vector()
runPath1 = paste(runPath,"covidseq_output/Sample_Analysis/",sep ="/")
num_actgx = 0; num_nx = 0;
for (i in 1:n){
     sample=summary1$Sample_Accession[i]
     amplicons=summary1$sc2_amplicons[i]
     if(amplicons >=50)
          {
           Lyapunovv<- Sys.glob(paste(runPath1,sample,"*/*.fasta",sep = ""),dirmark = TRUE)
           a =  str_count(read.fasta(Lyapunovv, as.string = T, forceDNAtolower = T), pattern = "a|c|t|g");num_actgx[i] = a
           b =  str_count(read.fasta(Lyapunovv, as.string = T, forceDNAtolower = T))-a; num_nx[i] = b; pass_fail[i] ="pass"; c = "pass"
           }
     else {# AmpliconThereshold <50,
          a = b =0; num_actgx[i] = 0; num_nx[i] = 0; pass_fail[i] ="fail"; c = "fail"
          }
  cat(sample," \t",a,"\t",b,"\t",c,"\n")
  }

df_new <- cbind(as.character(num_actgx), as.character(num_nx),pass_fail)
summary<-cbind(summary1,df_new);
summary<-summary %>% rename(sc2_amplicons = 7, num_acgt = 8, num_n = 9)
#========================================
# storing files
d=paste(runPath,'Rsumcovidseq',sep="/");dir.create(file.path(d,"" ), recursive = TRUE); p1<-Sys.time()
dx<- paste(d,'/Rcovidseq_summary-',paste0(Sys.Date(),'-',hour(Sys.time()),'-',minute(Sys.time()),'-',second(Sys.time())),".csv",sep=""); 
write.csv(summary,dx,row.names=FALSE)
dx<- paste(d,'/RunParameters-',paste0(Sys.Date(),'-',hour(Sys.time()),'-',minute(Sys.time()),'-',second(Sys.time())),".csv",sep=""); 
write.csv(RunPar,dx,row.names=FALSE)
cat("Summary & run rarameters files are complete and can be found at: ",d,"\n")
