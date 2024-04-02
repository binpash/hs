#!/bin/bash

export PATH=$PATH:$HOME/.local/bin
export PASH_SPEC_TOP=${PASH_SPEC_TOP:-$(git rev-parse --show-toplevel --show-superproject-working-tree)}

python3 $PASH_SPEC_TOP/report/run_benchmarks.py --subset unix_50 --csv-output
python3 $PASH_SPEC_TOP/report/run_benchmarks.py --subset max_temp --csv-output
python3 $PASH_SPEC_TOP/report/run_benchmarks.py --subset bus-analytics --csv-output
python3 $PASH_SPEC_TOP/report/run_benchmarks.py --subset dgsh --csv-output
