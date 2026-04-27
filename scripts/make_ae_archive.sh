#!/usr/bin/env bash

set -euo pipefail

root="$(git rev-parse --show-toplevel)"
out="${1:-$root/hs-osdi26-ae.tar.gz}"
prefix="hs-osdi26-ae"
tmp="$(mktemp -d)"

cleanup() {
    rm -rf "$tmp"
}
trap cleanup EXIT

if [[ ! -d "$root/deps/try/utils" ]]; then
    echo "deps/try is not initialized; run:" >&2
    echo "  git submodule update --init --recursive deps/try" >&2
    exit 1
fi

mkdir -p "$tmp/$prefix"

tar -C "$root" \
    --exclude-vcs \
    --exclude='./paper-hs-sosp24' \
    --exclude='./python_pkgs' \
    --exclude='./.venv' \
    --exclude='./python_hs/.venv' \
    --exclude='./deps/try/utils/*.o' \
    --exclude='./deps/try/utils/try-commit' \
    --exclude='./deps/try/utils/try-summary' \
    --exclude='./executor/fd_util' \
    --exclude='./executor/set-diff' \
    --exclude='*/__pycache__' \
    --exclude='./report/resources' \
    --exclude='./report/output' \
    --exclude='./test/output_bash' \
    --exclude='./test/output_orch' \
    --exclude='./test/results' \
    --exclude='./hs-osdi26-ae*.tar.gz' \
    -cf - . | tar -C "$tmp/$prefix" -xf -

tar -C "$tmp" -czf "$out" "$prefix"
echo "Wrote $out"
