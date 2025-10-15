#!/bin/bash
cd -- "$(dirname -- "${BASH_SOURCE[0]}")" || exit

HS_TOP="$(git rev-parse --show-toplevel)"
export HS_TOP

WARMUP=0
RUNS=1
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
    --)
        shift
        break
        ;;
    *)
        break
        ;;
    esac
done

readonly METHOD="$1"
shift
readonly BENCHMARK="$1"
shift

if [ -z "$METHOD" ] || [ -z "$BENCHMARK" ]; then
    echo "Usage: $0 [--warmup N] [--runs N] {spec|subprocess|full|hyperfine-spec|hyperfine-subprocess|hyperfine-full} {benchmark|all}"
    echo "Available benchmarks: ${BENCHMARKS[*]}"
    exit 1
fi

if [[ $METHOD != hyperfine* ]] && { [ "$WARMUP" -ne 0 ] || [ "$RUNS" -ne 1 ]; }; then
    echo "Error: --warmup and --runs can only be used with hyperfine-* methods"
    exit 1
fi

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

    rm -rf "./output/$bench/"

    local spec_cmd=(bash "$HS_TOP/pash-spec.sh" --python "$script" )
    local sub_cmd=(python3 "$script")

    case "$METHOD" in
    spec)
        "${spec_cmd[@]}" "$@"
        ;;
    subprocess)
        "${sub_cmd[@]}" "$@"
        ;;
    full)
        "${spec_cmd[@]}" "$@"
        "${sub_cmd[@]}"
        ;;
    hyperfine-spec)
        hyperfine --warmup "$WARMUP" --runs "$RUNS" --export-json "results-spec-$bench.json" --export-markdown "results-spec-$bench.md" "${spec_cmd[*]} "$*
        ;;
    hyperfine-subprocess)
        hyperfine --warmup "$WARMUP" --runs "$RUNS" --export-json "results-subprocess-$bench.json" --export-markdown "results-subprocess-$bench.md" "${sub_cmd[*]} $*"
        ;;
    hyperfine-full)
        hyperfine --warmup "$WARMUP" --runs "$RUNS" --export-json "results-$bench.json" --export-markdown "results-$bench.md" \
            -n spec "${spec_cmd[*]} $*" \
            -n subprocess "${sub_cmd[*]} $*"
        ;;
    *)
        echo "Error: Invalid method '$METHOD'"
        echo "Usage: $0 [--warmup N] [--runs N] {spec|subprocess|full|hyperfine-spec|hyperfine-subprocess|hyperfine-full} {benchmark|all}"
        exit 1
        ;;
    esac
}

if [ "$BENCHMARK" = "all" ]; then
    for bench in "${BENCHMARKS[@]}"; do
        echo "Running benchmark: $bench"
        run_benchmark "$bench" "$@"
    done
else
    run_benchmark "$BENCHMARK" "$@"
fi
