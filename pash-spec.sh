#!/usr/bin/env bash

set -euo pipefail

base_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ "${1:-}" == "--python" ]]; then
    echo "error: the legacy --python runner is not part of the OSDI '26 smoke test." >&2
    echo "See python_hs/report/README.md and artifact/paper-results/data/python_hs_results.json for the Python frontend evaluation materials." >&2
    exit 2
fi

exec "$base_dir/hs" "$@"
