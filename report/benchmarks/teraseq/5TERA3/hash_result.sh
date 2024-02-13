#!/bin/bash

source ../PARAMS.sh

samples=(
    "hsa.dRNASeq.HeLa.total.REL5.long.REL3.4"
    "hsa.dRNASeq.HeLa.total.REL5.long.REL3.5"
    "hsa.dRNASeq.HeLa.total.REL5.long.REL3.6"
    "hsa.dRNASeq.HeLa.total.REL5.long.REL3.X"
)

for f in "${samples[@]}"; do
    sdir="$SAMPLE_DIR/$f"
    for g in $(find "$sdir"); do
        if [ -f "$g" ]
        then
            echo -n "$g: "
            if [[ "$g" == *.gz ]]
            then
                zcat "$g" | sha256sum
            elif [[ "$g" == *.db ]]
            then
                sqlite3 "$g" "SELECT * FROM genome transcr" | sha256sum
            else
                sha256sum < "$g"
            fi
        fi
    done
done

