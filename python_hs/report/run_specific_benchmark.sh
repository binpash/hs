#!/bin/bash

set -u
cd -- "$(dirname -- "${BASH_SOURCE[0]}")" || exit

HS_TOP="$(git rev-parse --show-toplevel)"
export HS_TOP

WARMUP=0
RUNS=1
HS_WINDOW=16
HS_DEBUG=0
BENCHMARKS="$(find benchmarks/ -mindepth 1 -maxdepth 1 -type d -printf '%f ')"
readonly BENCHMARKS

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

RESULT_DIR="$(readlink -f "${1:-results}")"
export RESULT_DIR
mkdir -p "$RESULT_DIR"

if [ -z "$METHOD" ] || [ -z "$BENCHMARK" ]; then
    echo "Usage: $0 [--warmup N] [--runs N] [--debug N] {spec|sub|full|hyperfine-spec|hyperfine-sub|hyperfine-full} {benchmark|all}"
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
    local time_prefix="$RESULT_DIR/$type-$bench"
    rm -f "$time_prefix."{md,json}
    rm -rf "outputs/$bench"
    hyperfine --show-output --shell=bash --warmup "$WARMUP" --runs "$RUNS" --export-json "$time_prefix.json" --export-markdown "$time_prefix.md" "$@"
}

move_result() {
    local bench="${1:?No benchmark provided}"
    local type="${2:?No type provided}"
    local dest="outputs/$type-bench"
    rm -rf "$dest"
    mv "outputs/$bench" "$dest"
}

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

    case "$METHOD" in
    spec)
        hyperfine_with_args "$bench" spec "spec $script $*" && move_result "$bench" spec
        ;;
    sub)
        hyperfine_with_args "$bench" sub "sub $script" && move_result "$bench" sub
        ;;
    *)
        echo "Error: Invalid method '$METHOD'"
        echo "Usage: $0 [--warmup N] [--runs N] {spec|sub} {benchmark}"
        exit 1
        ;;
    esac
}

run_benchmark "$BENCHMARK" "$@"
