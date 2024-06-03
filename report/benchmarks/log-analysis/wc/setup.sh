#!/bin/bash

export PATH=$PATH:$HOME/.local/bin
export PASH_SPEC_TOP=${PASH_SPEC_TOP:-$(git rev-parse --show-toplevel --show-superproject-working-tree)}

download_dir="$PASH_SPEC_TOP/report/resources/log-analysis/wc"
benchmark_dir="$PASH_SPEC_TOP/report/benchmarks/log-analysis/wc"

IN_ROOT=${IN_ROOT:-'https://atlas-group.cs.brown.edu/data/web-logs/world-cup'}

wget "${IN_ROOT}/WorldCup_tools.tar" -P "${benchmark_dir}"
tar -xf WorldCup_tools.tar && rm WorldCup_tools.tar
( cd "${benchmark_dir}/ita_public_tools" && make && mv bin/recreate "${benchmark_dir}" && mv state/object_mappings.sort "${benchmark_dir}")

# Read each line from links.txt and download the file
wget --quiet -r -np -nH --cut-dirs=6 -P "${download_dir}" "${IN_ROOT}/"
rm -rf ${download_dir}/robots.txt ${download_dir}/index.html* ${download_dir}/WorldCup_tools.tar

mkdir outputs
