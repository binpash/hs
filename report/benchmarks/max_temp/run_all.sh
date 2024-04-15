#!/bin/bash

export PATH=$PATH:$HOME/.local/bin
export PASH_SPEC_TOP=${PASH_SPEC_TOP:-$(git rev-parse --show-toplevel --show-superproject-working-tree)}
export PASH_TOP=${PASH_TOP:-$PASH_SPEC_TOP/deps/pash}

output_dir="$PASH_SPEC_TOP/report/output/max_temp" # Adjust the path as necessary
download_dir="$PASH_SPEC_TOP/report/resources/max_temp"

./run --target sh-only
mkdir -p $output_dir/base
rm $download_dir/*.txt
mv $output_dir/* $output_dir/base

for window in 0 1 2 4 8 16 32 64 128
do
    ./run --target hs-only --window $window
    rm $download_dir/*.txt
    mkdir -p $output_dir/$window
    mv $output_dir/* $output_dir/$window
done

