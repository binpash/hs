#!/usr/bin/env bash

set -euo pipefail

report_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_top="$(git -C "$report_dir" rev-parse --show-toplevel --show-superproject-working-tree | awk 'NF { print; exit }')"

if [[ $# -eq 0 ]]; then
    set -- --target both --window 16
fi

cd "$repo_top"

while IFS= read -r entry; do
    [[ -z "$entry" || "$entry" == \#* ]] && continue

    run_script="./report/benchmarks/$entry/run"
    if [[ -x "$run_script" ]]; then
        echo "===== run $entry $* ====="
        "$run_script" "$@"
    else
        echo "Warn: no executable run script for $entry at $run_script" >&2
    fi
done < "$report_dir/all_benchmarks"

python3 "$report_dir/summarize_results.py"
