#!/usr/bin/env bash

set -eu

# point to the local downloaded folders
export PYTHONPATH="$PASH_TOP/python_pkgs/:$PASH_SPEC_TOP/python_hs/:${PYTHONPATH:-}"
# for start_server
export PASH_TMP_PREFIX="$(mktemp -d /tmp/pash_XXXXXXX)/"

source "$PASH_TOP/compiler/orchestrator_runtime/pash_init_setup.sh" --speculative
# sets daemon_pid
start_server
python3 "$PASH_SPEC_TOP/python_hs/python_hs/entrypoint.py" "$@"
cleanup_server "$daemon_pid"

