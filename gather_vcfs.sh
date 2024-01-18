# Author: Tom Iverson
# Released: 2023-11-30
# Version: 1.0.0
# Description: This script's main functionality is to gather sample vcf files from mycoSNP result directories for use in WGS analysis requests.
# The user must create an empty 'vcf_files' directory and 'samples.txt' file in the same location/directoy as this gather_vcfs.sh script
# The 'samples.txt' file should contain 2 tab-seperated columns. The 1st being the sample ids and the 2nd the run ids. Example: 302****	UT-M07101-2112**
# Example of use: bash gather_vcfs.sh

# Filter out any empty lines from samples.txt and overwrite it
grep . samples.txt > temp.txt && mv temp.txt samples.txt

# Function to copy vcf files over from fungal directory
copy_files() {
    sample_id="$1"
    run_id="$2"
    
    # Search for the files and copy them only if they don't exist in the destination
    file_found=$(find "/Volumes/IDGenomics_NAS/fungal/${run_id}/" -type f \( -name "${sample_id}*.g.vcf.gz" -o -name "${sample_id}*.g.vcf.gz.tbi" \) \
    -exec sh -c 'dst="vcf_files/$(basename {})"; [ ! -f "$dst" ] && cp {} "$dst" && echo "$dst"' \;)
    
    # If no files found in the primary directory, look in the secondary directory of vcf files
    if [ -z "$file_found" ]; then
        file_found=$(find "/Volumes/IDGenomics_NAS/fungal/mycosnp_vcfs_211208-230726" -type f \( -name "${sample_id}*.g.vcf.gz" -o -name "${sample_id}*.g.vcf.gz.tbi" \) \
        -exec sh -c 'dst="vcf_files/$(basename {})"; [ ! -f "$dst" ] && cp {} "$dst" && echo "$dst"' \;)
    fi
    
    # Print success or failure message
    if [ -z "$file_found" ]; then
        echo "Failed to copy VCF for sample: $sample_id"
    else
        echo "Successfully copied VCF for sample: $sample_id"
    fi
}

# Export the function for parallel to access
export -f copy_files

# Use parallel to invoke the function for each line in the file
cat samples.txt | parallel --colsep "\t" copy_files {1} {2}


