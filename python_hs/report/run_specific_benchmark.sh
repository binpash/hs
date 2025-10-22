#!/bin/bash

set -eu
cd -- "$(dirname -- "${BASH_SOURCE[0]}")" || exit

HS_TOP="$(git rev-parse --show-toplevel)"
export HS_TOP

WARMUP=0
RUNS=1
HS_WINDOW=16
HS_DEBUG=0
BENCHMARKS="$(find benchmarks/ -mindepth 1 -maxdepth 1 -type d -printf '%f ')"
readonly BENCHMARKS

RESULT_NUM=$(($(find results/ -maxdepth 1 -type d -name 'run_*' | sed 's/.*run_//' | sort -n | tail -1) + 1))
RESULT_DIR="$(readlink -f "./results/run_$RESULT_NUM")"
export RESULT_DIR
mkdir "$RESULT_DIR"

while true; do
    case "$1" in
    -w | --warmup)
        WARMUP="$2"
        shift 2
        ;;
    -r | --runs)
        RUNS="$2"
        shift 2
        ;;
    -d | --debug)
        HS_DEBUG="$2"
        shift 2
        ;;
    --)
        shift
        break
        ;;
    *)
        break
        ;;
    esac
done

export HS_DEBUG
export HS_WINDOW

readonly METHOD="$1"
shift
readonly BENCHMARK="$1"
shift

if [ -z "$METHOD" ] || [ -z "$BENCHMARK" ]; then
    echo "Usage: $0 [--warmup N] [--runs N] [--debug N] {spec|subprocess|full|hyperfine-spec|hyperfine-subprocess|hyperfine-full} {benchmark|all}"
    echo "Available benchmarks: ${BENCHMARKS[*]}"
    exit 1
fi

if [[ $METHOD != hyperfine* ]] && { [ "$WARMUP" -ne 0 ] || [ "$RUNS" -ne 1 ]; }; then
    echo "Error: --warmup and --runs can only be used with hyperfine-* methods"
    exit 1
fi

# NOTE: If I want to check for equality of stdout, redirect in spec and sub.
spec() {
    local bench="${1:?No benchmark provided}"
    shift
    "$HS_TOP/pash-spec.sh" --python "$bench" --window "$HS_WINDOW" -d "$HS_DEBUG" "$@"
}
export -f spec

sub() {
    python3 "${1:?No benchmark provided}"
}
export -f sub

hyperfine_with_args() {
    local bench="${1:?No benchmark provided}"
    shift
    local type="${1:?Type is not provided}"
    shift
    hyperfine --show-output --shell=bash --warmup "$WARMUP" --runs "$RUNS" --export-json "$RESULT_DIR/$type-$bench.json" --export-markdown "$RESULT_DIR/$type-$bench.md" "$@"
}

move_result() {
    local bench="${1:?No benchmark provided}"
    local type="${2:?No type provided}"
    local out_dir="$RESULT_DIR/${bench}-output/"
    mkdir -p "$out_dir"
    mv "outputs/$bench" "$out_dir/$type" || true
}
export -f move_result

run_benchmark() {
    local bench="$1"
    shift
    local bench_dir="benchmarks/$bench"

    if [ ! -d "$bench_dir" ]; then
        echo "Error: Benchmark directory '$bench_dir' not found"
        echo "Available benchmarks: $BENCHMARKS"
        exit 1
    fi

    local python_files=("$bench_dir"/*.py)

    # check if there's precisely one found python file
    if [[ ! -e "${python_files[*]}" ]]; then
        printf "Weird benchmarking files: %s" "${python_files[*]}"
        exit 1
    fi

    local script="${python_files[0]}"
    local stdout_prefix="$RESULT_DIR/$bench"

    case "$METHOD" in
    spec)
        spec "$script" "$@"
        move_result "$bench" spec
        ;;
    subprocess)
        sub "$script"
        move_result "$bench" sub
        ;;
    full)
        spec "$script" "$@"
        move_result "$bench" spec
        sub "$script"
        move_result "$bench" sub
        ;;
    hyperfine-spec)
        hyperfine_with_args "$bench" spec "spec $script $*"
        move_result "$bench" spec
        ;;
    hyperfine-subprocess)
        hyperfine_with_args "$bench" sub "sub $script"
        move_result "$bench" sub
        ;;
    hyperfine-full)
        hyperfine_with_args "$bench" spec "spec $script $*"
        move_result "$bench" spec
        hyperfine_with_args "$bench" sub "sub $script"
        move_result "$bench" sub
        ;;
    *)
        echo "Error: Invalid method '$METHOD'"
        echo "Usage: $0 [--warmup N] [--runs N] {spec|subprocess|full|hyperfine-spec|hyperfine-subprocess|hyperfine-full} {benchmark|all}"
        exit 1
        ;;
    esac

    rm -rf "./output/$bench/"
}

if [ "$BENCHMARK" = "all" ]; then
    for bench in $BENCHMARKS; do
        echo "Running benchmark: $bench"
        run_benchmark "$bench" "$@"
    done
else
    run_benchmark "$BENCHMARK" "$@"
fi

MISMATCHES=0
for bench_output_dir in "$RESULT_DIR"/*-output/; do
    spec_out="$bench_output_dir/spec"
    sub_out="$bench_output_dir/sub"
    if ! diff -rq "$spec_out" "$sub_out"; then
        echo "Mismatch: $bench_output_dir"
        MISMATCHES=$((MISMATCHES + 1))
    fi
done

if [ $MISMATCHES -ne 0 ]; then
    echo "$MISMATCHES mismatches."
    exit 1
fi

echo "No mismatches."
exit 0
