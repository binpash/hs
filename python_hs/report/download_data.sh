#!/bin/bash

# to top directory of this script
cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" || exit

benchmarks=(
  bioinfo-automine
)

validate_benchmark() {
    local bench="$1"
    for b in "${benchmarks[@]}"; do
        if [ "$b" = "$bench" ]; then
            return 0
        fi
    done
    return 1
}

if [ $# -gt 0 ]; then
  b="$1"
  downloader="benchmarks/$b/download_data.sh"
  if ! validate_benchmark "$b"; then
    echo "Passed invalid benchmark "$b"; benchmarks are: ${benchmarks[*]}"
    exit 1
  fi
  bash "$downloader"
else 
  for b in "${benchmarks[@]}"; do
    bash "$downloader"
  done
fi
