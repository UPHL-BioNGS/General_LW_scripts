pathogens=("Campylobacter_jejuni" "Escherichia_coli" "Salmonella_enterica")
for pathogen in ${pathogens[@]}; do
    echo "copying cluster tree and dist files for ${pathogen}"

    full_dist_file_path=/Volumes/NGS_2/Bioinformatics/rsainsbury/bigbacter_new/bigbacter_output/dists/${pathogen}-snp-dist-long.csv

    # code for going through all runs 
    for run in $(ls /Volumes/NGS_2/Bioinformatics/rsainsbury/bigbacter_new/results/ | grep '^[0-9]'); do
        echo "${run}"
        # get the 
        for cluster_tree_file in /Volumes/NGS_2/Bioinformatics/rsainsbury/bigbacter_new/results/${run}/${pathogen}/*/tree/${run}-*-*_snp-tree.nwk; do
            # Cut the the run name and dash
            cluster_tree_name=${cluster_tree_file##*/}
            cluster_tree_new_name=$(echo "${cluster_tree_name//${run}-/}")
            # Copy the file to newname
            cp "$cluster_tree_file" "/Volumes/NGS_2/Bioinformatics/rsainsbury/bigbacter_new/bigbacter_output/cluster_trees/$cluster_tree_new_name"     
        done

        # Concatenate all of the distance matrices together for each pathogen
        for cluster_dist_file in /Volumes/NGS_2/Bioinformatics/rsainsbury/bigbacter_new/results/${run}/${pathogen}/*/dist/${run}-${pathogen}-*_snp-dist-long.csv; do
            # Cut the the run name and dash
            cluster_dist_name=${cluster_dist_file##*/}
            cluster_dist_new_name=$(echo "${cluster_dist_name//${run}-/}")

            # adding cluster dist file to the full dist file for this pathogen
            tail -n +2 "$cluster_dist_file" >> ${full_dist_file_path}

        done
    done

    close_dist_file_path=/Volumes/NGS_2/Bioinformatics/rsainsbury/bigbacter_new/bigbacter_output/dists/${pathogen}-snp-close_dist_with_dup-long.csv
    unique_dist_file_path=/Volumes/NGS_2/Bioinformatics/rsainsbury/bigbacter_new/bigbacter_output/dists/${pathogen}-snp-close_dist-long.csv

    # Remove dists that are over 100 and add header
    awk -F ',' 'BEGIN {print "ID1,ID2,dist"}  $3 <= 100' ${full_dist_file_path} > ${close_dist_file_path}

    # Remove duplicate rows
    awk '!seen[$0]++' ${close_dist_file_path} > ${unique_dist_file_path}

    #removing cluster dist files 
    # rm /Volumes/NGS_2/Bioinformatics/rsainsbury/bigbacter_new/bigbacter_output/dists/${pathogen}-*_snp-dist-long.csv
    #removing long combined dist file
    rm ${full_dist_file_path}
    rm ${close_dist_file_path}

done

#concatenate all summary files together
ls -tr --sort=time /Volumes/NGS_2/Bioinformatics/rsainsbury/bigbacter_new/results/*/*-summary.csv | xargs awk 'NR==1 || FNR!=1'  > /Volumes/NGS_2/Bioinformatics/rsainsbury/bigbacter_new/bigbacter_output/summaries/all-summary.csv
#only keep the most recent instance of each row 
tac /Volumes/NGS_2/Bioinformatics/rsainsbury/bigbacter_new/bigbacter_output/summaries/all-summary.csv | awk '!seen[$1]++' | tac > /Volumes/NGS_2/Bioinformatics/rsainsbury/bigbacter_new/bigbacter_output/summaries/mid-summary.csv

#only keep the unmasked rows (we want Snippy rows not Gubbins)
awk -F, '$17 != "True"' /Volumes/NGS_2/Bioinformatics/rsainsbury/bigbacter_new/bigbacter_output/summaries/mid-summary.csv > /Volumes/NGS_2/Bioinformatics/rsainsbury/bigbacter_new/bigbacter_output/summaries/summary.csv

#removing the all summary file which has duplicates and the mid summary file which has masked results
rm /Volumes/NGS_2/Bioinformatics/rsainsbury/bigbacter_new/bigbacter_output/summaries/all-summary.csv
rm /Volumes/NGS_2/Bioinformatics/rsainsbury/bigbacter_new/bigbacter_output/summaries/mid-summary.csv

