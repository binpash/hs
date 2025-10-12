#!/bin/bash

# cd to the top directory of this script
cd -- "$(dirname -- "${BASH_SOURCE[0]}")" || exit

rm -r reference results

python3 ./chipseq_pipeline.py
