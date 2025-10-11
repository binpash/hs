#!/bin/bash 
cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" || exit

WARMUP=0
RUNS=1

benchmarks=(
  bioinfo-automine
)

OPTS=$(getopt -o w:r: --long warmup:,runs: -n 'benchmark.sh' -- "$@") || exit 1
eval set -- "$OPTS"

while true; do
    case "$1" in
        -w|--warmup)
            WARMUP="$2"
            shift 2
            ;;
        -r|--runs)
            RUNS="$2"
            shift 2
            ;;
        --)
            shift
            break
            ;;
    esac
done

METHOD="$1"
BENCHMARK="$2"

if [ -z "$METHOD" ] || [ -z "$BENCHMARK" ]; then
    echo "Usage: $0 [--warmup N] [--runs N] {spec|subprocess|full|hyperfine-spec|hyperfine-subprocess|hyperfine-full} {benchmark|all}"
    echo "Available benchmarks: ${benchmarks[*]}"
    exit 1
fi

if [[ "$METHOD" != hyperfine* ]] && { [ "$WARMUP" -ne 0 ] || [ "$RUNS" -ne 1 ]; }; then
    echo "Error: --warmup and --runs can only be used with hyperfine-* methods"
    exit 1
fi

validate_benchmark() {
    local bench="$1"
    for b in "${benchmarks[@]}"; do
        if [ "$b" = "$bench" ]; then
            return 0
        fi
    done
    return 1
}

run_benchmark() {
    local bench="$1"
    local bench_dir="./$bench"
    
    if [ ! -d "$bench_dir" ]; then
        echo "Error: Benchmark directory '$bench_dir' not found"
        exit 1
    fi
    
    cd "$bench_dir" || exit
    
    case "$METHOD" in
        spec)
            ./spec.sh
            ;;
        subprocess)
            ./subprocess.sh
            ;;
        full)
            ./spec.sh
            ./subprocess.sh
            ;;
        hyperfine-spec)
            hyperfine --warmup "$WARMUP" --runs "$RUNS" --export-json "results-spec-$bench.json" --export-markdown "results-spec-$bench.md" ./spec.sh
            ;;
        hyperfine-subprocess)
            hyperfine --warmup "$WARMUP" --runs "$RUNS" --export-json "results-subprocess-$bench.json" --export-markdown "results-subprocess-$bench.md" ./subprocess.sh
            ;;
        hyperfine-full)
            hyperfine --warmup "$WARMUP" --runs "$RUNS" --export-json "results-$bench.json" --export-markdown "results-$bench.md" \
              -n "spec" ./spec.sh \
              -n "subprocess" ./subprocess.sh
            ;;
        *)
            echo "Error: Invalid method '$METHOD'"
            echo "Usage: $0 [--warmup N] [--runs N] {spec|subprocess|full|hyperfine-spec|hyperfine-subprocess|hyperfine-full} {benchmark|all}"
            exit 1
            ;;
    esac
    
    cd - > /dev/null || exit
}

if [ "$BENCHMARK" = "all" ]; then
    for bench in "${benchmarks[@]}"; do
        echo "Running benchmark: $bench"
        run_benchmark "$bench"
    done
else
    if ! validate_benchmark "$BENCHMARK"; then
        echo "Error: Invalid benchmark '$BENCHMARK'"
        echo "Available benchmarks: ${benchmarks[*]}"
        exit 1
    fi
    
    run_benchmark "$BENCHMARK"
fi

