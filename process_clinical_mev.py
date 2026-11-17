import pandas as pd
import os
import subprocess
import argparse

def main():
    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(description="Convert Cecret results to LIMS import format.")
    
    # Positional arguments (or use flags like --run_name if preferred)
    parser.add_argument("-r", "--run_name", required=True, help="Name of the run (e.g., UT-VH00770-251017)")
    parser.add_argument("-d", "--date", required=True, help="Date for submission, formatted like: 2026-11-09")
    parser.add_argument("-s","--stage",required=True, help="Stage of submission process. Options include: 'sra','genbank', and 'ncbi_lw8'")
    args = parser.parse_args()

    run_name = args.run_name
    submission_date = args.date
    stage = args.stage
    run_dir = f"{run_name}-mev"
    analysis_dir = f"/Volumes/NGS_2/measles/{run_dir}"

    lw8_export_file = f"{analysis_dir}/{run_name}_export.csv"
    lw8_export = pd.read_csv(lw8_export_file)

    submission_dir = f"/Volumes/NGS_2/measles/submissions/{submission_date}"
    submission_attributes_dir = f"{submission_dir}/attributes"
    os.makedirs(submission_attributes_dir, exist_ok=True)

    cecret_sample_sheet = pd.read_csv(f"{analysis_dir}/cecretsamplesheet.csv")

    # Reading in cecret results
    cecret_results = pd.read_csv(f"{analysis_dir}/cecret/cecret_results.csv")
    cecret_results["assembly_coverage"] = (
        1 - cecret_results["num_N"] / cecret_results["num_total"]
    )

    if stage == "sra":
        print("Preparing files for SRA")
        #### Renaming Consensus files

        renamed_consensus_dir = f"{analysis_dir}/renamed_consensus"
        os.makedirs(renamed_consensus_dir, exist_ok=True)

        renaming_cons_subs_sed_file = f"{renamed_consensus_dir}/subs.sed"

        # filtering the lw_export to only test ids that have over 75% coverage and that are D8
        lw8_export_consensus = lw8_export[
            lw8_export["Test.Lims Test Id"].isin(
                pd.to_numeric(
                    cecret_results[
                        (cecret_results["assembly_coverage"] > 0.75)
                        & (cecret_results["nextclade_clade"] == "D8")
                    ]["sample_id"].tolist()
                )
            )
        ]

        # outputting subs.sed file for replacing names in consensus files
        (
            "s/"
            + lw8_export_consensus["Test.Lims Test Id"].astype(str)
            + "/"
            + lw8_export_consensus["Sample.Sample Number"].astype(str)
            + "/"
        ).to_csv(renaming_cons_subs_sed_file, index=False, header=False)

        # outputting samples.tsv for renplacing names in consensus file
        renaming_cons_samples_file = f"{renamed_consensus_dir}/samples.tsv"

        lw8_export_consensus[["Test.Lims Test Id", "Sample.Sample Number"]].to_csv(
            renaming_cons_samples_file, index=False, header=False, sep="\t"
        )

        # running bash script to actually copy and rename the files, then remove the subs.sed and samples.tsv files
        bash_script = f"""
            cat {renaming_cons_samples_file} | cut -f 1,2 | xargs -n 2 sh -c  'cat {analysis_dir}/cecret/consensus/"$0".consensus.fa | sed -f {renaming_cons_subs_sed_file} >  {renamed_consensus_dir}/"$1".consensus.fa'
            rm {renaming_cons_samples_file}
            rm {renaming_cons_subs_sed_file}
        """
        subprocess.run(bash_script, shell=True, executable="/bin/bash")

        #### Copy fastq files into submission dir

        submission_fastq_dir = f"{submission_dir}/fastq"
        os.makedirs(submission_fastq_dir, exist_ok=True)
        fastq_list = cecret_results[
            (cecret_results["nextclade_clade"].notna())
            & (cecret_results["nextclade_clade"] != "A")
        ]["sample_id"].tolist()

        # filtering the lw_export to only test ids that are not clade "A" or missing a clade
        lw8_export_fastq = lw8_export[
            lw8_export["Test.Lims Test Id"].isin(pd.to_numeric(fastq_list))
        ]

        # Exporting a samples.tsv for copying over fastq files
        fastq_samples_file = f"{submission_dir}/samples.tsv"

        lw8_export_fastq[["Test.Lims Test Id", "Submission Accession"]].to_csv(
            fastq_samples_file, index=False, header=False, sep="\t"
        )

        # Copying fastq files over and renaming them, then deleting the samples.tsv
        bash_script = f"""
        cat {fastq_samples_file} | parallel --colsep "\t" cp {analysis_dir}/reads/{{1}}*R1*fastq.gz {submission_fastq_dir}/{{2}}_R1.fastq.gz
        cat {fastq_samples_file} | parallel --colsep "\t" cp {analysis_dir}/reads/{{1}}*R2*fastq.gz {submission_fastq_dir}/{{2}}_R2.fastq.gz
        rm {fastq_samples_file}
        """

        subprocess.run(bash_script, shell=True, executable="/bin/bash")

        #### Copy fasta file and table into submission dir

        submission_fasta_dir = f"{submission_dir}/fasta"
        os.makedirs(submission_fasta_dir, exist_ok=True)

        # filtering the lw_export to only test ids that have over 50% coverage and are not clade "A" or missing a clade
        fasta_list = cecret_results[
            (cecret_results["assembly_coverage"] > 0.5)
            & (cecret_results["nextclade_clade"].notna())
            & (cecret_results["nextclade_clade"] != "A")
            & (cecret_results["vadr_p/f"] != "FAIL")
        ]["sample_id"].tolist()

        lw8_export_fasta = lw8_export[
            lw8_export["Test.Lims Test Id"].isin(pd.to_numeric(fasta_list))
        ]

        fasta_subs_sed_file = f"{submission_fasta_dir}/subs.sed"

        # outputting subs.sed file for replacing names in fasta file and table
        (
            "s/"
            + lw8_export_fasta["Test.Lims Test Id"].astype(str)
            + "/"
            + lw8_export_fasta["Submission Accession"].astype(str)
            + "/"
        ).to_csv(fasta_subs_sed_file, index=False, header=False)

        # Copy vadr fasta files over and change ids in file to submission ids

        bash_script = f"""
        cat {analysis_dir}/cecret/vadr/vadr.vadr.pass.fa | sed -f {fasta_subs_sed_file} > {submission_fasta_dir}/ultimate.fa
        cat {analysis_dir}/cecret/vadr/vadr.vadr.pass.tbl | sed -f {fasta_subs_sed_file} > {submission_fasta_dir}/ultimate.tbl
        
        rm {fasta_subs_sed_file}
        """

        subprocess.run(bash_script, shell=True, executable="/bin/bash")

        #### Removing the sequences we aren't submitting

        # exporting removed list file
        remove_list_file = f"{submission_fasta_dir}/remove_list.txt"
        remove_list = cecret_sample_sheet[
            ~cecret_sample_sheet["sample"].isin(
                cecret_results[
                    (cecret_results["assembly_coverage"] > 0.5)
                    & (cecret_results["nextclade_clade"].notna())
                    & (cecret_results["nextclade_clade"] != "A")
                ]["sample_id"].tolist()
            )
        ]["sample"]
        remove_list.to_csv(remove_list_file, index=False, header=False)

        # # potentially change this to match the tsv file so that you don't need seqkit
        # bash_script = f"""
        # seqkit grep -v -f {remove_list_file} {submission_fasta_dir}/ultimate_full.fa > {submission_fasta_dir}/ultimate.fa
        # rm {submission_fasta_dir}/ultimate_full.fa
        # """

        # Removing the excluded samples from the fasta file
        for sample in remove_list:
            bash_script = f"""
            awk '/>{sample}/ {{ inside=1; next }} />/{{ if (inside) {{ inside=0; print; next }} }} !inside {{ print }}' {submission_fasta_dir}/ultimate.fa > temp.txt && mv temp.txt {submission_fasta_dir}/ultimate.fa
            """
            subprocess.run(bash_script, shell=True, executable="/bin/bash")

        # Removing the excluded samples from the five column feature table
        for sample in remove_list:
            bash_script = f"""
            awk '/>Feature {sample}/ {{ inside=1; next }} />Feature/{{ if (inside) {{ inside=0; print; next }} }} !inside {{ print }}' {submission_fasta_dir}/ultimate.tbl > temp.txt && mv temp.txt {submission_fasta_dir}/ultimate.tbl
            """
            subprocess.run(bash_script, shell=True, executable="/bin/bash")

        # Remove the remove list file
        subprocess.run(
            f"rm {remove_list_file}",
            shell=True,
            executable="/bin/bash",
        )

        #### Creating the Biosample attributes file

        biosample_attributes = pd.DataFrame()

        biosample_attributes["sample_name"] = lw8_export["Submission Accession"]
        biosample_attributes["attribute_package"] = "Pathogen.cl"
        biosample_attributes["bioproject_accession"] = "PRJNA1293457"
        biosample_attributes["organism"] = "Morbillivirus hominis"
        biosample_attributes["strain"] = lw8_export["Result.Isolate Name"]
        biosample_attributes["isolate"] = ""
        biosample_attributes["collected_by"] = "UPHL"
        biosample_attributes["collection_date"] = lw8_export["Collection Date"]
        biosample_attributes["geo_loc_name"] = (
            "USA: "
            + lw8_export["Result.Isolate Name"]
            .str.split("/", expand=True)[1]
            .str.split(".", expand=True)[0]
        )  # formatting the Geo Loc Name, based off of the state in Result.Isolate Name from the LW8 export
        biosample_attributes["isolation_source"] = lw8_export["Isolation Source"]
        biosample_attributes["lat_lon"] = "Missing"
        biosample_attributes["host"] = "Homo sapiens"
        biosample_attributes["host_disease"] = "NA"

        # Filter to only the samples we are submitting fastqs for
        biosample_attributes = biosample_attributes[
            biosample_attributes["sample_name"].isin(
                lw8_export[lw8_export["Test.Lims Test Id"].isin(pd.to_numeric(fastq_list))][
                    "Submission Accession"
                ]
            )
        ]

        biosample_attributes.to_csv(
            f"{submission_attributes_dir}/biosample_attributes.tsv", index=False, sep="\t"
        )

        #### Creating the SRA attributes file

        sra_attributes = pd.DataFrame()

        sra_attributes["sample_name"] = lw8_export["Submission Accession"]
        sra_attributes["library_ID"] = lw8_export["Submission Accession"]
        sra_attributes["title"] = (
            "PCR Tiled Amplification of Morbillivirus hominis / Measles"
        )
        sra_attributes["library_strategy"] = "amplicon"
        sra_attributes["library_source"] = "VIRAL RNA"
        sra_attributes["library_selection"] = "PCR"
        sra_attributes["library_layout"] = "paired"
        sra_attributes["platform"] = "ILLUMINA"
        sra_attributes["instrument_model"] = "Illumina iSeq 100"
        sra_attributes["design_description"] = "Artic measles primalscheme 1.0.0"
        sra_attributes["filetype"] = "fastq"
        sra_attributes["filename"] = lw8_export["Submission Accession"] + "_R1.fastq.gz"
        sra_attributes["filename2"] = lw8_export["Submission Accession"] + "_R2.fastq.gz"

        # Filter to only the samples we are submitting fastqs for
        sra_attributes = sra_attributes[
            sra_attributes["sample_name"].isin(
                lw8_export[lw8_export["Test.Lims Test Id"].isin(pd.to_numeric(fastq_list))][
                    "Submission Accession"
                ]
            )
        ]

        sra_attributes.to_csv(
            f"{submission_attributes_dir}/sra_attributes.tsv", index=False, sep="\t"
        )

    if stage == "genbank":
        print("Preparing files for Genbank")
        #### Creating the Genbank source file

        # read in SRA metadata file
        for file in os.listdir(analysis_dir):
            if file.startswith("metadata"):
                sra_metadata = pd.read_csv(os.path.join(analysis_dir, file), delimiter="\t")

        # filtering the lw_export to only test ids that have over 50% coverage and are not clade "A" or missing a clade
        fasta_list = cecret_results[
            (cecret_results["assembly_coverage"] > 0.5)
            & (cecret_results["nextclade_clade"].notna())
            & (cecret_results["nextclade_clade"] != "A")
            & (cecret_results["vadr_p/f"] != "FAIL")
        ]["sample_id"].tolist()

        genbank_source = pd.DataFrame()

        genbank_source["Sequence ID"] = lw8_export["Submission Accession"]
        genbank_source["Organism"] = "Morbillivirus hominis"
        genbank_source["Host"] = "Homo sapiens"
        genbank_source["Geo Loc Name"] = (
            "USA: "
            + lw8_export["Result.Isolate Name"]
            .str.split("/", expand=True)[1]
            .str.split(".", expand=True)[0]
        )  # formatting the Geo Loc Name, based off of the state in Result.Isolate Name from the LW8 export
        genbank_source["Collection Date"] = lw8_export["Collection Date"]
        genbank_source["Collected By"] = "UPHL"
        genbank_source["Strain"] = lw8_export["Result.Isolate Name"]
        genbank_source["BioProject"] = "PRJNA1293457"

        # getting BioSample and SRA accessions and adding them to source df
        genbank_source = genbank_source.merge(
            sra_metadata[["sample_name", "biosample_accession", "accession"]],
            how="left",
            left_on="Sequence ID",
            right_on="sample_name",
        )
        genbank_source["BioSample"] = genbank_source["biosample_accession"]
        genbank_source["SRA"] = genbank_source["accession"]

        genbank_source.drop(
            ["sample_name", "biosample_accession", "accession"], axis=1, inplace=True
        )

        # Filter to only the samples we are submitting fastas for
        genbank_source = genbank_source[
            genbank_source["Sequence ID"].isin(
                lw8_export[lw8_export["Test.Lims Test Id"].isin(pd.to_numeric(fasta_list))][
                    "Submission Accession"
                ]
            )
        ]

        genbank_source.to_csv(
            f"{submission_attributes_dir}/genbank_source.tsv", index=False, sep="\t"
        )

    if stage == "ncbi_lw8":
        print("Preparing NCBI files for LW8")
        #### Making File for putting test results into LW8

        # read in SRA metadata file
        for file in os.listdir(analysis_dir):
            if file.startswith("metadata"):
                sra_metadata = pd.read_csv(os.path.join(analysis_dir, file), delimiter="\t")

        genbank_results = pd.read_csv("genbank.txt", sep=r"\s+", header=None)
        genbank_results.columns = [
            "Genbank Submission ID",
            "Submission Accession",
            "Genbank Accession",
        ]

        # join everything together and export to a comma-seperated file named {run_name}-mev.txt
        accessions_import_df = (
            lw8_export[["Test.Lims Test Id", "Submission Accession"]]
            .merge(
                sra_metadata[["sample_name", "biosample_accession", "accession"]],
                how="left",
                left_on="Submission Accession",
                right_on="sample_name",
            )
            .merge(
                genbank_results[["Submission Accession", "Genbank Accession"]],
                how="left",
            )
        )

        accessions_import_df.drop(
            ["Submission Accession", "sample_name"], axis=1, inplace=True
        )
        accessions_import_df.columns = [
            "LIMS_TEST_ID",
            "BioSample Accession",
            "SRA Accession",
            "GenBank Accession",
        ]
        accessions_import_df = accessions_import_df.fillna("Not Submitted")
        accessions_import_df.to_csv(
            f"{analysis_dir}/{run_name}-mev.txt", index=False, lineterminator="\r\n"
        )

if __name__ == "__main__":
    main()