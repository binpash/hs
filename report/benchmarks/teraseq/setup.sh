#!/bin/sh

export PASH_SPEC_TOP=${PASH_SPEC_TOP:-$(git rev-parse --show-toplevel --show-superproject-working-tree)}

# Building Docker Container with hs

docker build -t teraseq-data "$PASH_SPEC_TOP"/report/benchmarks/teraseq
docker build -t hs/teraseq "$PASH_SPEC_TOP" -f "$PASH_SPEC_TOP"/report/benchmarks/teraseq/Dockerfile.hs
