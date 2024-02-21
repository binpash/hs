#!/bin/bash

export PASH_SPEC_TOP=${PASH_SPEC_TOP:-$(git rev-parse --show-toplevel --show-superproject-working-tree)}
export PASH_TOP=${PASH_TOP:-$PASH_SPEC_TOP/deps/pash}

bench_teraseq="${PASH_SPEC_TOP}/report/benchmarks/teraseq"
teraseq_root="/root/TERA-Seq_manuscript"

tests=(
	"5TERA"
	"5TERA-short"
	"5TERA3"
	"TERA3"
	"Akron5Seq"
	"dRNASeq"
	"RNASeq"
	"RiboSeq"
	"mouse_SIRV"
)

# run all download.sh
for t in "${tests[@]}"
do
	test_dir="${bench_teraseq}/samples/$t"
	echo "Downloading for $t"
	bash ${teraseq_root}/samples/download.sh
done
