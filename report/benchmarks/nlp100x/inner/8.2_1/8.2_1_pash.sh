#!/bin/bash
# tag: vowel_sequences_gr_1K.sh
# PaSh-compatible version: uses ls with glob pattern (similar to driver.sh pattern)

mkdir -p "$OUTPUT_DIR"

cd "$INPUT_FILE"
for input_file in *
do
    if [ -f "$input_file" ]; then
        input=$(basename "$input_file")
        cat "$input_file" | tr -c 'A-Za-z' '[\n*]' | grep -v "^\s*$" | tr -sc 'AEIOUaeiou' '[\012*]' | sort | uniq -c | awk "\$1 >= 1000" > "$OUTPUT_DIR/$input.out"
    fi
done


