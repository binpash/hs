#!/bin/bash

MAINFILE="$(mktemp)"
export MAINFILE=$MAINFILE

export PASH_SPEC_TOP=${PASH_SPEC_TOP:-$(git rev-parse --show-toplevel --show-superproject-working-tree)}
"$PASH_SPEC_TOP"/pash-spec.sh $@

while IFS= read -r line; do
    execution_id=$(echo "$line" | awk '{print $2}')
    timefile="/tmp/try-time-${execution_id}"
    printf "%s;" "$execution_id"

    prev_timestamp=0
    while IFS= read -r line; do
        # Extract the timestamp from the line
        timestamp=$(echo "$line" | cut -d' ' -f1)

        # Calculate the delta t if it's not the first line
        if [[ $prev_timestamp != 0 ]]; then
            # milliseconds
            delta_t=$(echo "($timestamp - $prev_timestamp) * 1000" | bc)
            printf "%.9f;" "$delta_t"
        fi

        # Update the previous timestamp
        prev_timestamp=$timestamp
    done < "$timefile"
    echo
done < "$MAINFILE"
