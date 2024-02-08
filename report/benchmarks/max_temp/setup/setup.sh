#!/bin/bash

export PATH=$PATH:$HOME/.local/bin
export PASH_SPEC_TOP=${PASH_SPEC_TOP:-$(git rev-parse --show-toplevel --show-superproject-working-tree)}
export PASH_TOP=${PASH_TOP:-$PASH_SPEC_TOP/deps/pash}

download_dir="$PASH_SPEC_TOP/report/resources/max_temp" # Adjust the path as necessary

# FTP server details
ftp_server="ftp://ftp.ncdc.noaa.gov/pub/data/noaa"
ftp_dir="./"


# Start and end dates
start_year=${1:-1901}
end_year=${2:-1909}

# Create local directory if it doesn't exist
mkdir -p "$download_dir"

# Downloading files
for year in $(seq $start_year $end_year); do
    echo "Fetching files for year $year..."

    # Navigate to the year directory and download all .gz files
    lftp -e "mirror --verbose --parallel=3 $ftp_dir/$year $download_dir/$year; bye" -u anonymous, $ftp_server
done

echo "Files fetched from $start_year to $end_year."
