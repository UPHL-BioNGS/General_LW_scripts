#!/usr/bin/env python3

run_name = str(sys.argv[1])
run_type = str(sys.argv[2])


# Function to loop through files needed to be downloaded for each analysis.
def ica_download(run_type):
    if 'mycosnp':
        bashCommand = "icav2 projects enter Testing"
        process = subprocess.Popen(bashCommand.split(" ",3), stdout=subprocess.PIPE)
        process.communicate()

        bashCommand = "icav2 projectdata list --file-name %s --match-mode FUZZY" % run_name
        tmp= icav_out(bashCommand)
        for i in tmp:
            try:
                bashCommand = "./icav2 projectdata list --parent-folder %sResults/" % i.split()[0]
                tmp= icav_out(bashCommand)
                target_dir= i.split()[0]
                break
            except:
                pass
        for i in ['Results/stats/*','Results/multiqc_report.html','Results/combined/*']:
            bashCommand = "icav2 projectdata download %s%s /Volumes/IDGenomics_NAS/fungal/%s/" % (target_dir,i, run_name)
            process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
            process.communicate()
    if 'granduer':
        bashCommand = "icav2 projects enter Produciton"
        process = subprocess.Popen(bashCommand.split(" ",3), stdout=subprocess.PIPE)
        process.communicate()

        bashCommand = "icav2 projectdata list --file-name %s --match-mode FUZZY" % run_name
        tmp= icav_out(bashCommand)
        for i in tmp:
            try:
                bashCommand =  "./icav2 projectdata list --parent-folder %sgrandeur/" % i.split()[0]
                tmp= icav_out(bashCommand)
                target_dir= i.split()[0]
                break
            except:
                pass
        for i in ['grandeur/*']:
            bashCommand = "icav2 projectdata download %s%s /Volumes/IDGenomics_NAS/fungal/%s/" % (target_dir,i, run_name)
            process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
            process.communicate()

ica_download(run_type)
