# to take only th Spike protein sequence
library("Biostrings")
library("vcfR")
library("dplyr")
# reference
reference_genome <- readDNAStringSet("/Volumes/NGS/Analysis/Mic-Covid/reference.fasta")
reference_spike <- subseq(reference_genome, start=21563, end=25384);
writeXStringSet(reference_spike, "/Volumes/NGS/Analysis/covidseq/UT-VH00770-240830/ParFastas/reference_spike.fa")


# working with the spike protein
folder_path <- "/Volumes/NGS/Analysis/covidseq/UT-VH00770-240830/ParFastas2/"
fasta_files <- list.files(path = folder_path, pattern = "\\.fasta$", full.names = F)
fastas<-as.data.frame(fasta_files);
fastas

n <-nrow(fastas); vec<-vector(); sampl<-vector();n
for (i in 1:n){
 fasta<-fastas[i,1]
 path2<-paste("/Volumes/NGS/Analysis/covidseq/UT-VH00770-240830/ParFastas2",fasta,sep = "/"); path2
 sequence <- readDNAStringSet(path2)
 Spike <- subseq(sequence, start=21563, end=25384);
 name_spike<-paste(str_sub(fasta,1,7),"S.fasta",sep="_"); name_spike
 writeXStringSet(Spike, paste("/Volumes/NGS/Analysis/covidseq/UT-VH00770-240830/ParFastas2",name_spike,sep="/"))
  }



##  To coount the number of mutations in the spike protein using vcf file
#  Detecting the total number of mutations in the sample and how many mutations are in the spike protein, and looking for specific mutations


folder_path <- "/Volumes/NGS/Analysis/covidseq/UT-VH00770-240830/ParFastas2/"
fasta_files <- list.files(path = folder_path, pattern = "\\.fasta$", full.names = F)
fastas<-as.data.frame(fasta_files);
fastas
library(Rsamtools)
fastas
n
find *.fastasample_mutations<-vector()
mutations_in_spike<-vector()
mutations_in_Envelope<-vector()
mutations_in_Membrane<-vector()
mutations_in_Nuclecapsid<-vector()



for (i in 1:n){
  fasta<-fastas[i,1]
  id<-str_sub(fasta,1,7); id
  pathx<-paste(id,"vcf.gz",sep="."); pathx
  vcf_file<-paste("/Volumes/NGS/Analysis/covidseq/UT-VH00770-240826/covidseq_output/Logs_Intermediates/VariantCalling",id,pathx,sep="/"); vcf_file
  #sequence <- readDNAStringSet(path2); sequence
  #vcf_data <- scanTabix(tabix_file, param = region)
  vcf_data<-readVcf(vcf_file)
  #head(vcf_data)
  #head(rowRanges(vcf_data),56)
  #geno(vcf_data)$GT; geno # ojo---here apper the D614G ( 23403_A/G) A23403G
  vcf_df<-as.data.frame(rowRanges(vcf_data))
  #class(vcf_df)
  print(length((rowRanges(vcf_data))))
  sample_mutations[i] = length((rowRanges(vcf_data)))
  #vcf_df[1:1]
  aa<-vcf_df; 
  aa[,2]
        mutations_in_spike[i]<-sum(aa[,2]>=21563 & aa[,2]<=25384);print(sum(aa[,2]>=21563 & aa[,2]<=25384))
  mutations_in_Nuclecapsid[i]<-sum(aa[,2]>=28274 & aa[,2]<=29533);print(sum(aa[,2]>=28274 & aa[,2]<=29533))  
     mutations_in_Envelope[i]<-sum(aa[,2]>=26245 & aa[,2]<=26472);print(sum(aa[,2]>=26245 & aa[,2]<=26472))
     mutations_in_Membrane[i]<-sum(aa[,2]>=26523 & aa[,2]<=27191);print(sum(aa[,2]>=26523 & aa[,2]<=27191))
  #print(mutations_in_spike)
  #spike_mutations[i] = mutations_in_spike
  
}

  sample_mutations;
  mutations_in_spike;
  mutations_in_Nuclecapsid;
  mutations_in_Envelope;
  mutations_in_Membrane;

  fasta<-fastas[i,1]
id<-str_sub(fasta,1,7); id
pathx<-paste(id,"vcf.gz",sep="."); pathx
vcf_file<-paste("/Volumes/NGS/Analysis/covidseq/UT-VH00770-240816/covidseq_output/Logs_Intermediates/VariantCalling",id,pathx,sep="/"); vcf_file
#sequence <- readDNAStringSet(path2); sequence
#vcf_data <- scanTabix(tabix_file, param = region)
vcf_data<-readVcf(vcf_file)
head(vcf_data)
head(rowRanges(vcf_data),56)
geno(vcf_data)$GT; geno # ojo---here apper the D614G ( 23403_A/G) A23403G
vcf_df<-as.data.frame(rowRanges(vcf_data))
class(vcf_df)
print(length((rowRanges(vcf_data))))
vcf_df[1:1]
aa<-vcf_df; aa[,2]
sample_mutations<-length(aa[,8]); sample_mutations
vec<-aa[,2]; vec
mutations_in_spike<-sum(vec>21563 & vec<25384);mutations_in_spike

