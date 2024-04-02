#!/bin/bash

export PATH=$PATH:$HOME/.local/bin
export PASH_SPEC_TOP=${PASH_SPEC_TOP:-$(git rev-parse --show-toplevel --show-superproject-working-tree)}
export PASH_TOP=${PASH_TOP:-$PASH_SPEC_TOP/deps/pash}

inflate="$PASH_SPEC_TOP/report/util/inflate.sh"

resource_dir="$PASH_SPEC_TOP/report/resources"
download_dir="$resource_dir/dgsh"



mkdir -p "$download_dir"

cd "$download_dir"

echo "Downloading dgsh datasets..."

# #1
if [[ ! -f "dblp.xml" ]]; then
    wget -nc https://atlas-group.cs.brown.edu/data/dblp/dblp.xml.gz
    gunzip dblp.xml.gz
    $inflate dblp.xml 1G
fi

# 17
if [[ ! -f "goods_classification.csv" ]]; then
    wget -nc -O "trade.zip"  https://www.stats.govt.nz/assets/Uploads/International-trade/International-trade-December-2020-quarter/Download-data/international-trade-december-2020-quarter-csv.zip
    gunzip -j "trade.zip"
    rm -rf "trade.zip"
    $inflate goods_classification.csv 1G
fi

# Inputs for #5, #6, #8
if [[ ! -f pg100.txt ]]; then
    wget -nc https://www.gutenberg.org/cache/epub/100/pg100.txt
    $inflate pg100.txt 1G
fi

# Inputs for #7
if [[ ! -f weblog.log ]]; then
    wget -nc -O weblog.log https://raw.githubusercontent.com/elastic/examples/master/Common%20Data%20Formats/apache_logs/apache_logs
    $inflate weblog.log 1G
fi

# Inputs for #2, #3
git clone https://github.com/kelsny/overcommitted
git clone https://github.com/FFmpeg/FFmpeg.git
