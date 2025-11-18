#!/bin/bash
# tag: 1-syllable words
# PaSh-compatible version: uses ls with glob pattern (similar to driver.sh pattern)
# set -e

mkdir -p "$OUTPUT_DIR"

cd "$INPUT_FILE"
for input_file in *
do
    if [ -f "$input_file" ]; then
        input=$(basename "$input_file")
        cat "$input_file" | tr -c 'A-Za-z' '[\n*]' | grep -v "^\s*$" | grep -i '^[^aeiou]*[aeiou][^aeiou]*$' | sort | uniq -c | sed 5q > "$OUTPUT_DIR/$input.out"
    fi
done




