#!/bin/bash

export PATH=$PATH:$HOME/.local/bin
export PASH_SPEC_TOP=${PASH_SPEC_TOP:-$(git rev-parse --show-toplevel --show-superproject-working-tree)}
export PASH_TOP=${PASH_TOP:-$PASH_SPEC_TOP/deps/pash}

resource_dir="$PASH_SPEC_TOP/report/resources"
download_dir="$resource_dir/bus-analytics"

cd "$download_dir"

if [ ! -f bus.csv ]; then
    echo "Downloading full-size dataset..."
    wget -nc -O bus.csv.bz2 'https://www.balab.aueb.gr/~dds/oasa-2021-01-08.bz2'
    if [[ -f bus.csv.bz2 ]]; then
        echo "Decompressing full-size dataset..."
        bzip2 -d bus.csv.bz2
    fi
else
    echo "Full-size dataset already exists."
fi
