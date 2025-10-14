#!/bin/bash

set -e

HS_ROOT="$(git rev-parse --show-toplevel)"
DOCKER_ROOT=/srv/hs/python_hs/report

cd "$HS_ROOT/python_hs/report"

docker build -t hs "$HS_ROOT"
docker build -t python-hs-benchmarks .
docker run --rm \
    --init --privileged --cgroupns=host \
    -v "$PWD/data:$DOCKER_ROOT/data" \
    python-hs-benchmarks \
    ./run_specific_benchmark.sh "$@"
