#!/usr/bin/env Rscript
# Author: OLP/05/2024
# Viral proteins meandepth coverage

# Protein meandepth coverage is a measure to assess the average depth of sequencing coverage across the protein 
# It is simple the average number of sequencing reads aligned to each position, as determined by analyzing a 
# BAM (Binary Alignment/Map) file.

library("grid");library("rbin");library("data.table");
library("progress");library("dplyr");

options("width"=400);args = commandArgs(trailingOnly=T);runName<-args[1]

########## runName<-"UT-VH00770-241011"; # for testing
Samples<-as.data.frame(read.csv(paste("/Volumes/NGS/Analysis/covidseq",runName,"CecretPangolin/pangolin/lineage_report.csv", sep = "/"))$taxon)
path1<-paste("/Volumes/NGS/Analysis/covidseq",runName,"covidseq_output/Sample_Analysis",sep = "/"); 
vec_ORF6<-vector(); vec_ORF7a<-vector(); vec_ORF7b<-vector(); vec_ORF8<-vector(); vec_ORF10<-vector(); 
vec_nsp14<-vector(); vec_ORF3a<-vector();  

Coverage<-vector();sampl<-vector();n <-nrow(Samples); 

for (i in 1:n)
{
 sample<-Samples[i,1]; 
 d1<-Sys.glob(paste(path1,sample,"*filtered.bam",sep = "/"),dirmar = T); d1
# index
  icommand<-paste("samtools", "","index",d1); system(icommand)
# coverage 
   ORF6_res<-system(paste("samtools","","coverage","",d1," ","-r","","NC_045512.2:27202-27387"), intern = TRUE); 
  ORF7a_res<-system(paste("samtools","","coverage","",d1," ","-r","","NC_045512.2:27394-27759"), intern = TRUE);
  ORF7b_res<-system(paste("samtools","","coverage","",d1," ","-r","","NC_045512.2:27756-27887"), intern = TRUE); 
   ORF8_res<-system(paste("samtools","","coverage","",d1," ","-r","","NC_045512.2:27894-28259"), intern = TRUE);
  ORF10_res<-system(paste("samtools","","coverage","",d1," ","-r","","NC_045512.2:29558-29674"), intern = TRUE); 
  nsp14_res<-system(paste("samtools","","coverage","",d1," ","-r","","NC_045512.2:18040-19620"), intern = TRUE);
  ORF3a_res<-system(paste("samtools","","coverage","",d1," ","-r","","NC_045512.2:25393-26220"), intern = TRUE); 
  
  header1<-paste("Reference","    ","StartPos","   ","EndPos","       ","numreads", "   ","covbases","   ","coverage", "     ","meandepth","    ","meanbaseq","  ","meanmapq","     ","sample")
   if (i ==1) print(header1)else end;

   split_vector_ORF6 <- strsplit(ORF6_res, "\t")[[2]];  print(c(split_vector_ORF6,sample));  vec_ORF6[i]<-split_vector_ORF6[7]; 
 split_vector_ORF7a <- strsplit(ORF7a_res, "\t")[[2]]; print(c(split_vector_ORF7a,sample));vec_ORF7a[i]<-split_vector_ORF7a[7];
  split_vector_ORF7b <- strsplit(ORF7b_res, "\t")[[2]]; print(c(split_vector_ORF7b,sample));vec_ORF7b[i]<-split_vector_ORF7b[7];
   split_vector_ORF8 <- strsplit(ORF8_res, "\t")[[2]];  print(c(split_vector_ORF8,sample));  vec_ORF8[i]<-split_vector_ORF8[7]; 
  split_vector_ORF10 <- strsplit(ORF10_res, "\t")[[2]]; print(c(split_vector_ORF10,sample));vec_ORF10[i]<-split_vector_ORF10[7];
  split_vector_nsp14 <- strsplit(nsp14_res, "\t")[[2]]; print(c(split_vector_nsp14,sample));vec_nsp14[i]<-split_vector_nsp14[7];
  split_vector_ORF3a <- strsplit(ORF3a_res, "\t")[[2]]; print(c(split_vector_ORF3a,sample));vec_ORF3a[i]<-split_vector_ORF3a[7];

}
# save results

  listt<-Samples[1:n,1];
   ORF6_coverage <- as.data.frame(cbind(as.character(listt),as.character(round(as.numeric(vec_ORF6),1)))); 
  ORF7a_coverage <- as.data.frame(cbind(as.character(listt),as.character(round(as.numeric(vec_ORF7a),1)))); 
  ORF7b_coverage <- as.data.frame(cbind(as.character(listt),as.character(round(as.numeric(vec_ORF7b),1)))); 
   ORF8_coverage <- as.data.frame(cbind(as.character(listt),as.character(round(as.numeric(vec_ORF8),1))));
  ORF10_coverage <- as.data.frame(cbind(as.character(listt),as.character(round(as.numeric(vec_ORF10),1)))); 
  nsp14_coverage <- as.data.frame(cbind(as.character(listt),as.character(round(as.numeric(vec_nsp14),1)))); 
  ORF3a_coverage <- as.data.frame(cbind(as.character(listt),as.character(round(as.numeric(vec_ORF3a),1)))); 
  
  ORFs_coverage <-cbind(ORF6_coverage,ORF7a_coverage[,2],ORF7b_coverage[,2],ORF8_coverage[,2],ORF10_coverage[,2],nsp14_coverage[,2],ORF3a_coverage[,2])
  colnames(ORFs_coverage)<-c("Sample","ORF6 meanDepthCov","ORF7a meanDepthCov","ORF7b meanDepthCov","ORF8 meanDepthCov","ORF10 meanDepthCov","nsp14 meanDepthCov","ORF3a meanDepthCov");
  path2<-paste("/Volumes/NGS/Analysis/covidseq",runName,"ORFs_meandepth_coverage.csv",sep = "/");
  write.csv(ORFs_coverage,path2)

  
  