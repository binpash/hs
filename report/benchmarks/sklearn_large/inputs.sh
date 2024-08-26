#!/bin/bash

cd "$(realpath $(dirname "$0"))"

export PASH_SPEC_TOP=${PASH_SPEC_TOP:-$(git rev-parse --show-toplevel --show-superproject-working-tree)}
RESOURCES="$PASH_SPEC_TOP/report/resources/sklearn"

/usr/bin/env python3 -c "from sklearn.datasets import fetch_kddcup99; fetch_kddcup99(data_home=\"$RESOURCES\", percent10=False, download_if_missing=True)"
