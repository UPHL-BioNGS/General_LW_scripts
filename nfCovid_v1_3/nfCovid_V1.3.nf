#!/usr/bin/env nextflow
nextflow.enable.dsl=2
Basepath = System.getProperty("user.dir")

nextflow.enable.dsl=2
Basepath = System.getProperty("user.dir")

println("") 
println(" ____ _____ __      _____ _____")
println("/ ___|  _  |\\ \\    / /| || __  \\")
println("| |  | | | | \\ \\  / / | || | | |")
println("| |__| |_| |  \\ \\/ /  | || |_| |")
println("\\__ _|_____|   \\_ /   |_||_____/  Wworkflow(nf) for patient samples ")




VERSION = '1.2-July-27'
Author ="Olinto Linares-Perdomo"
LastModified="2023-08-28"
USAGE = "Grouping all the scripts releted to covid data analysis in a worflow. It will be triggered when the illumina analysis phase has completed and the covidseq_complete_nf.txt file has been created, it will be the trigger for this workflow"


println() ;println("Version: " + VERSION) ;println("Author: " + Author)
println("Last modified: " + LastModified); println("USAGE: " + USAGE);println()

params.paramito  = ''


// List of process
//  1: fastas : revise
//  2: cecret_nextclade_pangolin_and_nextstrain_clade : revised
//  3: ngs_summary_tracking_submission_files : revised
//  4: fastas2json : revised
//  5: movingJson : revised
//  6: Dripping_Rock : revised
//  7: UpdatingTrackingFinishedTab
//  8: preparing_files_for_submission : revised
//  9: WGS_meandepth_coverage : it is not necesasrly 
// 10. concatenating_fastas_for_alignment : revised
// 11. mafft_alignment : revised
// 12. tree_for_Phylogenetics_Analysis : revised
// 13. PANGO_lineage_freq : revised
// 14. MetadataTable_Microreact : revised
// 15. viral_proteins_coverage : revised
// 16. ORFs_coverage_ORF6_ORF7a_ORF7b_ORF8_ORF10_nsp14_ORF3a : revised


//  process 1 
process fastas { 
USAGE = """
	This process will collect the fasta files and relocate  them  in a folder for downstream analysis.
       """
input:
  val params.paramito
output:
 val start
 script: start ="$params.paramito"

"""
Rscript /Volumes/NGS_2/Bioinformatics/Covid_related/parFastas.R $params.paramito
"""
 }


//  process 2
process cecret_nextclade_pangolin_and_nextstrain_clade {
USAGE = """
        This process will trigger the Cecret workflow for pangolin and nextsrain-clade clasification.
       """
input:
    val runName
output:
     val start

  script: start = "$params.paramito"
  print("")
 """
 bash /Volumes/NGS_2/Bioinformatics/Covid_related/cCecret.sh $runName
 """
}

// process 3 
process ngs_summary_tracking_submission_files {
USAGE = """
        This process will trigger an  R script that collect data from LIMS (*.NGS last files updated on LIMS) and from the previous process to generte the followings files:
          1. ngs_runName.csv: This file is for surveillance
          2. summary.csv : This file for basic stats
          3. tracking.csv: This  file will be used downstrain to update the tracking system finished tab.
          4. submission.csv: This file has all samples that passed (amplicon > 50)  and will be used downstrain to prepare the data for submission to NCBI 
             (SRA  & GenBank) and GISAID databases.
      """
input:
   val runName
output:
      val start

      script:  start = "$params.paramito"
      println("")
 """
  Rscript /Volumes/NGS_2/Bioinformatics/Covid_related/ngs_summary_tracking_submission_files_ClarityLW8.R $runName
 """
}

//  process 4 
process fastas2json {
USAGE =  """
           Generating the  json  file. It uses a python script but an R script is ready somewhere to be used too
        """
input:
 val runName


output:
 val start
 script: start ="$params.paramito"

script:
print("")
"""
Rscript /Volumes/NGS_2/Bioinformatics/Covid_related/fastas2json.R $runName
"""
}


//  process 5 
process movingJson {

USAGE =  """
           Moving json file from json folder to working_json folder
        """
input:
 val runName

output:
 val start
 script: start ="$params.paramito"

script:
print("")
"""
Rscript /Volumes/NGS_2/Bioinformatics/Covid_related/json2working_json.R $runName
"""

}

// process 6
process Dripping_Rock {
USAGE =  """
           Triggering the Dripping_Rock workflow for daily_medatata build: Kelly
        """
input:
 val runName

script:
print("")
"""
Rscript /Volumes/NGS_2/Bioinformatics/Covid_related/RDripping_RockTriger.R $runName
"""
}


// process 7
process UpdatingTrackingFinishedTab {
USAGE = """
        This process will actualize the tracking systems finished tab
       """
 input:
    val runName 

 script:
 print("")
 """
 Rscript /Volumes/NGS_2/Bioinformatics/Covid_related/ActualizingTrackingFinishedTap.R $runName
 """
 }

// process 8
process preparing_files_for_submission {
USAGE = """
         This process will prepare the data files for submission to NCBI/(SRA &  GenBank) and GISAID Databases
         """
input:
  val runName

output:
  val runName

script: runName ="$params.paramito"
print("s")

"""
bash  //Volumes/NGS_2/Bioinformatics/Covid_related/prepare_submission_baseline_surveillance-2025.sh \
 /Volumes/NGS/Analysis/covidseq/$params.paramito /Volumes/NGS/Analysis/covidseq/$params.paramito/submission.csv
"""
}


//  process 9
process WGS_meandepth_coverage {
USAGE = """
	This process will run RSamtools to compute the WGS coverage, only meandepth will be used to be reported
        """
input:
    val runName
script:
print("")
"""
Rscript /Volumes/NGS_2/Bioinformatics/Covid_related/WGS_coverage.R $runName
"""
}

//  process 10
process concatenating_fastas_for_alignment {
USAGE = """
         This process will concatenate the reference genome with all fastas that passed for future analysis downstream
         """
input:
  val runName

output:
  val runName

script: runName ="$params.paramito"
print("s")

"""
bash /Volumes/NGS_2/Bioinformatics/Covid_related/concatenate_fastas.sh $runName
"""
}

// process 11
process mafft_alignment {
USAGE = """
         This process will align the sequences using MAFFT.
         """
input:
  val runName
output:
  val runName
script: runName ="$params.paramito"
print("s")
"""
Rscript  /Volumes/NGS_2/Bioinformatics/Covid_related/mafft_nf.R $runName

"""
}

// process 12
process tree_for_Phylogenetics_Analysis {
USAGE = """
         This process will generate the tree for phylogenetics analysis/Microreaact using iqtree2
         """
input:
  val runName
output:
  val runName
script: runName ="$params.paramito"
print("s")

"""
Rscript  /Volumes/NGS_2/Bioinformatics/Covid_related/iqtree2_covidData.R $runName

"""
}

// process 13
process PANGO_lineage_freq {
USAGE = """
         This process will generate the frequence of pangolin lineage as a csv file
         """
input:
  val runName
output:
  val runName

script: runName ="$params.paramito"
print("s")

"""
Rscript  /Volumes/NGS_2/Bioinformatics/Covid_related/PANGO_lineage_frequency.R $runName

"""
}

// process 14
process MetadataTable_Microreact {
USAGE = """
         This process will generate the metadata table to be uoloand tin Microreact
         """
input:
  val runName
output:
  val runName

script: runName ="$params.paramito"
print("s")

"""
Rscript  /Volumes/NGS_2/Bioinformatics/Covid_related/MetaDataTable_for_MicroReact.R $runName

"""
}

// process 15
process TsTv_ratio_spike_Protein {
USAGE = """
         This process will generate the TsTv ratio for the Spike protein
         """
input:
  val runName
output:
  val runName

script: runName ="$params.paramito"
print("s")

"""
Rscript  /Volumes/NGS_2/Bioinformatics/Covid_related/TsTv_ratio_Spike.R $runName

"""
}

// process 16
process TsTv_ratio_Envelope_Protein {
USAGE = """
         This process will generate the TsTv ratio for the Nucleocapsid protein
         """
input:
  val runName
output:
  val runName

script: runName ="$params.paramito"
print("s")

"""
Rscript  /Volumes/NGS_2/Bioinformatics/Covid_related//TsTv_ratio_Envelope.R $runName

"""
}

//  process 17
process viral_proteins_coverage {
USAGE = """
         This process will generate the coverage for the more critial virus proteins (S,N,M,E)
         """
input:
  val runName
output:
  val runName

script: runName ="$params.paramito"
print("s")

"""
Rscript  /Volumes/NGS_2/Bioinformatics/Covid_related/Viral_proteins_S_N_M_E_coverage.R $runName

"""
}


//  process 18
process ORFs_coverage_ORF6_ORF7a_ORF7b_ORF8_ORF10_nsp14_ORF3a {
USAGE = """
         This process will generate the coverage for the more critial ORFs parts (ORF6, ORF7a,ORF7b,ORF8,ORF10,nsp14,ORF3a)  
         """
input:
  val runName
output:
  val runName

script: runName ="$params.paramito"
print("s")

"""
Rscript  /Volumes/NGS_2/Bioinformatics/Covid_related/ORFs_coverage.R $runName

"""
}



workflow {

  fastas(params.paramito)

  cecret_nextclade_pangolin_and_nextstrain_clade(fastas.out)

  ngs_summary_tracking_submission_files(cecret_nextclade_pangolin_and_nextstrain_clade.out)

  preparing_files_for_submission(ngs_summary_tracking_submission_files.out)

  viral_proteins_coverage(ngs_summary_tracking_submission_files.out)

  ORFs_coverage_ORF6_ORF7a_ORF7b_ORF8_ORF10_nsp14_ORF3a(viral_proteins_coverage.out)

  UpdatingTrackingFinishedTab(ngs_summary_tracking_submission_files.out)

  concatenating_fastas_for_alignment(fastas.out)

  mafft_alignment(concatenating_fastas_for_alignment.out)

  fastas2json(params.paramito) 

  movingJson (fastas2json.out) 

  Dripping_Rock(movingJson.out) 

  tree_for_Phylogenetics_Analysis(mafft_alignment.out)

  PANGO_lineage_freq(cecret_nextclade_pangolin_and_nextstrain_clade.out)

  MetadataTable_Microreact(ORFs_coverage_ORF6_ORF7a_ORF7b_ORF8_ORF10_nsp14_ORF3a.out)


}

workflow.onComplete {
   println("nfCOVID workflow completed at: $workflow.complete with execution status: ${ workflow.success ? 'OK' : 'failed' }")
 }


