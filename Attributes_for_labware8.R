#!/usr/bin/env Rscript
# Author: Olinares-perdomo
# Usage: Extracting the SRA, Biosample, GenBank and GISAID accession  information in order to \
#        generate the Attributes.txt file, which will be sent to AWS/Lab Ware 8.

# note: The file from GISAID "gisaid_hcov-19_xxxx.tsv" needs to be download before running this script

# Parameter: Run Name ;  i.e. Rscript Attributes_V1.1.R UT-VH0770-250214
# last modified on 25/02

library(readr);library(lubridate); 
suppressPackageStartupMessages(library("dplyr"))
suppressPackageStartupMessages(library("data.table"))
library(utils)
library(httr);
library(rentrez);
library(dplyr);
library(yaml)

  config<-read_yaml("config.yml")
  base_path<-config$paths$covidseq_base

  args = commandArgs(trailingOnly=T)
  args[1]<-c("UT-VH00770-250214")
  full_path_run<- file.path(base_path,args[1],"covidseq_output", "Logs_Intermediates","SampleSheetValidation","SampleSheet_Intermediate.csv")
  full_path_pango<- file.path(base_path,args[1],"CecretPangolin","cecret_results.csv")
  runPath<-file.path(base_path,args[1]);

# Extracting Clarity ID form SampleSheet and passed samples from Cecret wf
    df1<-read.csv(full_path_run)
    x = apply(df1,1, function(x) {any(grepl(x, pattern = "Patient")|grepl(x, pattern = "UT-UPHL")) })
    IDs<-as.data.frame(cbind((cbind(df1[x, ][,c(1)],df1[x, ][,c(3)]))))
    Clarity_IDs<-IDs[,c(1,2)]; Clarity_IDs
    dataPango<-read.csv(full_path_pango)[,c("sample_id","sample")]
    Clarity_IDs_PASSED<-merge(dataPango,Clarity_IDs, by.x ="sample_id", by.y ="V1", all = FALSE)[3]

# Retrieving SRA and Biosample Accessions from NCBI/SRA DB using rentrez/sra
    SRRv<-vector(); SAMNv<-vector();sampleID<-vector()
    cat("\rPlease wait, Retrieving SRA and Biosample Accessions from NCBI/SRA DB using rentrez")
    for (i in 1:nrow(Clarity_IDs_PASSED)){
      sample<-Clarity_IDs_PASSED[i,1]; 
      search_results<-entrez_search(db = "sra", term = sample, retmax = 5)
      if(length(search_results$ids)>0){
        metadata<-entrez_fetch(db ="sra", id = search_results$ids, rettype = "runinfo", retmodel ="text")
        meta<-strsplit(metadata[[1]],"[\n,]")[[1]]
       } else {
        cat("No SRA Accession, and Biosample Accession were found, NCBI/SRA has not processed the submission yet, Please try again later")
      }
      SRRv[i]<-meta[48];  SAMNv[i]<-meta[72];  sampleID[i]<-sample
      # 48 and 72 are the cell location for SRR and SAMN respectively in the metadata table obtained from rentrez/NCBI/SRA DB
    }
    SRA_data <- as.data.frame(cbind(as.character(sampleID), as.character(SAMNv),as.character(SRRv)))
    colnames(SRA_data)<-c("Clarity ID", "SRA Accession", "Biosample Accession")
    cat("\rData from NCBI/SRA was retrieved sucesseful")

# Retrieving GenBank Accession from GenBank DB using rentrez/nuccore
    cat("Wait, Retrieving GenBank Accessions from NCBI/GenBank DB using rentrez")
    GenBank_Accession<-vector();SRRv<-vector(); SAMNv<-vector();sampleID<-vector()
    for (i in 1:nrow(Clarity_IDs_PASSED)){
      sample<-Clarity_IDs_PASSED[i,1]; 
      search_results<-entrez_search(db = "nuccore", term = sample, retmax = 5)
      if(length(search_results$ids)>0){
        genbank_data <- entrez_fetch(db = "nuccore", id = search_results$ids, rettype = "gb", retmode = "text")
       # writeLines(genbank_data, "genbank_data.gb")
        meta<-strsplit(genbank_data[[1]],"[\n, ]")[[1]]
      } else {
        cat("No GenBank Accession, NCBI/GenBank has not processed the submission yet, Please try again later")
      }
      GenBank_Accession[i]<-meta[8];  sampleID[i]<-sample
      # 8 is the cell location for GenBank accession in the metadata table obtained from rentrez/NCBI/GenBank DB
     }
    GenBank_data <- as.data.frame(cbind(as.character(sampleID), as.character(GenBank_Accession))) 
    colnames(GenBank_data)<-c("Clarity ID", "GenBank Accession")
    SRA_GenBak_data<-merge(SRA_data,GenBank_data, by.x = "Clarity ID", by.y ="Clarity ID", all.x = TRUE)
 
# GISAID Accessions: Note: Data from GISAID is typically accessed via their portal an must be downloaded manually. Once downloaded, this script
#                         will automatically detect the GISAID file and extract the assigned IDs from it.
    GISAID_file<-rownames(fileSnapshot(runPath,pattern=glob2rx("gisaid*.tsv"))$info[which.max(fileSnapshot(runPath,pattern=glob2rx("gisaid*.tsv"))$info$mtime),])
    GISAID_path<-paste(runPath,GISAID_file,sep="/")
    GISAID_data <- read.table(GISAID_path,header=TRUE,sep="\t", stringsAsFactors=FALSE,comment.char="", fill = T,quote="\"")[,c("Virus.name","Accession.ID")]
    GISAID_data$Virus.name<-gsub("^hCoV-19/USA/(.*)/2025","\\1",GISAID_data$Virus.name)
    colnames(GISAID_data)<-c("Clarity ID","GenBank Accesion")
    Attributes<-merge(SRA_GenBak_data,GISAID_data, by.x ="Clarity ID", by.y = "Clarity ID", all.x = T)
    colnames(Attributes)<-c("LIMS_TEST_ID","SRA Accession","Biosample Accession","GenBank Accession","GISAID Accesion")

# Atributes.txt file generation
    # adding to Attributes the samples that failed. All samples passed and failed must be submitted to Lab Ware 8
    Atributes<-merge(Clarity_IDs[2],  Attributes, by.x ="V2", by.y = "LIMS_TEST_ID", all.x = TRUE)
    colnames( Atributes)<-c("LIMS_TEST_ID", "SRA Accession", "Biosample Accession", "GenBank Accession", "GISAID Accession")

    Atributes$"GISAID Accession"[is.na(Atributes$"GISAID Accession")]= "not Submitted"
    Atributes$"SRA Accession"[is.na(Atributes$"SRA Accession")]= "not Submitted"
    Atributes$"Biosample Accession"[is.na(Atributes$"Biosample Accession")]= "not Submitted"
    Atributes$"GenBank Accession"[is.na(Atributes$"GenBank Accession")]= "not Submitted"

    Attibuttes<-Atributes %>% mutate("Cluster Code" = "")

    write.table(Attibuttes,paste(runPath,"/",args[1],"_6Attributes.txt",sep=""), sep = ',', row.names = FALSE, col.names = TRUE, eol="\r\n", quote = FALSE)
    cat("Attributes.txt file for Labware 8 is complete and can be found at",runPath,"\n")
  
