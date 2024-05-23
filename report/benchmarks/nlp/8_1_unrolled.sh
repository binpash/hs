#!/bin/sh 
# tag: sort_words_by_num_of_syllables
# set -e

IN=${IN:-$PWD/pg}
OUT=${OUT:-$PWD/output/8_1/}
ENTRIES=${ENTRIES:-10}
mkdir -p "$OUT"

#run_tests() {
#}
#export -f run_tests
for input in $(ls ${IN} | head -n ${ENTRIES})
do
    cat $IN/$input | tr -sc '[A-Z][a-z]' '[\012*]' | sort -u > ${OUT}/${input}.words
    tr -sc '[AEIOUaeiou\012]' ' ' < ${OUT}/${input}.words | awk '{print NF}' > ${OUT}/${input}.syl
    paste ${OUT}/${input}.syl ${OUT}/${input}.words | sort -nr | sed 5q > ${OUT}/${input}.out
done

echo 'done';
