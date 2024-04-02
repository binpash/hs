#!/bin/bash

RESOURCE_DIR="$PASH_SPEC_TOP/report/resources/max_temp"

echo $FROM $TO $RESOURCE_DIR

# Create output files and initialize them
echo "Year,Max,Min,Average"

## Processing files and data per year
for year in $(seq $FROM $TO); do
    echo "Processing year: $year"
    find "$RESOURCE_DIR/$year" -type f -name '*.gz' |
    xargs -I {} gunzip -c {} > $RESOURCE_DIR/$year.txt

    ## Processing
    cat "$RESOURCE_DIR/$year.txt" |
    cut -c 89-92 |
    grep -v 999 |
    sort -rn |
    head -n1

    cat "$RESOURCE_DIR/$year.txt" |
    cut -c 89-92 |
    grep -v 999 |
    sort -n |
    head -n1

    cat "$RESOURCE_DIR/$year.txt" |
    cut -c 89-92 |
    grep -v 999 |
    awk "{ total += \$1; count++ } END { print total/count }"
done
