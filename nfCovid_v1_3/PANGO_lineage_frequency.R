#!/usr/bin/env Rscript
# Author: OLP/08/2024
# PANGO_lineage_frequency
library("tidyverse")
library("lubridate")
library("grid")
library("data.table")
# library("data.table")

args = commandArgs(trailingOnly=T)
# args[1]<-c('UT-VH00770-250131') # only for testing phase

runPath1 <-paste('/Volumes/NGS/Analysis/covidseq',args[1],sep="/") 

pxx<- Sys.glob(paste(runPath1,"clinical*.txt",sep = "/"),dirmark = TRUE)
pxx
df1<-read.table(pxx) # no se por que esta aqui
#df1 = read.table(Sys.glob(paste(runPath1,"clinical*.txt",sep = "/"),dirmark = TRUE));
df1
pangoAddress<-paste(runPath1,"CecretPangolin/pangolin/lineage_report.csv",sep ="/")

pp<-fread(pangoAddress, select=c("pangolin_version"))

pp3<-unlist(pp[2,], use.names = F)

pk<- unlist(fread(pangoAddress, select=c("pangolin_version"))[2,],use.names = F); head(pk)

pango<-fread(pangoAddress,select = c("taxon","lineage")) 

pango<-pango %>% mutate_at("taxon", str_replace, paste("-",args[1],sep =""),""); M<-df1;M;

df2<-merge(M,pango, by.x="V1", by.y= "taxon", all.x=T) 

df2$lineage[is.na(df2$lineage)]= "failed"

unique_lineage<-df2$lineage; unique_lineage<-as.data.frame(table(unique_lineage))

write.csv(unique_lineage,paste(runPath1,"PANGO_lineage_frequeny.csv",sep="/"))


