#!/usr/bin/env Rscript
# Author: OLP/01/2022
# Usage: Getting metadata for ngs file
# Parameter: Run Name ;  i.e. Rscript ngs&summary.R UT-VH0770-230212
# last modified on 23/06/02

# library("easypackages");libraries("grid","rbin","progress","XML","xml2","seqinr","data.table","readr","dplyr")
#library("easypackages");
# se cambio cuando empece a correr desde a conc enviromen, problem that need to be solved
library("grid")
library("rbin")
library("progress")
library("seqinr")
library("data.table")
library("readr")
library("dplyr")
library("utils")
conflicts()
find("read.table")

sup <- suppressPackageStartupMessages
sup(library(lubridate));sup(library(tidyverse));options("width"=300)
args = commandArgs(trailingOnly=T);
 args[1]<- c("UT-VH00770-250328")# for testing only
if(nchar(args[1])==17){date<-ymd(substr(args[1], 12, 17))} else{date<-ymd(substr(args[1], 11, 16))};date
runPath <-paste('/Volumes/NGS/Analysis/covidseq',args[1],sep="/")
runPath
df1 = read.csv(paste(runPath,"covidseq_output/Logs_Intermediates/SampleSheetValidation/SampleSheet_Intermediate.csv"
                     ,sep = "/"))
head(df1)
x = apply(df1, 1, function(x) {any(grepl(x, pattern = "Patient")) });
args[1]
if(nchar(args[1])==17){
  runType<-"NextSeq"
  M<-df1[x, ][,c(1,2)]; 
  M<-cbind(M,paste(M$X.Header,args[1],sep="-"));
  M<-M[,c(1,3,3)]
} else{
  runType<-"NovaSeq"
  M<-df1[x, ][,c(1,2,2)] 
}

M
dim(M)

colnames(M)<-c("Sample_Accession","runName","fileName");
cat(crayon::bold$underline(" Detected a ",runType, "run with ",length(M$Sample_Accession),
                           " patient's samples","\n"))
head(M,10)
dim(M)
# Getting pangolin lineage (cecret must be ran first)
# ====================
pango<-read.csv(paste(runPath,"CecretPangolin/pangolin/lineage_report.csv",sep ="/"))[,c("taxon","lineage")]
dim(pango)
var <-paste('',args[1],sep='-')
pango<-pango %>% mutate_at("taxon", str_replace, var, "")
M<-merge(M,pango, by.x="Sample_Accession", by.y= "taxon", all.x=T)
M$lineage[is.na(M$lineage)]= "Not able to be sequenced"

# Searching LIMS for collection dates (NGS and All...)
# ========================
# (1) from NGS_covid
cat(crayon::bold("Please wait, serching UPHL-LIMS","\n"))
cat(crayon::bold("1. From NGS_Covid","\n"))
NGS_covid<-rownames(fileSnapshot("/Volumes/NGS_2/COVID/daily_metadata/lims/",
                                 pattern=glob2rx("NGS*.csv"))$info[which.max(fileSnapshot("/Volumes/NGS_2/COVID/daily_metadata/lims/",
                                                                                          pattern=glob2rx("NGS*.csv"))$info$mtime),])
locus<-paste('/Volumes/NGS_2/COVID/daily_metadata/lims/',NGS_covid,sep=""); locus
NGS_covid <- read.table(locus,header=TRUE,sep=",", stringsAsFactors=FALSE,comment.char="",nrows=500000, fill = T)
dim(NGS_covid)
NGS_covid<-NGS_covid[,c("sampleNumber","lastName","firstName","DOB","collectionDate")]
NGS_covid$sampleNumber<-as.character(NGS_covid$sampleNumber); 

# (2) from All_nocovid_NoNG
cat(crayon::bold("2. From All_nocovid_NoNGS","\n"))
All_nocovid<-rownames(fileSnapshot("/Volumes/NGS_2/COVID/daily_metadata/lims/",
                                   pattern=glob2rx("All*.csv"))$info[which.max(fileSnapshot("/Volumes/NGS_2/COVID/daily_metadata/lims/",
                                                                                            pattern=glob2rx("All*.csv"))$info$mtime),])
locus<-paste('/Volumes/NGS_2/COVID/daily_metadata/lims/',All_nocovid,sep="")
All_ncovid_NoNGS <- read.table(locus,header=TRUE,sep=",", stringsAsFactors=FALSE,comment.char="", fill = T,quote="\"")
All_ncovid_NoNGS<-All_ncovid_NoNGS[,c("sampleNumber","lastName","firstName","DOB","collectionDate")]

# Generating a LIMS for this run
# ========================
LIMS<-rbind(NGS_covid,All_ncovid_NoNGS)
dim(LIMS)
dim(M)
ngs<-merge(M,LIMS, by.x ="Sample_Accession",by.y="sampleNumber", x.all = T) # aqui pasa algo loquisimo
dim(ngs)

ngs<-cbind(ngs,'Name of facility performing the test'='UPHL', 'ordering facility' ='UHPL',
           'Name or description of the test ordered'="SARS-CoV-2 Whole Genome Sequencing",
           'lab test date'=date,'lab test status' ="preliminary")
ngs_file<-dplyr::select(ngs,"lastName",	"firstName",	"DOB",	"Name of facility performing the test",
                 "Name or description of the test ordered","collectionDate", "Sample_Accession",
                 "lab test date","lab test status","lineage","ordering facility")
ngs_file[is.na(ngs_file)] <- ""
colnames(ngs_file)[7]<-c("sampleNumber");colnames(ngs_file)[10]<-c("Test result")
head(ngs_file)
dim(ngs_file)

# Storing ngs file at /Volumes/NGS/Analysis/covidseq/ $runName
# ==========================
d=paste(runPath,'Rsumcovidseq',sep="/")
dir.create(file.path(d,"" ), recursive = T)
LL<-paste(substring(Sys.time(), 1,10),substring(Sys.time(), 12,13),
          substring(Sys.time(),15,16),substring(Sys.time(), 18,19),sep = "-")
dx<- paste(paste('ngs',args[1],sep="_"),LL,".csv",sep="-")
dx<-paste(d,dx, sep ='/');
write.csv(ngs_file,dx,row.names=F)
dx2<- paste(paste('ngs',args[1],sep="_"),".csv",sep="");
dx2<-paste(d,dx2, sep ='/');
write.csv(ngs_file,dx2,row.names=F)
cat(crayon::bold("ngs file is complete and can be found at",d,"\n"))


head(M)

## 
MRes<-ngs_file[,"sampleNumber", drop =F] 
Mx<-merge(MRes,M, by.x="sampleNumber",by.y="Sample_Accession",all.x = T)
head(Mx)
names(Mx)[1]<-"Sample_Accession"
M<-Mx
head(M)
# Summary file
# ======================
clade = dplyr::select(read.table(file = paste(runPath,"CecretPangolin/nextclade/nextclade.tsv",
                                       sep ="/"), sep = '\t', header = T),seqName,clade); 
runPath
df2 = read.csv(paste(runPath,"CecretPangolin/pangolin/lineage_report.csv",sep ="/"))
      
df3 = read.table(file = paste(runPath,"covidseq_output/Logs_Intermediates/VirusDetection/kmer/Summary.tsv",sep ="/"),
                 sep = '\t', header = T); 
df4 = read.csv(paste(runPath,"covidseq_output/Logs_Intermediates/FastqGeneration/Reports/Demultiplex_Stats.csv",sep ="/"))
df4<-dplyr::select(df4, c("SampleID","X..Reads","Mean.Quality.Score..PF."))
var <-paste('',args[1],sep='-')
df4<-df4 %>% mutate_at("SampleID", str_replace, var, ""); colnames(df4)<-c("SampleID","Nume_reads","Mean_Quality_Score")

# Random Number Generator for Sample_IDs
# =========================
dim(M)
head(M)
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
head(df3,60)
colnames(df3)[2] <- 'sc2_amplicons';#
summary1<-merge(summary1,df2, by.x="df1", by.y= "taxon", all.x=TRUE)
summary1<-merge(summary1,df3, by.x="df1", by.y= "Sample", all.x=TRUE)
summary1<-merge(summary1,clade, by.x="df1", by.y= "seqName", all.x=TRUE)

collectionD<-dplyr::select(ngs_file,sampleNumber,collectionDate)
summary1<-merge(summary1,collectionD, by.x="df1", by.y= "sampleNumber", all.x=TRUE)

head(summary1)
# Reading fasta files for nucleotides count: actg & anbiguous (n)
# ========================
num_actgx<-vector();num_nx<-vector(); pass_fail<-vector()
runPath1 = paste(runPath,"covidseq_output/Sample_Analysis/",sep ="/")
num_actgx = 0; num_nx = 0;
n
head(summary1,20)

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

head(num_actgx)
num_actgx

df_new <- as.data.frame(cbind(as.character(num_actgx), as.character(num_nx),pass_fail)); 
df_new<-df_new %>% dplyr::rename(num_actg = 1, num_n = 2)
summary<-cbind(summary1,df_new);

# Adding info to the summary file
# ==============================
summary<-merge(summary,df4, by.x = "df1", by.y = "SampleID", all.x = T )
colnames(summary)[1]<-c("SampleNumber")
summary<-cbind(summary,'Run Name'=args[1]) 
#Clarity<-read.csv(paste("/Volumes/NGS/Analysis/covidseq",args[1],"Results.csv",sep ="/"))
Clarity<-read.csv(paste("/Volumes/NGS/Analysis/covidseq/",args[1],"/",args[1],"Results.csv",sep =""))
# paste("/Volumes/NGS/Analysis/covidseq/",args[1],"/",args[1],"Results.csv",sep ="")
# paste("/Volumes/NGS/Analysis/covidseq/",args[1],"/",args[1],"Results.csv",sep ="")
head(Clarity)
Clarityy<-data.frame(Clarity$LIMS_TEST_ID, Clarity$Submission.ID); 
head(Clarityy)

summary_Clarity<-merge(summary,Clarityy,by.x = "SampleNumber", by.y = "Clarity.LIMS_TEST_ID", all.x = T);
head(summary)

summary_Clarity$Sample_ID<-NULL
head(summary_Clarity,2)
ss<-summary_Clarity[c("SampleNumber","Clarity.Submission.ID","lineage","scorpio_call","sc2_amplicons","clade","collectionDate","num_actg","num_n","pass_fail","Nume_reads","Mean_Quality_Score","Run Name")]
colnames(ss)[colnames(ss) == "Clarity.submission.ID"]<-"Sample_ID"
summary<-ss;

# Saving file at /Volumes/NGS/Analysis/covidseq/$runName
# ==========================
d=paste(runPath,'Rsumcovidseq',sep="/");dir.create(file.path(d,"" ), recursive = TRUE); p1<-Sys.time()
dx<- paste(d,'/Rcovidseq_summary-',paste0(Sys.Date(),'-',hour(Sys.time()),'-',minute(Sys.time())),".csv",sep=""); 
write.csv(summary,dx,row.names=FALSE)
cat(crayon::bold$underline("Summary is complete and can be found at: ",d,"\n"))
# info for SARS-CoV-2-Tracking
# =============================

d=paste(runPath,'Rsumcovidseq',sep="/");dir.create(file.path(d,"" ), recursive = TRUE); p1<-Sys.time()

dx<- paste(d,'/NGS_Tracking-',paste0(Sys.Date(),'-',hour(Sys.time()),'-',minute(Sys.time())),".csv",sep=""); 
write.csv(summary,dx,row.names=FALSE)
head(summary,2)

write.csv(dplyr::select(summary,"SampleNumber","Clarity.Submission.ID","collectionDate","Run Name","lineage","num_actg","clade"),dx,row.names=FALSE)
write.csv(dplyr::select(summary,"SampleNumber","collectionDate","Run Name","lineage","num_actg","clade"),dx,row.names=FALSE)

# Generating the submission file
# ==============================
head(summary)
data1<-dplyr::select(summary,"SampleNumber","Clarity.Submission.ID","collectionDate","Run Name","lineage","num_actg")
data2<-subset(data1,num_actg > 1000); head(data2,100)
fwrite(data2, paste(runPath,"submission.csv",sep="/"),row.names = F)

