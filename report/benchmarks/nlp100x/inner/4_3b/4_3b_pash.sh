#!/bin/bash
#tag: count_trigrams.sh
# PaSh-compatible version: uses ls with glob pattern (similar to driver.sh pattern)

mkdir -p "$OUTPUT_DIR"

pure_func() {
    input=$1
    TEMPDIR=$(mktemp -d)
    cat > ${TEMPDIR}/${input}.words
    tail +2 ${TEMPDIR}/${input}.words > ${TEMPDIR}/${input}.nextwords
    tail +2 ${TEMPDIR}/${input}.words > ${TEMPDIR}/${input}.nextwords2
    paste ${TEMPDIR}/${input}.words ${TEMPDIR}/${input}.nextwords ${TEMPDIR}/${input}.nextwords2 |
    sort | uniq -c 
    rm -rf ${TEMPDIR}
}

cd "$INPUT_FILE"
for input_file in *
do
    if [ -f "$input_file" ]; then
        input=$(basename "$input_file")
        cat "$input_file" | tr -c 'A-Za-z' '[\n*]' | grep -v "^\s*$" | pure_func $input > "$OUTPUT_DIR/$input.trigrams"
    fi
done
