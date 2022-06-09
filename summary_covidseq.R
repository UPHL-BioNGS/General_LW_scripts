#!/usr/bin/env Rscript
# Author: OLP/2022
# Usage: 1. summary for PatientSamples on the SampleSheet after the analysis phase is completed
#        2. Arguments: run name
#        3. Example: Rscript / . . . ./summary_v2.R UT-A01290-220416

 
# libraries
library("easypackages")
libraries("tidyverse","XML","xml2","seqinr","lubridate"); 


args = commandArgs(trailingOnly=T)
date<-ymd(substr(args[1], 11, 16));runPath <-paste('/Volumes/NGS/Analysis/covidseq',args[1],sep="/"); 
head(date)
runPath

#=============================================
# Type Of Sequencer : NovaSeq or NextSeq
Sequencer <-substr(args[1], 4, 4); Sequencer; dat<-substr(args[1], 11, 16);dat
if (Sequencer =="A"){ TypeOfSequencer<-"NovaSeq";Pt<-"A01290"} else {TypeOfSequencer<-"NextSeq";Pt<-"NB551133"};Pt; 
t=.5;Sys.sleep(t)

#=============================================
# Path to Analysis
ss1 = paste(runPath,"covidseq_output/SampleSheet_Intermediate.csv",sep ="/"); 
ss2 = paste(runPath,"covidseq_output/lineage/combined_lineage_report.csv",sep ="/"); 
ss3 = paste(runPath,"covidseq_output/Logs_Intermediates/VirusDetection/kmer/Summary.tsv",sep ="/");

#=============================================
df1 = read.csv(ss1); # SampleSheet
df2 = read.csv(ss2); # combined_llineage_report
df3 = read.table(file = ss3, sep = '\t', header = T); # amplicons 

#=============================================
# detecting the lineage tool version from the  main_seq xxxx  script
s<-"/Volumes/NGS/Bioinformatics/dragen_scripts/main_seq_run_v2.sh"
sx = read.csv(s)[(70:70),];
Lineage_tools<- substring(sx, 7,40);
print(Lineage_tools)

#=============================================
# Searching the samplesheet for general info 
instrument_type<-df1[4,2];cat("instrument_type:", instrument_type,"\n");Sys.sleep(t)
wetlab_assay<-df1[5,2]; cat("wetlab_assay:", wetlab_assay,"\n");Sys.sleep(t)
pangolin_version<-df2[1,9];cat("pangolin_version :",pangolin_version,"\n");Sys.sleep(t)
pangoLEARNversion<-df2[1,8];cat("pangoLEARNversion :",pangoLEARNversion,"\n");Sys.sleep(t)
software = "Illumina DRAGEN COVID pipeline (R.U.O.), vs. 1.0.1"; cat("software: ",software,"\n");Sys.sleep(t)
lineage_tools = Lineage_tools;cat ("Lineage tools: ",lineage_tools,"\n");Sys.sleep(t)

#=============================================
#Sequencer Read Type & Read Length from output/ . . . ./RunParameters.xml
pathOutput <-paste("/Volumes/NGS/Output/",Pt,"/",dat,"*/RunParameters.xml",sep='');pathOutput
fileName<-Sys.glob(pathOutput,dirmark = TRUE); 
ReadType<-xmlToDataFrame(nodes=getNodeSet(xmlParse(read_xml(fileName)),"//ReadType"));ReadType
ReadLength<-xmlToDataFrame(nodes=getNodeSet(xmlParse(read_xml(fileName)),"//Read1NumberOfCycles"));ReadLength 

#=============================================
# Number of PatientSample (n); 
df1<-tail(df1,-13);
df1<-df1[,c(1,3)]; 
colnames(df1) <- c("Sample_Accession","Sample_Type");
df1<-filter(df1, Sample_Type == "PatientSample"); 
n<-length(df1$Sample_Type); cat("Number of PatientSamples",n,"\n");Sys.sleep(t)

#=============================================
# Random Number Generator for Sample_ID
RNG<-paste(floor(runif(n, min=99, max=1000)),floor(runif(n, min=99, max=1000)),sep =""); 

#============================================
# Checking for duplicates in RNG
while(length(RNG)!= length(unique(RNG)))
     { RNG<-paste(floor(runif(n, min=99, max=1000)),floor(runif(n, min=99, max=1000)),sep ="");}
IDD<-paste("UT-UPHL",substr(args[1], 11, 16),sep="-");
Sample_ID<-paste(IDD,RNG,sep=""); 
summary1<-cbind(df1,Sample_ID);
head(summary1)

#============================================
#left join: SampleSheet & Combined Lineage Report files
var <-paste('',args[1],sep='-'); head(var)
df2 <-df2 %>% mutate_at("taxon", str_replace, var, "")
df2<-df2[,c("taxon","lineage","scorpio_call")]
head(df2); #Taxon, lineage, scorpio_call
df3 = read.table(file = ss3, sep = '\t', header = TRUE); # 
df3<-df3 %>% mutate_at("Sample", str_replace, var, ""); head(df3)
df3<-df3[,c("Sample","nTargetsDetected.SARS.CoV2")]; 
colnames(df3)[2] <- 'sc2_amplicons';#
summary1<-merge(summary1,df2, by.x="Sample_Accession", by.y= "taxon", all.x=TRUE); 
head(summary1)
summary1<-merge(summary1,df3, by.x="Sample_Accession", by.y= "Sample", all.x=TRUE);

#==========================================
# adding generalc information: 
summary1<-cbind(summary1,'wetlab_assay'= wetlab_assay,"instrument_type"=instrument_type,"software"=software,"lineage_tools"=lineage_tools,
                "pangolin_version"=pangolin_version,'read_Type' = ReadType,"readLength" = ReadLength)
                colnames(summary1)[12]<-("Read_Type");
                colnames(summary1)[13]<-("Read_Length");
                head(summary1)

#==========================================
# Nucleotides count: (num_actg & num_n
num_actgx<-vector();num_nx<-vector(); pass_fail<-vector()
runPath1 = paste(runPath,"covidseq_output/Sample_Analysis/",sep ="/"); 
num_actgx = 0; num_nx = 0;
for (i in 1:n){
     sample=summary1$Sample_Accession[i]; 
     amplicons=summary1$sc2_amplicons[i];
      if(amplicons >=50)
      { 
        Lyapunovv<- Sys.glob(paste(runPath1,sample,"*/*.fasta",sep = ""),dirmark = TRUE); 
        a =  str_count(read.fasta(Lyapunovv, as.string = T, forceDNAtolower = T), pattern = "a|c|t|g");num_actgx[i] = a;
        b =  str_count(read.fasta(Lyapunovv, as.string = T, forceDNAtolower = T))-a; num_nx[i] = b; pass_fail[i] ="pass"; c = "pass"
      }
      else {# AmpliconThereshold <50, 
             a = b =0; num_actgx[i] = 0; num_nx[i] = 0; pass_fail[i] ="fail"; c = "fail"
           }
     cat(sample," \t",a,"\t",b,"\t",c,"\n")
}

head(summary1)
df_new <- cbind(as.character(num_actgx), as.character(num_nx),pass_fail); 
summary<-cbind(summary1,df_new); 
colnames(summary)[14]<-("num_actg");colnames(summary)[15]<-("num_n"); 

#========================================
# # Creating a directory and storing results
d=paste(runPath,'R-sumcovidseq',sep="/");dir.create(file.path(d,"" ), recursive = TRUE); p1<-Sys.time(); 
LL<-paste(substring(p1, 1,10),substring(p1, 12,13),substring(p1, 15,16),substring(p1, 18,19),sep = "-")
dx<- paste("Rcovidseq_summary",LL,".csv",sep="-");
dxx<-paste(d,dx, sep ='/');
write.csv(summary,dxx,row.names=FALSE)
cat("Summary file is complete and can be found at: ",d)
