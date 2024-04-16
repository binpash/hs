#!/bin/bash

export PATH=$PATH:$HOME/.local/bin
export PASH_SPEC_TOP=${PASH_SPEC_TOP:-$(git rev-parse --show-toplevel --show-superproject-working-tree)}
export PASH_TOP=${PASH_TOP:-$PASH_SPEC_TOP/deps/pash}

download_dir="$PASH_SPEC_TOP/report/resources/max_temp" # Adjust the path as necessary


# Loop through the years from 2000 to 2018
for year in {2000..2020}; do
    # Create the URL for the specific year
    url="ftp://ftp.ncdc.noaa.gov/pub/data/noaa/$year"

    # Create a temporary directory for each year
    mkdir -p "$year"

    # Download files from the current year's directory
    lftp -c "open '$url' && mirror --parallel=5 --verbose . '$year'"
done
