#!/bin/bash

# Set error handling
set -e

# Set environment variables
export PATH=$PATH:$HOME/.local/bin
export PASH_SPEC_TOP=${PASH_SPEC_TOP:-$(git rev-parse --show-toplevel --show-superproject-working-tree)}
export PASH_TOP=${PASH_TOP:-$PASH_SPEC_TOP/deps/pash}

# Directory setup
resource_dir="$PASH_SPEC_TOP/report/resources"
download_dir="$resource_dir/bio"
mkdir -p "$download_dir"

# Default input file
default_input_file="$PASH_SPEC_TOP/report/benchmarks/bio/setup/input.txt"

# Color setup for warning messages
RED='\033[0;31m'
NC='\033[0m'

# Function to check and install samtools
check_install_samtools() {
    if ! dpkg -s samtools >/dev/null 2>&1; then
        echo "Installing samtools..."
        sudo apt-get install samtools
    fi

    local version=$(dpkg -s samtools | grep Version)
    # if [[ ! $version == "Version: 1.13" ]]; then
    #     printf "${RED}Invalid Samtools Version\n"
    #     printf "Samtools Version: 1.13 IS required${NC}\n"
    #     exit 1
    # fi
}

# Function to process input file and download BAM files
download_bam_files() {
    local input_file=$1
    while IFS=' ' read -r pop sample link; do
        if [[ ! -f "$download_dir/$sample.bam" ]]; then
            echo "Downloading $sample..."
            wget -O "$download_dir/$sample.bam" "$link"
        fi
    done < "$input_file"
}

# Parse command-line arguments
input_file=$default_input_file
while getopts ":i:c" opt; do
    case $opt in
        i) input_file=$OPTARG ;;
        c) 
            echo "Cleaning up..."
            rm -rf "$download_dir"/*.bam
            rm -rf "$download_dir"/*.sam
            rm -rf "$download_dir"/../output
            exit 0
            ;;
        \?) echo "Invalid option -$OPTARG" >&2
            exit 1
            ;;
    esac
done

# Main script execution
check_install_samtools
download_bam_files "$input_file"
