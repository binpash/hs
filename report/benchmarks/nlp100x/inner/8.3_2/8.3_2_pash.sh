#!/bin/bash
# tag: find_anagrams.sh
# PaSh-compatible version: uses ls with glob pattern (similar to driver.sh pattern)

mkdir -p "$OUTPUT_DIR"

pure_func() {
    input=$1
    TEMPDIR=$(mktemp -d)
    sort -u > ${TEMPDIR}/${input}.types
    rev < ${TEMPDIR}/${input}.types > ${TEMPDIR}/${input}.types.rev
    sort ${TEMPDIR}/${input}.types ${TEMPDIR}/${input}.types.rev | uniq -c | awk "\$1 >= 2 {print \$2}"
    rm -rf ${TEMPDIR}
}

cd "$INPUT_FILE"
for input_file in *
do
    if [ -f "$input_file" ]; then
        input=$(basename "$input_file")
        cat "$input_file" |  tr -c 'A-Za-z' '[\n*]' | grep -v "^\s*$" | pure_func $input > "$OUTPUT_DIR/$input.out"
    fi
done


