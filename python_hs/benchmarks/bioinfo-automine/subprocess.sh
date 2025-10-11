#!/bin/bash

# cd to the top directory of this script
cd -- "$(dirname -- "${BASH_SOURCE[0]}")" || exit

python3 ./chipseq_pipeline.py
