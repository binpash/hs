#!/usr/bin/env bash

cd -- "$(dirname "${BASH_SOURCE[0]}")"

: "${PYTHON_HS_LOGFILE:?PYTHON_HS_LOGFILE not set, exiting}"

../../pash-spec.sh -d 1 "$@" 2>&1 | tee "$PYTHON_HS_LOGFILE"
