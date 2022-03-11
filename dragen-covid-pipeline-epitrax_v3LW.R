#!/usr/bin/env Rscript
# Author: OLP/01/2022
# Usage: Getting metadata
# Parameters: Only one: Run Name i.e. Rscript / . . . ./dragen-covid-pipeline-epitrax-v2.R UT-A01290-220113

library("dplyr", warn.conflicts = FALSE)
library("grid")
library("rbin")#
library("tidyverse")
library("lubridate", warn.conflicts = FALSE)
library("tibble")

# Step 1: date from argument
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
args = commandArgs(trailingOnly=TRUE)
#args[1]<-c('UT-A01290-220304'); # only to works on script preparation
s<- paste('/Volumes/NGS/Analysis/covidseq/',args[1],sep="/"); head(s)
ss<-gsub("\\.*.*/","", s);date<-ymd(substr(ss, 11, 16)); head(ss); head(date)

# Step 2: Reading covidseq_summary
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
loc<-paste(paste('/Volumes/NGS/Analysis/covidseq',args[1],sep="/"),"sumcovidseq",sep ="/"); head(loc)
covidseq_summary<-read.csv(paste(loc,"covidseq_summary.csv", sep="/"));
covidseq_summary<-covidseq_summary[,c(1,9)]; colnames(covidseq_summary)[2] <- 'Test result';#  sample and pangolin_lineage


# Step 3: Selecting only PatientSamples from the SampleSheet
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Empy weels. 
# The SampleSheet was modified on 2022-02-26 where Empty well is callep as Empty but if this
# script is used for data before that the script filter the Empty well in the following lines
sample<-covidseq_summary$sample; sample<-gsub("\\Emp.*","", sample);
covidseq_summary$sample<-sample

loc2 <-paste("/Volumes/NGS/Analysis/covidseq",args[1],sep="/"); head(loc2)
SampleSheet<-read.csv(paste(loc2,"covidseq_output/SampleSheet_Intermediate.csv", sep="/"));
ss1<-tail(SampleSheet,-13);#ss : SampleSheet
ss<-ss1[,c(1,3)]; # selecting sampleNumber and PatientSample
colnames(ss) <- c("Sample_Accession","Sample_Type");
ss<-filter(ss, Sample_Type == "PatientSample"); 
# inner join
covidseq_summary_filtered<-merge(ss,covidseq_summary, by.x="Sample_Accession", by.y= "sample")
covidseq_summary_filtered<-covidseq_summary_filtered[,c(1,3)]
head(covidseq_summary_filtered)

#Step 4: Detecting last files from NAS: NGS_Covid_...*csv & All_ncovid_NoNGS...*csv files
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
tmpshot <- fileSnapshot("/Volumes/IDGenomics_NAS/NextStrain/EpiTrax/", pattern=glob2rx("All*.csv"))#
nNGS<-rownames(tmpshot$info[which.max(tmpshot$info$mtime),]);
tmpshot <- fileSnapshot("/Volumes/IDGenomics_NAS/NextStrain/EpiTrax/", pattern=glob2rx("NGS*.csv"))#
NGS<-rownames(tmpshot$info[which.max(tmpshot$info$mtime),]);
cat("2.- These files have been detected (IDGenomics_NAS) as the last files created: ",nNGS, " and ",NGS,"\n")


#Step 5: Combining selected collumns from NGS_covid and ALL_ncovid_NoNgs into a file called LIMS = (NGS+nNGS)
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
covidseq_summaryIdLab<-covidseq_summary_filtered[c(grep("^[[:digit:]]", covidseq_summary_filtered$Sample_Accession)), ]; # only samples with LabId
NGS<-read.csv(paste("/Volumes/IDGenomics_NAS/NextStrain/EpiTrax/",NGS,sep="")); 
NGSS<-NGS[,c(3,4,5,7,9,12)];head(NGSS);
nNGS<-read.csv(paste("/Volumes/IDGenomics_NAS/NextStrain/EpiTrax/",nNGS,sep=""));
nNGSS<-nNGS[,c(3,4,5,7,9,11)];head(nNGSS);
LIMS<-bind_rows(NGSS, nNGSS);head(LIMS);

#Step 6: matrix1: Collecting demographic data for those samples with laboratory accessions (left join tables)
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
matrix1<-merge(covidseq_summaryIdLab,LIMS, by.x="Sample_Accession", by.y= "sampleNumber", all.x=TRUE);head(matrix1); # left join
matrix1<-matrix1[,c(3,4,5,7,1,2)]; head(matrix1)
colnames(matrix1)[5] <- 'sampleNumber';
matrix1<-distinct(matrix1)
head(matrix1)


# Step 7: matrix2: Demographic data for samples with IHC2 (Exxxxxxx/Xxxxxx) left join tables)
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
LIMS2<-(LIMS %>% filter(grepl('/',submitterId))); head(LIMS2)
IHC1<-gsub("\\.*.*/","", (LIMS2 %>% filter(grepl('/',submitterId)))$submitterId );
LIMS2$IHC1<-IHC1
LIMS2$submitterId<-NULL
covidseq_summaryIHC1<-covidseq_summary_filtered[-c(grep("^[[:digit:]]", covidseq_summary_filtered$Sample_Accession)), ]; 
matrix2<-merge(covidseq_summaryIHC1,LIMS2, by.x="Sample_Accession", by.y= "IHC1");# inner join
matrix2<-distinct(matrix2)
matrix22<-matrix2; 
head(matrix22); # to same the IHC variable
head(covidseq_summaryIHC1);head(LIMS2)
matrix2<-matrix2[,c(3,4,5,7,6,2)]; head(matrix2)
matrix2$sampleNumber<-as.character(matrix2$sampleNumber)
matrix2<-distinct(matrix2)


# Step 8: matrix3: Demographic data for samples with any customer but not with xxxxxxx/xxxxxxxx
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
LIMS3<-dplyr::filter(LIMS, !grepl("/",submitterId)); head(LIMS3);
L1<-matrix22$Sample_Accession;
L2<-covidseq_summaryIHC1$Sample_Accession; head(L2); # 
L3<-L2[-pmatch(L1,L2)]; 
covidseq_summaryOthers<-merge(covidseq_summaryIHC1,L3,by.x="Sample_Accession", by.y= "y",all.y = TRUE); # right join)
matrix3<-merge(covidseq_summaryOthers,LIMS3, by.x="Sample_Accession", by.y= "submitterId",all.x=TRUE); # 
matrix3$sampleNumber<-as.character(matrix3$sampleNumber)

#coalesce
x1<-matrix3$Sample_Accession;x2<-matrix3$sampleNumber;
cc<-coalesce(x1,x2);
matrix3$sampleNumber<-cc
matrix3<-matrix3[,c(3,4,5,7,6,2)];


# step 9:  preparing ngs file and sending it to the RunName . . . . .covidseq_summary folder
         # to not rewrite the results from Python script in the same folder, this fileName will have  an R included  at the end indicating 
         # file from R script, i.e. ngs_UT-A01290-220304R.csv

ngs_file<-bind_rows(matrix1,matrix2, matrix3);

ngs_file$'Test result'[is.na(ngs_file$'Test result')]= "No able to be sequenced";
ngs_file2<-cbind(ngs_file, 'Name of facility performing the test'='UPHL', 'ordering facility' ='UHPL',
                 'Name or description of the test ordered'="SARS-CoV-2 Whole Genome Sequencing",
                 'lab test date'=ymd(date),'lab test status' ="preliminary",'ordering facility' ="UPHL")
ngs_file2$'lab test date'<-as.character(ngs_file2$'lab test date')

ngs_file2[is.na(ngs_file2)]= ""
ngs_file<-ngs_file2[,c(1,2,3,7,9,4,5,10,11,6,8)];
head(ngs_file)

arg<-args[1]; argg<-paste(arg,'R',sep="")
ngs_file_name<-paste(paste('ngs',argg,sep="_"),'csv',sep=".");
# ngs_file_name<-paste(paste('ngs',args[1],sep="_"),'csv',sep=".");
write.csv(ngs_file,paste(loc,ngs_file_name,sep="/"),row.names=FALSE)
cat("The file",ngs_file_name, "should be completed and saved at" ,loc ,"\n")
# bye bye
