#!/usr/bin/env python

"""
Author: Tom Iverson
Released: 2023-11-30
Version: 1.0.0
Description:
This script's main functionality is to accurately change the seq id in the vcf-to-fasta file, which is a mycoSNP result file, to the id required in C. auris WGS analysis requests. 
The following files are required in the same directory as this script. 
  1. seqid.txt
  2. copy of the vcf-to-fasta.fasta file that is renamed 'original.fasta
  3. an empty 'corrected.fasta' file to write to
The script takes the tab-seperated 'seqid.txt' file that the user has created with the following headers "current_seqid" and "alternate_seqid" and replaces the sequence identifiers
found in the 'original.fasta' file with the values from the seqid.txt and writes it to the 'corrected.fasta' file. The 'corrected.fasta' file can then be used to create a newick file.
EXAMPLE:
python changeseqids.py
"""

# Import the txt file containing current_seqid and alternate_seqid into a dictionary
dictionary = {}
with open('seqid.txt') as f:
  for line in f:
    values = line.strip().split()
    if len(values) >= 2:
      current_seqid, alternate_seqid = values[:2]
      dictionary[current_seqid] = alternate_seqid

# Open the original fasta file and the corrected fasta file to write to
original_file = 'original.fasta'
corrected_file = 'corrected.fasta'

# Replace the sequence identifiers in the original fasta file with the values from the dictionary
with open(original_file) as f_in, open(corrected_file, 'w') as f_out:
  for line in f_in:
    if line.startswith('>'):
      current_seqid = line.strip()[1:]
      if current_seqid in dictionary:
        f_out.write(f'>{dictionary[current_seqid]}\n')
      else:
        f_out.write(line)
    else:
      f_out.write(line)

