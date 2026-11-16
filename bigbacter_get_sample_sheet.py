import pandas as pd
import os
import sys
from pathlib import Path
import argparse


# function for getting sample sheet from run name
def get_samples_from_run(run, organisms, pulsenet_dir="/Volumes/NGS_2/pulsenet_and_arln/"):
    # try to read in the grandeur summary file, if it fails return
    try:
        grandeur_summary = pd.read_csv(
            f"{pulsenet_dir}{run}/pubdir/results/grandeur_summary.tsv", sep="\t"
        )
    except: 
        print(f"Could not find a Grandeur summary file for run: {run}, checked here: {pulsenet_dir}{run}/pubdir/results/grandeur_summary.tsv")
        print("(This could be because the run is not yet finished on AWS)")
        return

    # filtering down to only the organisms we care about and samples with over 40x coverage
    grandeur_summary = grandeur_summary[
        grandeur_summary["mash_dist_organism"].isin(organisms)
    ]
    # check that there are some BigBacter organisms in this run, otherwise return
    if grandeur_summary.shape[0] == 0:
        print(f"None of the samples were BigBacter organisms for run: {run}, this run will be appended to the added runs list")
        with open(added_runs_path, "a") as file:
            file.write(run + "\n")
        return
    # check that some of the samples meet the coverage threshold, otherwise return
    grandeur_summary = grandeur_summary[grandeur_summary["coverage"] > 40]
    if grandeur_summary.shape[0] == 0:
        print(f"None of the samples meet the coverage threshold of 40x for run: {run}, this run will be appended to the added runs list")
        with open(added_runs_path, "a") as file:
            file.write(run + "\n")
        return
    
    # adding columns for sample_sheet
    grandeur_summary["taxa"] = grandeur_summary["mash_dist_organism"]
    grandeur_summary["fastq_1"] = (
        pulsenet_dir + run + "/reads/" + grandeur_summary["file"]
    )
    grandeur_summary["fastq_2"] = grandeur_summary["fastq_1"].str.replace("_R1", "_R2")
    grandeur_summary["assembly"] = (
        pulsenet_dir
        + run
        + "/pubdir/results/contigs/"
        + grandeur_summary["sample"].astype(str)
        + "_contigs.fa"
    )

    # checking that files exist
    grandeur_summary["fastq_1"] = grandeur_summary["fastq_1"].apply(
        lambda x: "missing" if not os.path.exists(x) else x
    )
    grandeur_summary["fastq_2"] = grandeur_summary["fastq_2"].apply(
        lambda x: "missing" if not os.path.exists(x) else x
    )
    grandeur_summary["assembly"] = grandeur_summary["assembly"].apply(
        lambda x: "missing" if not os.path.exists(x) else x
    )

    grandeur_summary = grandeur_summary[
        ~grandeur_summary.apply(
            lambda col: col.astype(str).str.contains("missing")
        ).any(axis=1)
    ]

    # check that the dataframe isn't empty after filtering out files that don't exist, if it is empty, return
    if grandeur_summary.shape[0] == 0:
        print(f"Couldn't find the fastq files or assembly files for any samples from run {run}")
        return

    print(f"{grandeur_summary.shape[0]} samples found for run: {run}")
    return grandeur_summary[["sample", "taxa", "assembly", "fastq_1", "fastq_2"]]


def main(): 
    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(description="Create sample sheet for BigBacter from Grandeur run directories")
    # Positional arguments (or use flags like --run_name if preferred)
    parser.add_argument("-s", "--samplesheet", required=True, help="Name for the outputted samplesheet.csv file, typically in this format: samplesheet_all_2026_11_02.csv")
    args = parser.parse_args()

    # Declaring file pathds
    pulsenet_dir = "/Volumes/NGS_2/pulsenet_and_arln/"
    run = "UT-SH00792-261028"
    organisms = ["Escherichia_coli", "Campylobacter_jejuni", "Salmonella_enterica"]
    bigbacter_dir = "/Volumes/NGS_2/Bioinformatics/rsainsbury/bigbacter_new"
    new_sample_sheet_path = f"{bigbacter_dir}/samplesheets/{args.samplesheet}"
    removed_samples_path = f"{bigbacter_dir}/removed_files.txt"
    added_runs_path = f"{bigbacter_dir}/added_runs.txt"


    with open(added_runs_path, "r") as file:
        added_runs = file.read().splitlines()

    print("Finding run directories")
    # getting run directories
    run_dir_paths = [f for f in Path(pulsenet_dir).iterdir() if f.is_dir()] # get all directory paths in pulsenet directory
    run_dir_paths = [str(dir_path) for dir_path in run_dir_paths] # transform to strings
    run_dir_names = [s.removeprefix(pulsenet_dir) for s in run_dir_paths] # remove full path, leaving just the run name
    run_dir_names = [name for name in run_dir_names if name.startswith("UT-")] # filtering to only the run directories
    run_dir_names = [name for name in run_dir_names if not "combined" in name] #filtering out combined runs
    run_dir_names = [name for name in run_dir_names if not name in added_runs] #filtering out runs that have already been added to the BigBacter DB

    # check if there are any runs that haven't been added, if not exit early
    if len(run_dir_names)==0:
        print("There are no new runs that haven't been added to the BigBacter database ")
        sys.exit(0)

    print("Found the following runs that have not been added: ")
    print(run_dir_names)
    # creating samplesheet from list of runs that need to be added
    sample_sheet_list = []
    for run in run_dir_names:
        individual_sample_sheet = get_samples_from_run(run, organisms)
        if isinstance(individual_sample_sheet, pd.DataFrame): # check that it didn't return nothing
            sample_sheet_list.append(individual_sample_sheet)
        
    # check if the sample sheet list is empty, if it is add the runs to the added_runs list and exit early 
    if len(sample_sheet_list) == 0:
        print("There are no samples ready to be added to BigBacter from these runs, check why")
        print("(Run names will need to be added to /Volumes/NGS_2/Bioinformatics/rsainsbury/bigbacter_new/added_runs.txt manually if you don't want them to be checked every time)")
        # with open(added_runs_path, "a") as file:
        #     for run in run_dir_names:
        #         file.write(run + "\n")
        sys.exit(0)

    sample_sheet = pd.concat(sample_sheet_list, ignore_index=True)

    sample_sheet["sample"] = sample_sheet["sample"].apply(lambda x: "'" + str(x) + "'")

    # Saving to csv
    sample_sheet.to_csv(new_sample_sheet_path,index=False)
    print(f"Saved a samplesheet with {sample_sheet.shape[0]} samples to: {new_sample_sheet_path}")

if __name__ == "__main__":
    main()