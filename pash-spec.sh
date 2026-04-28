#!/usr/bin/env bash

set -euo pipefail

base_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ "${1:-}" == "--python" ]]; then
    echo "error: the legacy --python runner is not part of the binpash-hs runtime package." >&2
    echo "See python_hs/report/README.md in the source repository for Python frontend evaluation materials." >&2
    exit 2
fi

exec "$base_dir/hs" "$@"
