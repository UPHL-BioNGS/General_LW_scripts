#!/usr/bin/env Rscript
# Author: OLP
# Usage: Getting metadata for daily_metadata: fast2JOSN file
# Parameter: RunName :  i.e. Rscript fastas2JSON.R UT-VH00770-230212

library("easypackages");libraries("grid","rbin","data.table","progress","XML","xml2","seqinr","data.table","rjson","jsonlite", "lubridate","Biostrings")
sup <- suppressPackageStartupMessages
sup(library(lubridate));sup(library(tidyverse))
args = commandArgs(trailingOnly=T);

if(nchar(args[1])==17){date<-ymd(substr(args[1], 12, 17))} else{date<-ymd(substr(args[1], 11, 16))};date
runPath <-paste('/Volumes/NGS/Analysis/covidseq',args[1],sep="/")
df1 = read.csv(paste(runPath,"covidseq_output/Logs_Intermediates/SampleSheetValidation/SampleSheet_Intermediate.csv",sep = "/"))
x = apply(df1, 1, function(x) {any(grepl(x, pattern = "Patient")) });
M<-df1[x, ][,c(1,2)]; 
M<-cbind(M, paste(M$X.Header.,args[1],sep = "-"))
colnames(M)<-c("Sample_Accession","runName","fileName");
cat(" Detected ", length(M$Sample_Accession), " patient's samples")

M1<-read.csv(paste('/Volumes/NGS/Analysis/covidseq',args[1],'CecretPangolin/combined_summary.csv',sep = "/"))
head(M,10)
#inner join tables: which patient samples have fastas
#==========================
MM<-merge(M, M1, by.x ='Sample_Accession', by.y='sample_id');M<-MM[,c(1,3)]
cat(crayon::blue$underline(" Detected ", length(MM$Sample_Accession), " patient's samples with fasta sequence"))

# Searhing Volumes/IDGenomicsNAS/COVID/daily_metadata/lims/*NGS*.csv
# =========================
cat(crayon::blue$underline("Please wait, serching UPHL-LIMS - NGS_COVID","\n"))
# (1) NGS_COVID
# =======================
NGS_covid<-rownames(fileSnapshot("/Volumes/IDGenomics_NAS/COVID/daily_metadata/lims/",
                                 pattern=glob2rx("NGS*.csv"))$info[which.max(fileSnapshot("/Volumes/IDGenomics_NAS/COVID/daily_metadata/lims/",
                                                                                          pattern=glob2rx("NGS*.csv"))$info$mtime),])
locus<-paste('/Volumes/IDGenomics_NAS/COVID/daily_metadata/lims/',NGS_covid,sep=""); locus
df <- read.table(locus,header=TRUE,sep=",", stringsAsFactors=FALSE,comment.char="",nrows=500000, fill = T)
NGS_covid_data<-data.frame(df$sampleNumber,df$lastName, df$firstName, df$DOB,df$collectionDate)

#(2) All_nocovid_NoNGS
cat(crayon::blue$underline("Please wait, serching UPHL-LIMS - All_nocovid_NoNGS","\n"))
# =====================
All_nocovid<-rownames(fileSnapshot("/Volumes/IDGenomics_NAS/COVID/daily_metadata/lims/",
                                   pattern=glob2rx("All*.csv"))$info[which.max(fileSnapshot("/Volumes/IDGenomics_NAS/COVID/daily_metadata/lims/",
                                                                                            pattern=glob2rx("All*.csv"))$info$mtime),])
locus<-paste('/Volumes/IDGenomics_NAS/COVID/daily_metadata/lims/',All_nocovid,sep="")
locus

df <- read.table(locus,header=TRUE,sep=",", stringsAsFactors=FALSE,comment.char="", fill = T,quote="\"")


All_ncovid_NoNGS_data<-data.frame(df$sampleNumber,df$lastName, df$firstName, df$DOB,df$collectionDate)
head(All_ncovid_NoNGS_data,10)
dim(All_ncovid_NoNGS_data)
# Generating a LIMS for this run
# ========================
LIMS<-rbind(NGS_covid_data,All_ncovid_NoNGS_data)
head(LIMS, 20)
colnames(LIMS)<-c("sampleNumber","lastName", "firstName", "DOB","collectionDate")
head(M)
PatientDemographic<-merge(M,LIMS,by.x = "Sample_Accession", by.y ="sampleNumber", all.x = T)

head(PatientDemographic,10)
# (3) Getting data from epitrax_export_1551
cat(crayon::blue$underline("Please wait, serching epitrax_export_155","\n"))
# ========================
EpiTrax_Export<-rownames(fileSnapshot("/Volumes/IDGenomics_NAS/COVID/daily_metadata/epitrax/",
                                      pattern=glob2rx("export_1551*.csv"))$info[which.max(fileSnapshot("/Volumes/IDGenomics_NAS/COVID/daily_metadata/epitrax/",
                                                                                                       pattern=glob2rx("export_1551*.csv"))$info$mtime),])
cat(crayon::blue$underline("Please wait, searching EpiTrax","\n")); head(EpiTrax_Export)
locus<-paste('/Volumes/IDGenomics_NAS/COVID/daily_metadata/epitrax/',EpiTrax_Export,sep="")
M_epitrax<-fread(locus, select =c("patient_record_number","lab_accession_no"))
M_epitrax<-cbind(M_epitrax,M_epitrax$lab_accession_no); colnames(M_epitrax)[3]<-"Epitrax_ID"
head(M_epitrax)
Epi<-unique(merge(M,M_epitrax, by.x ="Sample_Accession", by.y = "lab_accession_no", all.x = T))
head(Epi,20)
Epi$patient_record_number<-as.character(Epi$patient_record_number)
Epi$patient_record_number[is.na(Epi$patient_record_number)] <- "missing"
Epi$Epitrax_ID[is.na(Epi$Epitrax_ID)] <- "not_found"
# all together
# ======================
Matrix<- cbind(Epi,PatientDemographic)
Matrix$Epitrax_ID[is.na(Matrix$Epitrax_ID)] <- "Not_found"
lims_found<-Matrix$collectionDate; lims_found[is.na(lims_found)] <- "missing";lims_found[!is.na(lims_found)] <- "sampleNumer"
Matrix<-cbind(Matrix,lims_found); 
head(Matrix,30)

#Getting the sequences: only PatientSamples
# ======================
cat(crayon::blue$underline("Please wait, getting the fasta sequences","\n"))
path<-paste(runPath,"covidseq_output/Sample_Analysis/",sep="/")


head(M,21)
seq_name<-0; sequence<-0
counter = length(M$Sample_Accession); 

for (i in 1:counter){
  sample=Matrix$Sample_Accession[i]; sample
  Lyapunovv<- Sys.glob(paste(path,sample,"*/*.fasta",sep = ""),dirmark = TRUE); Lyapunovv
  fastaFile <- readDNAStringSet(Lyapunovv)
  sequence[i] = paste(fastaFile)
}
df <- data.frame(sequence);

# JSON file
# ===================
Alist_1 = vector(mode="list", length = counter)
Alist_1[[1]] = Matrix$Sample_Accession[1:counter]
Alist_1[[2]] = Matrix$collectionDate[1:counter]
Alist_1[[3]] = Matrix$patient_record_number[1:counter]
Alist_1[[4]] = Matrix$fileName[1:counter]
Alist_1[[5]] = Matrix$lims_found[1:counter]
Alist_1[[6]] = df


json2 <- data.frame(
          LIMS_ID = Alist_1[[1]],
  collection_date = Alist_1[[2]],
       Epitrax_ID = Alist_1[[3]],
         filename = Alist_1[[4]],
       lims_found = Alist_1[[5]],
          df)

Path2Save<-paste("/Volumes/IDGenomics_NAS/COVID/daily_metadata/json/",paste(args[1],"json",sep="."), sep = "")
cat(crayon::blue$underline("fastas2Json file can be found at: ", Path2Save,"\n"))
write_json(json2, Path2Save)
