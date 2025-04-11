#!/usr/bin/env Rscript
# Author: OLP/01/2022
# Usage: Phylogenetic tree using iqtree2/system2
# Parameter: Run Name ;  i.e. Rscript iqtree2_covidData.R UT-VH00770-240802
# last modified on 08-03-2024
library("Biostrings")
library("seqinr")
library("ape")

sup <- suppressPackageStartupMessages
sup(library(lubridate));sup(library(tidyverse));options("width"=300)
args = commandArgs(trailingOnly=T);
#args[1]<- c("UT-VH00770-240816") #for testing only
path<-paste(args[1],"aligned_sequences.fasta",sep="-")
path
#input_file <- paste("/Volumes/NGS/Analysis/covidseq",args[1],"UT-VH00770-240816-aligned_sequences.fasta",sep="/"); input_file
input_file <- paste("/Volumes/NGS/Analysis/covidseq",args[1],path,sep="/"); input_file
output_prefix <- "output_tree"

output_prefix<-paste("/Volumes/NGS/Analysis/covidseq",args[1],"output_tree",sep="/")

# Run IQ-TREE with desired options: IQ-tree 2 fundametal algorthm is the Felseinstein's algorthm based in Maximum Likelihood in finding the best tree
system2("iqtree2", args = c("-s", input_file, "-nt", "AUTO", "-m", "TEST", "-bb", "1000", "-pre", output_prefix))

# -s: specifies the input sequence file
# -nt: specifies the number of CPU threads to use; "AUTO" uses all available
# -m: model selection; "TEST" allows IQ-TREE to choose the best model
# -bb: number of ultrafast bootstrap replicates
# -pre: prefix for the output files
#  AUTO: uses the free available cores in the system


