#!/usr/bin/env Rscript
# Author: OLP/05/2024
# Viral proteins meandepth coverage

# Protein meandepth coverage is a measure to assess the average depth of sequencing coverage across the protein 
# It is simple the average number of sequencing reads aligned to each position, as determined by analyzing a 
# BAM (Binary Alignment/Map) file.

library("grid");library("rbin");library("data.table");
library("progress");library("dplyr");

options("width"=400);args = commandArgs(trailingOnly=T);runName<-args[1]

##  runName<-"UT-VH00770-241217"; # for testing
Samples<-as.data.frame(read.csv(paste("/Volumes/NGS/Analysis/covidseq",runName,"CecretPangolin/pangolin/lineage_report.csv", sep = "/"))$taxon)
path1<-paste("/Volumes/NGS/Analysis/covidseq",runName,"covidseq_output/Sample_Analysis",sep = "/"); 
vec_S<-vector(); vec_E<-vector(); vec_M<-vector(); vec_N<-vector(); Coverage<-vector();sampl<-vector();n <-nrow(Samples); 

for (i in 1:n)
{
 sample<-Samples[i,1]; 
 d1<-Sys.glob(paste(path1,sample,"*filtered.bam",sep = "/"),dirmar = T); d1
# index
  icommand<-paste("samtools", "","index",d1); system(icommand)
# coverage (S-E-M-N)
  S_res<-system(paste("samtools","","coverage","",d1," ","-r","","NC_045512.2:21563-25384"), intern = TRUE); 
  E_res<-system(paste("samtools","","coverage","",d1," ","-r","","NC_045512.2:26245-26472"), intern = TRUE);
  M_res<-system(paste("samtools","","coverage","",d1," ","-r","","NC_045512.2:26523-27191"), intern = TRUE); 
  N_res<-system(paste("samtools","","coverage","",d1," ","-r","","NC_045512.2:28274-29533"), intern = TRUE);
  
  header1<-paste("Reference"," ","StartPos"," ","EndPos"," ","numreads", " ","covbases"," ","coverage", " ","meandepth","  ","meanbaseq","  ","meanmapq","  ","sample")
  if (i ==1) print(header1)else end;

  split_vector_S <- strsplit(S_res, "\t")[[2]]; print(c(split_vector_S,sample));vec_S[i]<-split_vector_S[7]; # S-protein meandepth coverage
  split_vector_E <- strsplit(E_res, "\t")[[2]]; print(c(split_vector_E,sample));vec_E[i]<-split_vector_E[7]; # E-protein meandepth coverage
  split_vector_M <- strsplit(M_res, "\t")[[2]]; print(c(split_vector_M,sample));vec_M[i]<-split_vector_M[7]; # M-protein meandepth coverage
  split_vector_N <- strsplit(N_res, "\t")[[2]]; print(c(split_vector_N,sample));vec_N[i]<-split_vector_N[7]; # N-protein meandepth coverage
  
}
# save results
  listt<-Samples[1:n,1];
         Spike_coverage <- as.data.frame(cbind(as.character(listt),as.character(round(as.numeric(vec_S),1)))); 
      Envelope_coverage <- as.data.frame(cbind(as.character(listt),as.character(round(as.numeric(vec_E),1)))); 
      Membrane_coverage <- as.data.frame(cbind(as.character(listt),as.character(round(as.numeric(vec_M),1)))); 
  Nucleocapsid_coverage <- as.data.frame(cbind(as.character(listt),as.character(round(as.numeric(vec_N),1))));
  
  Viral_proteins_coverage <-cbind(Spike_coverage,Envelope_coverage[,2],Membrane_coverage[,2],Nucleocapsid_coverage[,2])
  colnames(Viral_proteins_coverage)<-c("Sample","S-gene meanDepthCov","E-gene meanDepthCov","M-gene meanDepthCov","N-gene meanDepthCov");
  path2<-paste("/Volumes/NGS/Analysis/covidseq",runName,"Viral_proteins-meandepth_coverage.csv",sep = "/");
  write.csv(Viral_proteins_coverage,path2)

  
  
