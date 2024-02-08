#!/bin/bash

FROM=${FROM:-1901}
TO=${TO:-1909}
# RESOURCE_DIR="$PASH_SPEC_TOP/report/resources/max_temp"

echo $FROM $TO $RESOURCE_DIR

# Create output files and initialize them
echo "Year,Max,Min,Average"

## Processing files and data per year
for year in $(seq $FROM $TO); do
    echo "Processing year: $year"
    year_file="year_${year}.txt"
    > "$year_file" # Clear or create the year file

    # Process each .gz file in the year's directory
    for file in $RESOURCE_DIR/$year/*.gz; do
        if [[ -f "$file" ]]; then
            gunzip -c "$file" >> "$year_file"
        else
            echo "File not found: $file"
        fi
    done

    # Processing data for the year
    max_temp=$(cut -c 89-92 < "$year_file" | grep -v 999 | sort -rn | head -n1)
    min_temp=$(cut -c 89-92 < "$year_file" | grep -v 999 | sort -n | head -n1)
    avg_temp=$(awk '{ total += $1; count++ } END { if (count > 0) print total/count }' < "$year_file" | grep -v 999)

    # Append results to the CSV file
    echo "$year,$max_temp,$min_temp,$avg_temp"

done
