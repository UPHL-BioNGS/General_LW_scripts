#!/usr/bin/env python3

"""
Author: Erin Young
Released: 2023-01-27
Version: 0.0.20230127

Description:
This script takes the results from Grandeur and
1) generates the email text for a run
2) formats the results for labware

EXAMPLE:
python3 results.py directory
"""

import pandas as pd
import sys
import os

if len(sys.argv) < 2:
    print("directory not found!") 
    print("USAGE: python3 results.py $directory")
    exit(1)

out=str(sys.argv[1])
sample_sheet    = out + "/SampleSheet.csv"
grandeur_output = out + "/grandeur/summary/grandeur_extended_summary.tsv"
amrfinder       = out + "/grandeur/amrfinderplus/amrfinderplus_summary.csv"

if not os.path.exists(out):
    print("FATAL: Directory of results does not exist")
    exit(1)

if not os.path.exists(sample_sheet):
    print("FATAL: SampleSheet.csv from basespace not found!")
    exit(1)

if not os.path.exists(grandeur_output):
    print("FATAL: Grandeur output not found!")
    exit(1)

df = pd.read_csv(sample_sheet)
print(df)