#!/usr/bin/env Rscript
# Author: OLP/01/2022
# Usage: fastas2json
# Parameter: Run Name ;  i.e. Rscript fastas2json.R UT-VH00770-230828
# last modified on 23/0822

#library("easypackages");libraries("grid","data.table","progress","XML","xml2","data.table","readr");
library("grid")
library("data.table")
library("progress")
library("data.table")
library("readr")


args = commandArgs(trailingOnly=T);
args[1]<-c("UT-VH00770-250328")
# json files: fastas2json 
# ========================
# path2python<-paste("python3.12.3 /home/Bioinformatics/Dripping_Rock/bin/fasta_to_json.py",args[1],sep = " ") after conda thing
 #path2python<-paste("python /home/Bioinformatics/Dripping_Rock/bin/fasta_to_json.py",args[1],sep = " ")
#/Volumes/NGS_2/Bioinformatics/olinto/Rdev_Dripping_Rock/Dripping_Rock_test/Dripping_Rock/bin/fasta_to_json.py
path2python<-paste("python /Volumes/NGS_2/Bioinformatics/olinto/Rdev_Dripping_Rock/Dripping_Rock_test/Dripping_Rock/bin/fasta_to_json.py",args[1],sep = " ")
path2python
 system(path2python)
