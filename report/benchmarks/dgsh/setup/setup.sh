#!/bin/bash

export PATH=$PATH:$HOME/.local/bin
export PASH_SPEC_TOP=${PASH_SPEC_TOP:-$(git rev-parse --show-toplevel --show-superproject-working-tree)}
export PASH_TOP=${PASH_TOP:-$PASH_SPEC_TOP/deps/pash}

resource_dir="$PASH_SPEC_TOP/report/resources"
download_dir="$resource_dir/dgsh"



mkdir -p "$download_dir"

cd "$download_dir"

echo "Downloading dgsh datasets..."

if [[ ! -f dblp.xml ]]; then
    wget -nc https://atlas-group.cs.brown.edu/data/dblp/dblp.xml.gz
    gunzip dblp.xml.gz
    cat dblp.xml | head -n 1000000 > mini.xml
fi

if [[ ! -f fid ]]; then
    wget -nc -O "trade.zip"  https://www.stats.govt.nz/assets/Uploads/International-trade/International-trade-December-2020-quarter/Download-data/international-trade-december-2020-quarter-csv.zip
    unzip -j "trade.zip"
    rm -rf "trade.zip"
fi

# Inputs for #5, #6, #8
if [[ ! -f pg100.txt ]]; then
    wget -nc https://www.gutenberg.org/cache/epub/100/pg100.txt
    touch larger_file.txt
    for i in {1..10}; do 
        cat pg100.txt >> larger_file.txt
    done
fi

# Inputs for #7
if [[ ! -f weblog.log ]]; then
    wget -nc -O weblog.log https://raw.githubusercontent.com/elastic/examples/master/Common%20Data%20Formats/apache_logs/apache_logs
    touch larger_weblog.log
    for i in {1..10}; do 
        cat weblog.log >> larger_weblog.log
    done
fi

# Inputs for #1
if [[ ! -f ai4math-mathematical-qa-dataset.zip ]]; then
    kaggle datasets download thedevastator/ai4math-mathematical-qa-dataset
    unzip -j ai4math-mathematical-qa-dataset.zip
    rm -rf ai4math-mathematical-qa-dataset.zip
fi

# Inputs for #2, #3
git clone https://github.com/kelsny/overcommitted
git clone https://github.com/torvalds/linux
