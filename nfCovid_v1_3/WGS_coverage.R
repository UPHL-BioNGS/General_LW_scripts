#!/usr/bin/env Rscript
# Author: OLP/05/2024
# WGS meandepth coverage

# WGS meandepth coverage is a measure to assess the average depth of sequencing coverage across the whole genome.
# It is simple the average number of sequencing reads aligned to each position in the whole genome, as determined by analyzing a 
# BAM (Binary Alignment/Map) file.

#library("easypackages");libraries("grid","rbin","data.table","progress","dplyr")
library("grid")
library("rbin")
library("data.table")
library("progress")
library("dplyr")

options("width"=400)
args = commandArgs(trailingOnly=T);runName<-args[1]
# runName<-"UT-VH00770-240517"; # for testing

WGS <- read.csv(paste("/Volumes/NGS/Analysis/covidseq",runName,"CecretPangolin/pangolin/lineage_report.csv", sep = "/"))
WGS2<-as.data.frame(WGS$taxon)
class(WGS2)
path2<-paste("/Volumes/NGS/Analysis/covidseq",runName,"covidseq_output/Sample_Analysis",sep = "/"); path2
n <-nrow(WGS2); vec<-vector(); sampl<-vector();
# n<-5; for testing
for (i in 1:n)
{
 sample<-WGS2[i,1]; 
 d1<-Sys.glob(paste(path2,sample,"*filtered.bam",sep = "/"),dirmar = T); d1
# index
  icommand<-paste("samtools", "","index",d1); system(icommand)
# coverage
  command<-paste("samtools","","coverage","",d1," ","-r","","NC_045512.2:1-29903"); res<-system(command, intern = TRUE)
  header1<-paste("Reference","   ","StartPos","    ","EndPos","     ","numreads", "   ","covbases","      ","coverage", "    ","meandepth","  ","meanbaseq","  ","meanmapq","       ","sample")
  if (i ==1) print(header1)else end;

  split_vector <- strsplit(res, "\t")[[2]];
  print(c(split_vector,sample));  
  vec[i]<-split_vector[7]; # to report S-protein meandepth coverage on SARS-NGS tracking systems
}
# save results
  listt<-WGS2[1:n,1];
  WGS_coverage <- as.data.frame(cbind(as.character(listt), as.character(round(as.numeric(vec),1)))); 
  colnames(WGS_coverage)<-c("Sample","WGS meanDepth");
  pp<-paste(paste("/Volumes/NGS/Analysis/covidseq",runName,sep = "/"),paste(paste(runName,"WGS_coverage",sep="_"),".csv",sep=""),sep = "/");
  write.csv(WGS_coverage,pp)

