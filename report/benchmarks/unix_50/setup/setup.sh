#!/bin/bash

#set -e

# Setting environment variables
export PATH=$PATH:$HOME/.local/bin
export PASH_SPEC_TOP=${PASH_SPEC_TOP:-$(git rev-parse --show-toplevel --show-superproject-working-tree)}
export PASH_TOP=${PASH_TOP:-$PASH_SPEC_TOP/deps/pash}

# Directory configurations
resource_dir="$PASH_SPEC_TOP/report/resources"
download_dir="$resource_dir/unix_50"
mkdir -p "$download_dir"
cd "$download_dir"

# Define inputs
inputs=(
1 10 11 12 2 3 4 5 6 7 8 9.1 9.2 9.3 9.4 9.5 9.6 9.7 9.8 9.9
)

echo "Preparing unix_50 datasets..."

inflate="$PASH_SPEC_TOP/report/util/inflate.sh"

if [[ ! -f "*.txt" ]]; then
    echo "Downloading unix_50 datasets..."
    wget -r -np -nH --cut-dirs=3 -R "index.html*, robots.txt" https://atlas-group.cs.brown.edu/data/unix50/
fi

for i in ${inputs[@]}; do
    if [[ ! -f "10M_$i.txt" ]]; then
        echo "Inflating $i.txt..."
        $inflate "$i.txt" 1M
        $inflate "1M-$i.txt" 10M
        $inflate "$10M-i.txt" 100M
        $inflate *.txt 1G
    fi
done
