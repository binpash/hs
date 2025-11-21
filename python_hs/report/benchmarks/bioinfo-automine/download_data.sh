#!/bin/bash

# Setup script with inlined data file for benchmark

#Author: Hamid D. Ismail, Ph.D.
#Book title: Bioinformatics of Autoimmune Diseases
# TODO: Filter this to only the ones we end up using for the script.
sra_ids=(
    SRR26147696
    # SRR26147697
    # SRR26147702
    # SRR26147714
    # SRR26147715
    SRR26147716
)
# to top directory of this script
cd -- "$(dirname -- "${BASH_SOURCE[0]}")" || exit
# to the report directory
cd ../../ || exit

data_dir="$(readlink -f "data/bioinfo-automine")"

mkdir -p "$data_dir"
cd "$data_dir" || exit


# Install fasterq-dump if not available
if ! dpkg -l | grep sra-toolkit > /dev/null; then
    sudo apt-get update && sudo apt-get install -y sra-toolkit
fi

# Set number of threads
threads=8
# Download paired-end FASTQ files using fasterq-dump
for sra_id in "${sra_ids[@]}"; do
    echo "Downloading $sra_id with $threads threads..."
    fasterq-dump --split-files --threads "$threads" --verbose "$sra_id"
    gzip "${sra_id}_1.fastq" "${sra_id}_2.fastq"
done

echo "Download completed."
touch "$data_dir/.downloaded"
