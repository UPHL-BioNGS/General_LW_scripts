#!/usr/bin/env Rscript
# Author: OLP/01/2022
# Usage: Getting metadata for ngs file
# Parameter: Run Name ;  i.e. Rscript ngs&summary.R UT-VH0770-230212
# last modified on 23/06/02
library("Biostrings")
library(seqinr)



directory_path <- "/Volumes/NGS/Analysis/covidseq/UT-VH00770-240726/ParFastas/"; # parfastas
directory_path_reference <- "/Volumes/NGS/" ; # reference]



#aligned_output.fasta

# List all FASTA files in the directory
fasta_files <- list.files(path = directory_path, pattern = "\\.fasta$|\\.fa$", full.names = TRUE); # fasta_files
# Initialize an empty vector to store concatenated content
concatenated_fasta <- character()

# Loop through each file and concatenate its content
for (file in fasta_files) {
  file_content <- readLines(file)
  concatenated_fasta <- c(concatenated_fasta, file_content)
}

 concatenated_fasta


# including the reference at the top
fasta_files_ref <- list.files(path = directory_path_reference, pattern = "\\.fasta$|\\.fa$", full.names = TRUE)
for (file in fasta_files_ref) {
  file_content <- readLines(file)
  file_content
  concatenated_fasta_all <- c(file_content, concatenated_fasta)
}

concatenate_s.fasta <- concatenated_fasta_all;
concatenated_fasta_all;


sequences<-concatenated_fasta_all


# Write the sequences to a temporary file
input_file <- tempfile(fileext = ".fasta")



writeLines(sequences, input_file)

# Define the output file
output_file <- tempfile(fileext = ".fasta")

# Run MAFFT using a system call
system(paste("mafft --auto", input_file, ">", output_file))

# Read the aligned sequences
aligned_sequences <- readLines(output_file)

# Print the aligned sequences
cat(aligned_sequences, sep = "\n")



# to save
# Specify the output file path
output_file <- "/Volumes/NGS/Analysis/covidseq/UT-VH00770-240726/ParFastas/aligned_sequences_output.fasta"



sequences_named<-aligned_sequences;
# Save to FASTA file
write.fasta(sequences_named, names = names(sequences_named), file.out = "/Volumes/NGS/Analysis/covidseq/UT-VH00770-240726/ParFastas/Paramito-aligned_sequences.fasta")


