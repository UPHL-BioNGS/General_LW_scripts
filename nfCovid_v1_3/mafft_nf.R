#!/usr/bin/env Rscript
# Author: OLP/01/2022
# Usage: MAFFT
# Parameter: Run Name ;  i.e. Rscript ngs&summary.R UT-VH0770-230212
# last modified on 08-03-24

library(Biostrings)
sup <- suppressPackageStartupMessages
sup(library(lubridate));sup(library(tidyverse));options("width"=300)
args = commandArgs(trailingOnly=T);
# args[1]<- c("UT-VH00770-241206") #for testing only
 args[1]<- c("UT-VH00770-250328");

paste('/Volumes/NGS/Analysis/covidseq',args[1],sep="/")
fasta_file <- paste("/Volumes/NGS/Analysis/covidseq",args[1],"concatenate_for_alignment.fasta",sep = "/");
sequences <- readDNAStringSet(paste("/Volumes/NGS/Analysis/covidseq",args[1],"concatenate_for_alignment.fasta",sep="/"), format="fasta")
output_file <-paste("/Volumes/NGS/Analysis/covidseq",args[1],paste(args[1],"aligned_sequences.fasta",sep="-"),sep = "/");
mafft_command <- paste("mafft --auto", fasta_file, ">", output_file)
system(mafft_command)

