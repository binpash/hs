#!/bin/bash

# Define the directory containing the log files and mappings
log_dir="/media/data_1/gliargo/dynamic-parallelizer/report/benchmarks/bio4/input/logs/wc"
mapping_file="${log_dir}/object_mappings.sort"
tool="${log_dir}/recreate"

# Ensure the mappings file exists
if [ ! -f "$mapping_file" ]; then
    echo "Error: Mappings file $mapping_file not found!"
    exit 1
fi

# Ensure the tool exists
if [ ! -x "$tool" ]; then
    echo "Error: Tool $tool not found or not executable!"
    exit 1
fi

# Process each uncompressed log file in the directory
for file in "$log_dir"/*; do
    if [ -f "$file" ] && [[ "$file" == *.gz ]]; then
        output_file="${file%.gz}.log"
        echo "Processing $file and saving to $output_file"
    	gzip -dc "$file" | "$tool" "$mapping_file" > "$output_file"
    fi
done
