#!/bin/bash

set -e

HS_ROOT="$(git rev-parse --show-toplevel)"
DOCKER_ROOT=/srv/hs/python_hs/report
USER_ID="$(id -u)"
GROUP_ID="$(id -g)"

cd "$HS_ROOT/python_hs/report"

docker build -t hs "$HS_ROOT"
docker build -t python-hs-benchmarks .
docker run --rm \
    --init --privileged --cgroupns=host \
    -v "$PWD/data:$DOCKER_ROOT/data" \
    -v "$PWD/results:$DOCKER_ROOT/results" \
    -v "$PWD/output:$DOCKER_ROOT/output" \
    python-hs-benchmarks "$@"

# fix permissions
docker run --rm \
    -v "$PWD/data:$DOCKER_ROOT/data" \
    -v "$PWD/results:$DOCKER_ROOT/results" \
    -v "$PWD/output:$DOCKER_ROOT/output" \
    python-hs-benchmarks \
    chown -R "$USER_ID:$GROUP_ID" data/ results/ output/
