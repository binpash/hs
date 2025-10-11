#!/bin/bash

# Setup script with inlined data file for benchmark

#Author: Hamid D. Ismail, Ph.D.
#Book title: Bioinformatics of Autoimmune Diseases

sra_ids=(
    SRR26147696
    SRR26147697
    SRR26147702
    SRR26147714
    SRR26147715
    SRR26147716
)
# to top directory of this script
cd -- "$(dirname -- "${BASH_SOURCE[0]}")" || exit
# to the benchmark directory
cd .. || exit

data_dir="$(readlink -f "data/bioinfo-automine")"

if [ -d "$data_dir" ]; then
    echo "directory $1 already exists, skipping download."
fi

mkdir -p "$data_dir"
cd "$data_dir" || exit

# Check if fasterq-dump is available
if ! command -v fasterq-dump &>/dev/null; then
    echo "Error: fasterq-dump is not installed or not in PATH."
    exit 1
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
