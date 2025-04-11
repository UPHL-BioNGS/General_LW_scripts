#!/usr/bin/env Rscript
# Author: OLP/01/2022
# Usage: Moving json file from json folder to working_json folder
# # last modified on 23/12/26 [yy/mm/dd]

#library("easypackages");libraries("data.table","readr","dplyr")
library("data.table")
library("readr")
library("dplyr")



sup <- suppressPackageStartupMessages

# Detecting last json in json folder, it was just created before
NGS_covidJSON <-rownames(fileSnapshot("/Volumes/IDGenomics_NAS/COVID/daily_metadata/json/",
              pattern=glob2rx("*.json"))$info[which.max(fileSnapshot("/Volumes/IDGenomics_NAS/COVID/daily_metadata/json/",pattern=glob2rx("*.json"))$info$mtime),])
NGS_covidJSON

# moving this json file  to working_json  folder
file.copy(from = paste("/Volumes/IDGenomics_NAS/COVID/daily_metadata/json",NGS_covidJSON,sep="/"), 
          to   = paste("/Volumes/IDGenomics_NAS/COVID/daily_metadata/working_json",NGS_covidJSON,sep="/"), overwrite = T)
          
#file.copy(from, to, overwrite = FALSE, recursive = FALSE, copy.mode = TRUE, copy.date = FALSE)



