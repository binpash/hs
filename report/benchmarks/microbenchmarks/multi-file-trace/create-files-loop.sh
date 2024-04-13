#!/bin/bash

# Arguments passed from the main script
output_dir="$1"
count="$2"
size_in_MB="$3"

for i in $(seq 1 $count); do
    dd if=/dev/zero of="${output_dir}/file${i}.txt" bs=1M count="$size_in_MB" status=none
done
