#!/bin/bash


# i.e: 
#

display_usage() {
	echo -e "Concatenate reeference and fasta files from parFastas for dowmstream analysis: MAFFT-iqtree2-Microreact"
	}


runName=$1
reference="/Volumes/NGS/reference.fasta" # reference genome
cat "$reference"
fastas_dir="/Volumes/NGS/Analysis/covidseq/$runName/ParFastas"
output_file="/Volumes/NGS/Analysis/covidseq/$runName/concatenate_for_alignment.fasta"
cat "$reference" "$fastas_dir"/3*.fasta > "$output_file"
echo "All FASTA file have been concatenated into $output_file." 




 
