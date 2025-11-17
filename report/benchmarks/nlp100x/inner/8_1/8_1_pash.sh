#!/bin/bash
# tag: sort_words_by_num_of_syllables
# PaSh-compatible version: uses ls with glob pattern (similar to driver.sh pattern)

mkdir -p "$OUTPUT_DIR"

pure_func() {
    input=$1
    TEMPDIR=$(mktemp -d)
    cat > ${TEMPDIR}/${input}.words
    tr -sc '[AEIOUaeiou\012]' ' ' < ${TEMPDIR}/${input}.words | awk '{print NF}' > ${TEMPDIR}/${input}.syl
    paste ${TEMPDIR}/${input}.syl ${TEMPDIR}/${input}.words | sort -nr | sed 5q
    rm -rf ${TEMPDIR}
}

cd "$INPUT_FILE"
for input_file in *
do
    if [ -f "$input_file" ]; then
        input=$(basename "$input_file")
        cat "$input_file" | tr -c 'A-Za-z' '[\n*]' | grep -v "^\s*$" | sort -u | pure_func $input > "$OUTPUT_DIR/$input.out"
    fi
done


