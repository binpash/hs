#!/usr/bin/env bash

set -euo pipefail

report_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_top="$(git -C "$report_dir" rev-parse --show-toplevel --show-superproject-working-tree | awk 'NF { print; exit }')"

cd "$repo_top"

declare -A seen=()
while IFS= read -r entry; do
    [[ -z "$entry" || "$entry" == \#* ]] && continue
    bench="${entry%%/*}"
    [[ -n "${seen[$bench]:-}" ]] && continue
    seen[$bench]=1

    setup="./report/benchmarks/$bench/setup"
    if [[ -x "$setup" ]]; then
        echo "===== setup $bench ====="
        "$setup"
    else
        echo "Warn: no executable setup script for $bench at $setup" >&2
    fi
done < "$report_dir/all_benchmarks"
