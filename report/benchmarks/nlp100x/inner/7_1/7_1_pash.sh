#!/bin/bash
# tag: count_morphs
# PaSh-compatible version: uses ls with glob pattern (similar to driver.sh pattern)

mkdir -p "$OUTPUT_DIR"

cd "$INPUT_FILE"
for input_file in *
do
    if [ -f "$input_file" ]; then
        input=$(basename "$input_file")
        cat "$input_file" | sed 's/ly$/-ly/g' | sed 's/ .*//g' | sort | uniq -c > "$OUTPUT_DIR/$input.out"
    fi
done




