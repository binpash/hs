#!/bin/bash
# Fetch the 100MB and 1GB wikipedia samples and their index files. Each is
# skipped when already extracted, so rerunning ./setup is cheap. The full
# (>200 GB) and 10G sets are left out on purpose; see git history for URLs.
set -e
BENCH_TOP=${BENCH_TOP:-$(git rev-parse --show-toplevel)}
RESOURCES_DIR=${RESOURCES_DIR:-$BENCH_TOP/report/resources/web-index}
BASE=https://atlas.cs.brown.edu/data/wikipedia
mkdir -p "$RESOURCES_DIR"

fetch() {  # size: 100m or 1g
    local size=$1
    if [ -d "$RESOURCES_DIR/articles$size" ] && [ -s "$RESOURCES_DIR/index$size.txt" ]; then
        echo "wikipedia$size already present, skipping"
        return
    fi
    echo "Downloading wikipedia$size"
    wget -nv --no-check-certificate -O "$RESOURCES_DIR/index$size.txt" "$BASE/index$size.txt"
    # Stream the archive straight into tar: no tarball left on disk, and
    # extraction overlaps the download.
    wget -nv --no-check-certificate -O - "$BASE/wikipedia$size.tar.gz" | tar -xzf - -C "$RESOURCES_DIR"
}

fetch 100m
fetch 1g
