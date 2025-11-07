#!/bin/bash

# Download OrthoMaM v12 CDS and convert to unaligned for MACSE testing

set -eu


SEQUENCES_N=16
PCORE=$(( SEQUENCES_N / 2 ))
DATASET_URL=https://orthomam.mbb.cnrs.fr/orthomam_v12/cds/omm_filtered_NT_CDS/
OUTPUT_DIR=data/biostars-multiprocessing
ALIGN_NAME_PATHS=benchmarks/biostars-multiprocessing/aligned_sequence_names.txt

cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
cd ../../ || exit

if [ -f "$OUTPUT_DIR/.downloaded" ]; then
    echo "Data already downloaded, skipping."
    exit 0
fi

rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR/omm_filtered_NT_CDS"

head -n "$SEQUENCES_N" "$ALIGN_NAME_PATHS" \
    | xargs -P "$PCORE" -I {} \
       curl -s --output-dir "$OUTPUT_DIR/omm_filtered_NT_CDS" -O "$DATASET_URL"/{}

cd "$OUTPUT_DIR"

find omm_filtered_NT_CDS -name "*.fasta" | xargs -P "$PCORE" -I {} sh -c '
    file="$1"
    basename="${file##*/}"
    sed "/^>/!s/[-. ]//g" "$file" > "${basename%.fasta}.fa"
' _ {}

# Clean up
rm -rf omm_filtered_NT_CDS

echo "Unaligned files created: $(find . -maxdepth 1 -name "*.fa" | wc -l)"
touch .downloaded
