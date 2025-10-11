#!/bin/bash

HS_TOP="$(git rev-parse --show-toplevel)"
cd -- "$(dirname -- "${BASH_SOURCE[0]}")" || exit

exec bash "$HS_TOP/pash-spec.sh" --python ./chipseq_pipeline.py
