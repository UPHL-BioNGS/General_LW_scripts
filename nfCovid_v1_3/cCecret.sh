nextflow pull UPHL-BioNGS/Cecret
nextflow run UPHL-BioNGS/Cecret -profile uphl --fastas /Volumes/NGS/Analysis/covidseq/$1/ParFastas/ --outdir /Volumes/NGS/Analysis/covidseq/$1/CecretPangolin/
echo "pangoline lineage is ready"

