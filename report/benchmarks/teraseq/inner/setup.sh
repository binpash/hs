#!/bin/sh
set -eu

export PASH_SPEC_TOP=${PASH_SPEC_TOP:-$(git rev-parse --show-toplevel --show-superproject-working-tree)}

git -C "$PASH_SPEC_TOP" submodule update --init --recursive deps/try

# Keep the enormous, stable TERA-Seq inputs/data on the host. Baking them into
# Docker layers is both slow and prone to overlayfs unpack failures on this host.
TERASEQ_CACHE_DIR=${TERASEQ_CACHE_DIR:-"$PASH_SPEC_TOP"/report/benchmarks/teraseq/.cache}
TERASEQ_SAMPLES_DIR="$TERASEQ_CACHE_DIR/samples"
TERASEQ_DATA_DIR="$TERASEQ_CACHE_DIR/data"
mkdir -p "$TERASEQ_SAMPLES_DIR" "$TERASEQ_DATA_DIR"

expected_fastqs=22
count_fastqs() {
    find "$TERASEQ_SAMPLES_DIR" -path '*/fastq/reads.*.fastq.gz' -type f -size +1M | wc -l
}

actual_fastqs=$(count_fastqs)
if [ -f "$TERASEQ_CACHE_DIR/inputs.done" ] && [ "$actual_fastqs" -lt "$expected_fastqs" ]; then
    echo "Ignoring incomplete TERA-Seq input cache at $TERASEQ_SAMPLES_DIR ($actual_fastqs/$expected_fastqs FASTQ files found)."
    rm -f "$TERASEQ_CACHE_DIR"/inputs.done
fi

if [ -f "$TERASEQ_CACHE_DIR/data.done" ] && [ -z "$(find "$TERASEQ_DATA_DIR" -mindepth 1 -print -quit)" ]; then
    echo "Ignoring empty TERA-Seq data cache at $TERASEQ_DATA_DIR."
    rm -f "$TERASEQ_CACHE_DIR"/data.done
fi

docker build \
    --cache-to type=inline \
    -t teraseq20-scripts \
    "$PASH_SPEC_TOP"/report/benchmarks/teraseq/inner

docker run --rm \
    -v "$TERASEQ_SAMPLES_DIR":/cache \
    teraseq20-scripts \
    /bin/bash -lc 'cp -a /root/TERA-Seq_manuscript/samples/. /cache/'

if [ "${TERASEQ_REBUILD_INPUTS:-0}" = "1" ]; then
    rm -f "$TERASEQ_CACHE_DIR"/inputs.done
fi

if [ "${TERASEQ_REBUILD_DATA:-0}" = "1" ]; then
    rm -f "$TERASEQ_CACHE_DIR"/data.done
fi

if [ ! -f "$TERASEQ_CACHE_DIR/inputs.done" ]; then
    docker run --rm \
        -e PASH_SPEC_TOP=/root/TERA-Seq_manuscript \
        -v "$TERASEQ_SAMPLES_DIR":/root/TERA-Seq_manuscript/samples \
        teraseq20-scripts \
        /bin/bash -lc 'cd /root/TERA-Seq_manuscript && ./inputs.sh'
    actual_fastqs=$(count_fastqs)
    if [ "$actual_fastqs" -lt "$expected_fastqs" ]; then
        echo "TERA-Seq input download is incomplete at $TERASEQ_SAMPLES_DIR ($actual_fastqs/$expected_fastqs FASTQ files found)." >&2
        echo "Rerun setup to resume missing downloads; existing FASTQs will be reused." >&2
        exit 1
    fi
    touch "$TERASEQ_CACHE_DIR/inputs.done"
else
    echo "Using cached TERA-Seq inputs at $TERASEQ_SAMPLES_DIR. Set TERASEQ_REBUILD_INPUTS=1 to rerun downloads."
fi

if [ ! -f "$TERASEQ_CACHE_DIR/data.done" ]; then
    docker run --rm \
        -e PASH_SPEC_TOP=/root/TERA-Seq_manuscript \
        -v "$TERASEQ_SAMPLES_DIR":/root/TERA-Seq_manuscript/samples \
        -v "$TERASEQ_DATA_DIR":/root/TERA-Seq_manuscript/data \
        teraseq20-scripts \
        /bin/bash -lc 'cd /root/TERA-Seq_manuscript/data && /root/TERA-Seq_manuscript/run-data.sh && cd /root/TERA-Seq_manuscript && ./setup'
    touch "$TERASEQ_CACHE_DIR/data.done"
else
    echo "Using cached TERA-Seq data at $TERASEQ_DATA_DIR. Set TERASEQ_REBUILD_DATA=1 to rerun data preparation."
fi

docker build \
    --cache-to type=inline \
    -t hs/teraseq \
    "$PASH_SPEC_TOP" \
    -f "$PASH_SPEC_TOP"/report/benchmarks/teraseq/inner/Dockerfile.hs
