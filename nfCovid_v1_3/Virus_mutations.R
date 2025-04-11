#!/usr/bin/env Rscript
# Author: OLP/05/2024
# Spike-protein meandepth coverage


# S-protein meandepth coverage is a measure to assess the average depth of sequencing coverage across the Spike protein 
# It is simple the average number of sequencing reads aligned to each position in the S-protein, as determined by analyzing a 
# BAM (Binary Alignment/Map) file.

#library("easypackages");libraries("grid","rbin","data.table","progress","dplyr")
library("grid")
library("rbin")
library("data.table")
library("progress")
library("dplyr")
library("ggplot2")
library("Biostrings")
library("Biostrings")
library("GenomicRanges")
library("rtracklayer")




# 1. How to read a particular nucletide in the reference genome
ref_genome <- readDNAStringSet("/Volumes/NGS/Analysis/Mic-Covid/240802/BWA_test/NCBIsequence.fasta");print(ref_genome)
start_position <- 16026;end_position <- 16030; 
specific_region <- subseq(ref_genome[[1]], start=start_position, end=end_position); specific_region


# mutation analysis from fastas: This fastas are already aligned to the reference, come from consensus fasta
fasta_in_analysis<-readDNAStringSet("/Volumes/NGS/Analysis/covidseq/UT-VH00770-240802/ParFastas/3580360.fasta");print(fasta_in_analysis)
start_position <- 16026;end_position <- 16030; 
specific_region <- subseq(fasta_in_analysis[[1]], start=start_position, end=end_position); specific_region


# mutation analysis from the VCF.gz file (this file come from read aligned to the genome)

args = commandArgs(trailingOnly=T);runName<-args[1]
# runName<-"UT-VH00770-240726"; # for testing

Spike <- read.csv(paste("/Volumes/NGS/Analysis/covidseq",runName,"CecretPangolin/pangolin/lineage_report.csv", sep = "/"))
Spike2<-as.data.frame(Spike$taxon)
class(Spike2)
path2<-paste("/Volumes/NGS/Analysis/covidseq",runName,"covidseq_output/Sample_Analysis",sep = "/"); path2
n <-nrow(Spike2); vec<-vector(); sampl<-vector();

for (i in 1:n)
{
 sample<-Spike2[i,1]; 
 d1<-Sys.glob(paste(path2,sample,"*filtered.bam",sep = "/"),dirmar = T); d1
# index
  icommand<-paste("samtools", "","index",d1); system(icommand)
# coverage
  command<-paste("samtools","","coverage","",d1," ","-r","","NC_045512.2:21563-25384"); res<-system(command, intern = TRUE)
  header1<-paste("Reference","   ","StartPos","    ","EndPos","     ","numreads", "   ","covbases","      ","coverage", "    ","meandepth","  ","meanbaseq","  ","meanmapq","       ","sample")
  if (i ==1) print(header1)else end;

  split_vector <- strsplit(res, "\t")[[2]];
  print(c(split_vector,sample));  
  vec[i]<-split_vector[7]; # to report S-protein meandepth coverage on SARS-NGS tracking systems
}
# save results
  listt<-Spike2[1:n,1];
  Spike_coverage <- as.data.frame(cbind(as.character(listt), as.character(round(as.numeric(vec),1)))); 
  colnames(Spike_coverage)<-c("Sample","Spike-protein meanDepth");
  pp<-paste(paste("/Volumes/NGS/Analysis/covidseq",runName,sep = "/"),paste(paste(runName,"S-protein-meandepth_coverage",sep="_"),".csv",sep=""),sep = "/");
  write.csv(Spike_coverage,pp)

