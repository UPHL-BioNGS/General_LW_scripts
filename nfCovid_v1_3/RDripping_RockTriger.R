#!/usr/bin/env Rscript
# Author: OLP/01/2022
# Usage: Triggering the Dripping_Roc workfloe
# # last modified on 23/12/26

# library("easypackages");libraries("data.table","readr","dplyr")
library("data.table")
library("readr")
library("dplyr")
sup <- suppressPackageStartupMessages
sup(library(lubridate));sup(library(tidyverse));options("width"=300)

# Detecting last folder opened to trigger from there the Drinping_rock nextflow/workflow
FolderLastOpen <-rownames(fileSnapshot("/Volumes/NGS_2/COVID/daily_metadata/",
              pattern=glob2rx("2025*"))$info[which.max(fileSnapshot("/Volumes/NGS_2/COVID/daily_metadata/",pattern=glob2rx("2025*"))$info$mtime),])

setwd(paste("/Volumes/NGS_2/COVID/daily_metadata",FolderLastOpen,sep="/"))
nextflow_script <- "/home/Bioinformatics/Dripping_Rock/nextflow.nf"
system(paste("nextflow run", nextflow_script))





