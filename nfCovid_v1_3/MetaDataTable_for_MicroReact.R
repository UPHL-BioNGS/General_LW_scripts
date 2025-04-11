#!/usr/bin/env Rscript
# Author: OLP/01/2022
# Usage: MetadataTabel for microreact project
# Parameter: Run Name ;  i.e. Rscript MetadataTable_for_microReact.R UT-VH077-230822
# last modified on 08-28-23

library("data.table")
library("dplyr")
library("stringr")
library("readr")
library("grid")
library("progress")
library("readr")
library("utils")

sup <- suppressPackageStartupMessages
sup(library(lubridate));sup(library(tidyverse));options("width"=300)
args = commandArgs(trailingOnly=T);
######## args[1]<- c("UT-VH00770-241004"); # for testing only
ngsT<-read.csv(paste("/Volumes/NGS/Analysis/covidseq/",args[1],"/Rsumcovidseq/",paste("ngs_",args[1],".csv", sep =""), sep =""));
MetadaTable<-ngsT[c("sampleNumber","Test.result","DOB","lastName","firstName","collectionDate")];
date<-ngsT[c("collectionDate")];
year<-as.data.frame(str_sub(date$collectionDate,1,4)); month<-as.data.frame(str_sub(date$collectionDate,6,7)); 
day<-as.data.frame(str_sub(date$collectionDate,9,10));
m<-cbind(MetadaTable,year, month, day);colnames(m)[7:9]<-c("year","month","day")
path<-paste("/Volumes/NGS/Analysis/covidseq/",args[1],sep="");

Viral_proteins_coverage<-read.csv(Sys.glob(paste(path,"/*Viral*",sep = ""),dirmark = TRUE));
ORFs_meandepth_coverage<-read.csv(Sys.glob(paste(path,"/ORFs*",sep = ""),dirmark = TRUE));
genes_coverage<-cbind(Viral_proteins_coverage[,-1],ORFs_meandepth_coverage[,c(-1,-2)]); 

MetadataTable<-merge(m,genes_coverage, by.x="sampleNumber", by.y= "Sample", all.x=TRUE)
head(MetadataTable)
dx<- paste(paste("/Volumes/NGS/Analysis/covidseq",args[1],sep = "/"),'/MetadataTable_microreact-',
           paste0(Sys.Date(),'-',hour(Sys.time()),'-',minute(Sys.time())),".csv",sep=""); 
write.csv(MetadataTable,dx)

