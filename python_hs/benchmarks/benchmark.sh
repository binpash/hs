#!/bin/bash

set -e

HS_ROOT="$(git rev-parse --show-toplevel)"

cd "$HS_ROOT/python_hs/benchmarks"

# Build hs container if needed
docker image inspect hs >/dev/null 2>&1 || docker build -t hs "$HS_ROOT"

# Build python-hs-benchmarks container if needed
docker image inspect python-hs-benchmarks >/dev/null 2>&1 ||
    docker build -t python-hs-benchmarks .

docker run --rm \
    -v "$PWD:/work" \
    -w /work \
    python-hs-benchmarks \
    ./run_specific_benchmark.sh "$@"
