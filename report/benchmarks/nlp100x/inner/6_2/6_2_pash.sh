#!/bin/bash
# tag: four-letter words
# PaSh-compatible version: uses ls with glob pattern (similar to driver.sh pattern)
# set -e

mkdir -p "$OUTPUT_DIR"

cd "$INPUT_FILE"
for input_file in *
do
    if [ -f "$input_file" ]; then
        input=$(basename "$input_file")
        cat "$input_file" | tr -c 'A-Za-z' '[\n*]' | grep -v "^\s*$" | grep -c '^....$' > "$OUTPUT_DIR/$input.out0"
        cat "$input_file" | tr -c 'A-Za-z' '[\n*]' | grep -v "^\s*$" | sort -u | grep -c '^....$'  > "$OUTPUT_DIR/$input.out1"
    fi
done




