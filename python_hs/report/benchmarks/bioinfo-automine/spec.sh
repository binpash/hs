#!/bin/bash

set -e

BENCHMARK="$(readlink -f -- "$(dirname -- "${BASH_SOURCE[0]}")")"
HS_TOP="$(git rev-parse --show-toplevel)"
cd "$HS_TOP/python_hs/report/"

exec bash "$HS_TOP/pash-spec.sh" --python "$BENCHMARK/chipseq_pipeline.py"
