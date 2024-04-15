#!/bin/bash

export PATH=$PATH:$HOME/.local/bin
export PASH_SPEC_TOP=${PASH_SPEC_TOP:-$(git rev-parse --show-toplevel --show-superproject-working-tree)}
export PASH_TOP=${PASH_TOP:-$PASH_SPEC_TOP/deps/pash}

output_dir="$PASH_SPEC_TOP/report/output/max_temp" # Adjust the path as necessary
download_dir="$PASH_SPEC_TOP/report/resources/max_temp"
result_dir="$PASH_SPEC_TOP/results/dgsh"

./run --target sh-only
rm $download_dir/*.txt
mkdir -p $result_dir/base
mv $output_dir/* $result_dir/base

for window in 0 1 2 4 8 16 32 64 128
do
    ./run --target hs-only --window $window
    rm $download_dir/*.txt
    mkdir -p $result_dir/$window
    mv $output_dir/* $result_dir/$window
done

