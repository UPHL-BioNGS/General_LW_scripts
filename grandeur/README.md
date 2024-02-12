# Getting Grandeur results where they need to go

Once Grandeur is done running, `grandeur_results_files.py` is intended to format the results into something easy for
- The google sheet where we store results (specifically the 'Finished' and 'ARLN_regional')
- Labware 8

Dependencies for grandeur_results_files.py (argparse and os _should_ be contained in python3)
- argparse
- os
- pandas

## USAGE
```
python3 grandeur_results_files.py -g <directory with grandeur results> -s <sample sheet from basespace>
```

This is specific to results from running Grandeur on the MiSeq and currently does not work with Sample Sheets from the other machines.

## Additional scripts
`download_reads_basespace.py` is a python script that I put together to get or upload the sample sheet and fastq files from basespace.

Dependencies for download_reads_basespace.py (python packages _should_ already be part of python3)
- argparse
- subprocess
- concurrent.futures
- os
- bs with a default set for basespace
- icav2 access

