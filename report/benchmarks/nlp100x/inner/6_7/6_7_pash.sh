#!/bin/bash
# verses with 2 or more, 3 or more, exactly 2 instances of light.
# PaSh-compatible version: uses ls with glob pattern (similar to driver.sh pattern)

mkdir -p "$OUTPUT_DIR"

cd "$INPUT_FILE"
for input_file in *
do
    if [ -f "$input_file" ]; then
        input=$(basename "$input_file")
        cat "$input_file" | grep -c 'light.\*light'                                 > "$OUTPUT_DIR/$input.out0"
        cat "$input_file" | grep -c 'light.\*light.\*light'                         > "$OUTPUT_DIR/$input.out1"
        cat "$input_file" | grep 'light.\*light' | grep -vc 'light.\*light.\*light' > "$OUTPUT_DIR/$input.out2"
    fi
done


