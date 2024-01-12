#!/usr/bin/env Rscript
# Author: OLP/12/2023
# Usage: Trigger the Dripping_Rock workflow using linux/crontab.
# last modified on 01/09/2024 (MM/DD/YYYY)

  library("easypackages");libraries("data.table","readr","dplyr")
  sup <- suppressPackageStartupMessages
      
  setwd("/Volumes/IDGenomics_NAS/COVID/daily_metadata/") 
  dir.create(as.character.Date(Sys.Date()))
  setwd(paste("/Volumes/IDGenomics_NAS/COVID/daily_metadata/",as.character.Date(Sys.Date()),sep="/"))
  
  print("RDripping_Rock wf")
  
  nextflow_script <- "/home/Bioinformatics/Dripping_Rock"
  system(paste("nextflow run", nextflow_script))

