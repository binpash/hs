#!/bin/bash

export PASH_SPEC_TOP=${PASH_SPEC_TOP:-$(git rev-parse --show-toplevel --show-superproject-working-tree)}

benchmark_dir="$PASH_SPEC_TOP/report/benchmarks/sklearn"

cd "$(realpath $(dirname "$0"))"
mkdir -p "$PASH_SPEC_TOP/report/resources/sklearn"
mkdir -p "$PASH_SPEC_TOP/report/output/sklearn"

pip install -r requirements.txt
