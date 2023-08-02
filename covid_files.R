#!/usr/bin/env Rscript
# Author: OLinares
# Usage: Getting metadata covid stuff: ngs file, summary, data from NGS tracking system
# Parameter: Run Name ;  i.e. Rscript covid_dataFiles.R UT-A01290-230627 or Rscript covid_dataFiles.R UT-VH00770-230714
# last modified on July-26-2023

library("easypackages");libraries("grid","rbin","data.table","progress","XML"
                                  ,"xml2","seqinr","data.table","readr", "lubridate","gargle","googlesheets4")
sup <- suppressPackageStartupMessages
sup(library(lubridate));sup(library(tidyverse));options("width"=300)
args = commandArgs(trailingOnly=T)#

if(nchar(args[1])==17){date<-ymd(substr(args[1], 12, 17))} else{date<-ymd(substr(args[1], 11, 16))};date
runPath <-paste('/Volumes/NGS/Analysis/covidseq',args[1],sep="/")
df1 = read.csv(paste(runPath,"covidseq_output/Logs_Intermediates/SampleSheetValidation/SampleSheet_Intermediate.csv" ,sep = "/"))
df1

x = apply(df1, 1, function(x) {any(grepl(x, pattern = "Patient")) });



# Detecting runType and selecting the respective data from the SampleSheet format
# NextSeq and NovaSeq runs have different SampleSheet formats 
# ===================
if(nchar(args[1])==17){
  runType<-"NextSeq"
  M<-df1[x, ][,c(1,2)]; M<-cbind(M,paste(M$X.Header,args[1],sep="-"));M<-M[,c(1,3,3)]
} else{
  runType<-"NovaSeq"
  M<-df1[x, ][,c(1,2,3)] 
}
M
colnames(M)<-c("Sample_Accession","runName","SampleType");cat(crayon::bold$underline(" Detected a ",runType, "run with ",length(M$Sample_Accession),
                           " patient's samples","\n"))
head(M,10)
dim(M)

# Getting pangolin lineage 
# ====================
pango<-read.csv(paste(runPath,"CecretPangolin/pangolin/lineage_report.csv",sep ="/"))[,c("taxon","lineage")]
dim(pango);
var <-paste('',args[1],sep='-')
pango<-pango %>% mutate_at("taxon", str_replace, var, "")
M<-merge(M,pango, by.x="Sample_Accession", by.y= "taxon", all.x=T)
M$lineage[is.na(M$lineage)]= "Not able to be sequenced"

# Searching LIMS for collection dates (NGS and All...)
# ========================

# (1) from NGS_covid
cat(crayon::bold("Please wait, serching UPHL-LIMS","\n"))
cat(crayon::bold("1. From NGS_Covid","\n"))
NGS_covid<-rownames(fileSnapshot("/Volumes/IDGenomics_NAS/COVID/daily_metadata/lims/",
                                 pattern=glob2rx("NGS*.csv"))$info[which.max(fileSnapshot("/Volumes/IDGenomics_NAS/COVID/daily_metadata/lims/",
                                                                                          pattern=glob2rx("NGS*.csv"))$info$mtime),])
locus<-paste('/Volumes/IDGenomics_NAS/COVID/daily_metadata/lims/',NGS_covid,sep=""); locus
NGS_covid <- read.table(locus,header=TRUE,sep=",", stringsAsFactors=FALSE,comment.char="",nrows=500000, fill = T)
dim(NGS_covid)
NGS_covid<-NGS_covid[,c("sampleNumber","lastName","firstName","DOB","collectionDate")]
NGS_covid$sampleNumber<-as.character(NGS_covid$sampleNumber); 

# (2) from All_nocovid_NoNGS & and NGS_covid
cat(crayon::bold("2. From All_nocovid_NoNGS","\n"))
All_nocovid<-rownames(fileSnapshot("/Volumes/IDGenomics_NAS/COVID/daily_metadata/lims/",
                                   pattern=glob2rx("All*.csv"))$info[which.max(fileSnapshot("/Volumes/IDGenomics_NAS/COVID/daily_metadata/lims/",
                                                                                            pattern=glob2rx("All*.csv"))$info$mtime),])
locus<-paste('/Volumes/IDGenomics_NAS/COVID/daily_metadata/lims/',All_nocovid,sep="")
All_ncovid_NoNGS <- read.table(locus,header=TRUE,sep=",", stringsAsFactors=FALSE,comment.char="", fill = T,quote="\"")
All_ncovid_NoNGS<-All_ncovid_NoNGS[,c("sampleNumber","lastName","firstName","DOB","collectionDate")]

# Generating a LIMS-DB for this run
# ========================
LIMS<-rbind(NGS_covid,All_ncovid_NoNGS)
dim(LIMS)
dim(M)
ngs<-merge(M,LIMS, by.x ="Sample_Accession",by.y="sampleNumber", x.all = T) # aqui pasa algo loquisimo
dim(ngs)
ngs<-cbind(ngs,'Name of facility performing the test'='UPHL', 'ordering facility' ='UHPL',
           'Name or description of the test ordered'="SARS-CoV-2 Whole Genome Sequencing",
           'lab test date'=date,'lab test status' ="preliminary")
ngs_file<-select(ngs,"lastName",	"firstName",	"DOB",	"Name of facility performing the test",
                 "Name or description of the test ordered","collectionDate", "Sample_Accession",
                 "lab test date","lab test status","lineage","ordering facility")
ngs_file[is.na(ngs_file)] <- ""
colnames(ngs_file)[7]<-c("sampleNumber");colnames(ngs_file)[10]<-c("Test result")
head(ngs_file)
dim(ngs_file)

# Storing ngs file at /Volumes/NGS/Analysis/covidseq/$runName
# ==========================
d=paste(runPath,'Rsumcovidseq',sep="/")
dir.create(file.path(d,"" ), recursive = T)
LL<-paste(substring(Sys.time(), 1,10),substring(Sys.time(), 12,13),
          substring(Sys.time(),15,16),substring(Sys.time(), 18,19),sep = "-")
dx<- paste(paste('ngs_file',args[1],sep="_"),LL,".csv",sep="")
dx<-paste(d,dx, sep ='/');write.csv(ngs_file,dx,row.names=F)
cat(crayon::bold("ngs file is complete and can be found at",d,"\n"))

# Summary file
# ======================
clade = select(read.table(file = paste(runPath,"CecretPangolin/nextclade/nextclade.tsv",
                                       sep ="/"), sep = '\t', header = T),seqName,clade); 
clade<-clade %>% mutate_at("seqName", str_replace, var, "")

df2 = read.csv(paste(runPath,"CecretPangolin/pangolin/lineage_report.csv",sep ="/"))
df3 = read.table(file = paste(runPath,"covidseq_output/Logs_Intermediates/VirusDetection/kmer/Summary.tsv",sep ="/"),
                 sep = '\t', header = T); 
df4 = read.csv(paste(runPath,"covidseq_output/Logs_Intermediates/FastqGeneration/Reports/Demultiplex_Stats.csv",sep ="/"))
df4<-select(df4, c("SampleID","X..Reads","Mean.Quality.Score..PF."))
var <-paste('',args[1],sep='-')
df4<-df4 %>% mutate_at("SampleID", str_replace, var, ""); df4<-df4 %>% rename(Num_reads = 2, Mean_Quality_Score = 3)


# Random Number Generator (RNG) for Sample_IDs
# =========================
n<-length(M$Sample_Accession); n
RNG<-paste(floor(runif(n, min=99, max=1000)),floor(runif(n, min=99, max=1000)),sep ="")

# Checking for duplicates in RNG
while(length(RNG)!= length(unique(RNG)))
{ RNG<-paste(floor(runif(n, min=99, max=1000)),floor(runif(n, min=99, max=1000)),sep ="");}

if(nchar(args[1])==17){
  IDD<-paste("UT-UPHL",substr(args[1], 12, 18),sep="-")} else{
    IDD<-paste("UT-UPHL",substr(args[1], 11, 16),sep="-")}
Sample_ID<-paste(IDD,RNG,sep="")
df1<-M$Sample_Accession
summary1<-cbind(df1,Sample_ID);
#join tables: SampleSheet & Combined Lineage Report
#==========================  
var <-paste('',args[1],sep='-');
df2 <-df2 %>% mutate_at("taxon", str_replace, var, "")
df2<-df2[,c("taxon","lineage","scorpio_call")]
df3<-df3 %>% mutate_at("Sample", str_replace, var, "")
df3<-df3[,c("Sample","nTargetsDetected.SARS.CoV2")]
head(df3)
colnames(df3)[2] <- 'sc2_amplicons';#
clade
head(summary1)
head(clade)
summary1<-merge(summary1,df2, by.x="df1", by.y= "taxon", all.x=TRUE)
summary1<-merge(summary1,df3, by.x="df1", by.y= "Sample", all.x=TRUE)
summary1<-merge(summary1,clade, by.x="df1", by.y= "seqName", all.x=TRUE)

collectionD<-select(ngs_file,sampleNumber,collectionDate)
summary1<-merge(summary1,collectionD, by.x="df1", by.y= "sampleNumber", all.x=TRUE)


# Reading fasta files for nucleotides count: actg & anbiguous (n)
# ========================
num_actgx<-vector();num_nx<-vector(); pass_fail<-vector()
runPath1 = paste(runPath,"covidseq_output/Sample_Analysis/",sep ="/")
num_actgx = 0; num_nx = 0;
n
head(summary1)
for (i in 1:n){
  sample=summary1$df1[i]; sample; 
  amplicons=summary1$sc2_amplicons[i];amplicons
  if(amplicons >=50)
  {
    Lyapunovv<- Sys.glob(paste(runPath1,sample,"*/*.fasta",sep = ""),dirmark = TRUE)
    Lyapunovv
    a =  str_count(read.fasta(Lyapunovv, as.string = T, forceDNAtolower = T), pattern = "a|c|t|g");num_actgx[i] = a
    b =  str_count(read.fasta(Lyapunovv, as.string = T, forceDNAtolower = T))-a; num_nx[i] = b; pass_fail[i] ="pass"; c = "pass"
   
  }else {# AmpliconThereshold <50,
    a = b =0; num_actgx[i] = 0; num_nx[i] = 0; pass_fail[i] ="fail"; c = "fail"
  }
  cat(sample," \t",a,"\t",b,"\t",c,"\t",i,"\n")
}
  
  df_new <- as.data.frame(cbind(as.character(num_actgx), as.character(num_nx),pass_fail)); 
  df_new<-df_new %>% rename(num_actg = 1, num_n = 2)
  head(df_new)
  summary<-cbind(summary1,df_new);
  head(summary)
  
  # Adding more  info to the summary file
  # ==============================
  summary<-merge(summary,df4, by.x = "df1", by.y = "SampleID", all.x = T )
  head(summary)
  colnames(summary)[1]<-c("SampleNumber")
  summary<-cbind(summary,'Run Name'=args[1]) 
 
  # Saving file summary file at  /Volumes/NGS/Analysis/covidseq/$runName
  # ==========================
  d=paste(runPath,'Rsumcovidseq',sep="/");dir.create(file.path(d,"" ), recursive = TRUE); p1<-Sys.time()
  dx<- paste(d,'/Rcovidseq_summary-',paste0(Sys.Date(),'-',hour(Sys.time()),'-',minute(Sys.time()),'-',second(Sys.time())),".csv",sep=""); 
  write.csv(summary,dx,row.names=FALSE)
  cat(crayon::bold$underline("Summary is complete and can be found at: ",d,"\n"))
  head(summary)
  
  # Creating a file for NGS tracking system for copy/paste
  # ===========================
  dx<- paste(d,'/NGS_Tracking-',paste0(Sys.Date(),'-',hour(Sys.time()),'-',minute(Sys.time()),'-',second(Sys.time())),".csv",sep=""); 
  write.csv(select(summary,"SampleNumber","Sample_ID","collectionDate","Run Name","lineage","num_actg","clade")
            ,dx,row.names=FALSE)
  
  # json file: fastas2json  
  # ========================
  path2python<-paste("python3 /home/Bioinformatics/Dripping_Rock/bin/fasta_to_json.py",args[1],sep = " ")
  path2python
  system(path2python)

  # File to be  added to labware 8: NGS_COV_SEQ.txt
  # ========================
  path<-paste(d,"NGS_COV_SEQ.txt", sep ="/")
  f1 <-select(summary,1,13,2,3,8)
  col_names<-c("LIMS_TEST_ID","Run Name","UPHL Submission ID","Lineage","Non-Ambiguous Bases"); colnames(f1)<-col_names;
  write.table(f1, path, sep =",", col.names = T, row.names = F, quote = F)

# Adding results to SARS-CoV-2 NGS Tracking/Finished sheet.
# =============================
tokenPar <- readRDS("/Volumes/NGS/Bioinformatics/Lin/secrets/7a6077d23f6776ccc63f8f70bc12b214_olinares-perdomo@utah.gov")
gs4_auth(token = tokenPar)
page<-"https://docs.google.com/spreadsheets/d/1N_d2V6XESUeGTlb-uJIe_yPkHBe5qqXLFWWXY86wJZU/edit#gid=572325282"
RunResults<-read.csv(dx, header = T)
col_names<-c("Lab ID","Submission ID","Collection Date","Sequencing run","Pangolin Lineage (updated 2021-08-10)",
              "Number of non-ambiguous bases","Clade") 
colnames(RunResults)<-col_names; sheet_id<-page
sheet_append(sheet_id, data = RunResults)
cat(crayon::bold(nrow(RunResults), "columns have been added to SARS-CoV-2 NGS Tracking/Finished sheet ralated to run",args[1] ,"\n"))


