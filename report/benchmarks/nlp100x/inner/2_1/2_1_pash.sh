#!/bin/bash
# tag: merge_upper
# PaSh-compatible version: uses ls with glob pattern (similar to driver.sh pattern)

mkdir -p "$OUTPUT_DIR"

cd "$INPUT_FILE"
for input_file in *
do
    if [ -f "$input_file" ]; then
        input=$(basename "$input_file")
        cat "$input_file" | tr '[a-z]' '[A-Z]' |  tr -c 'A-Za-z' '[\n*]' | grep -v "^\s*$" | sort | uniq -c > "$OUTPUT_DIR/$input.out"
    fi
done


