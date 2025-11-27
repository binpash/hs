#!/bin/bash

set -euo pipefail
shopt -s extglob

cd -- "$(dirname -- "${BASH_SOURCE[0]}")" || exit

REPORT_DIR="$PWD"
readonly REPORT_DIR
export REPORT_DIR

HS_TOP="$(git rev-parse --show-toplevel)"
readonly HS_TOP
export HS_TOP

HS_RUNS=3
HS_WINDOW=30
HS_DEBUG=0

readonly DOCKER_ROOT=/srv/hs/python_hs/report
readonly DOCKER_IMAGE=python-hs-benchmarks
export DOCKER_ROOT DOCKER_IMAGE

BENCHMARKS="$(find benchmarks/ -mindepth 1 -maxdepth 1 -type d -printf '%f ')"
readonly BENCHMARKS

show_usage() {
    echo "Usage: $0 [OPTIONS] {spec|sub|multi} BENCHMARK"
    echo ""
    echo "Options:"
    echo "  -r, --runs N     Number of benchmark runs (default: 3)"
    echo "  -d, --debug N    Debug level (default: 0)"
    echo ""
    echo "Available benchmarks: $BENCHMARKS"
    exit 1
}

while true; do
    case "${1:-}" in
    -r | --runs)
        HS_RUNS="$2"
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
    -*)
        echo "Error: Unknown option: $1"
        show_usage
        ;;
    *)
        break
        ;;
    esac
done

if [ $# -lt 2 ]; then
    echo "Error: Missing required arguments"
    show_usage
fi

readonly METHOD="$1"
readonly BENCHMARK="$2"
shift 2

RESULT_DIR="$(readlink -f "${1:-results}")"
readonly RESULT_DIR
export RESULT_DIR

export HS_DEBUG
export HS_WINDOW
export HS_RUNS

case "$METHOD" in
spec | sub | multi) ;;
*)
    echo "Error: Invalid method '$METHOD'. Must be one of: spec, sub, multi"
    show_usage
    ;;
esac

if [ ! -d "benchmarks/$BENCHMARK" ]; then
    echo "Error: Benchmark directory 'benchmarks/$BENCHMARK' not found"
    echo "Available benchmarks: $BENCHMARKS"
    exit 1
fi

prepare_container() {
    # Cleanup previous container from last run (if exists)
    if [ -f "$HS_STATE_FILE" ]; then
        local prev_container
        prev_container=$(cat "$HS_STATE_FILE")
        if [ -n "$prev_container" ]; then
            docker stop "$prev_container" &>/dev/null || true
            docker rm "$prev_container" &>/dev/null || true
        fi
    fi

    # Start fresh container
    local container_name="hs-bench-${HS_METHOD}-${HS_BENCHMARK}-$$-$RANDOM"
    echo "[Container: $container_name]" >&2

    docker run -d \
        --name "$container_name" \
        --init \
        --privileged \
        --cgroupns=host \
        -v "$REPORT_DIR/data:$DOCKER_ROOT/data" \
        -v "$REPORT_DIR/results:$DOCKER_ROOT/results" \
        -v "$REPORT_DIR/output:$DOCKER_ROOT/output" \
        "$DOCKER_IMAGE" \
        sleep infinity >/dev/null

    # Wait for container to be ready
    while ! docker exec "$container_name" test -d "$DOCKER_ROOT" &>/dev/null; do
        sleep 0.1
    done

    # Save container name to state file
    echo "$container_name" > "$HS_STATE_FILE"
}

run_benchmark_in_container() {
    # Read container name from state file
    local container_name
    container_name=$(cat "$HS_STATE_FILE")

    # Execute benchmark (this is the only part that gets timed)
    docker exec "$container_name" bash -c "$HS_BENCHMARK_CMD"
}

cleanup_container() {
    local container_name="$1"
    if [ -n "$container_name" ]; then
        docker stop "$container_name" &>/dev/null || true
        docker rm "$container_name" &>/dev/null || true
    fi
}

# Export functions so hyperfine can call them
export -f prepare_container
export -f run_benchmark_in_container
export -f cleanup_container

run_benchmark() {
    local method="$1"
    local benchmark="$2"

    local bench_dir="benchmarks/$benchmark"
    local subprocess_script="$bench_dir/subprocess_.py"
    local multiprocess_script="$bench_dir/multiprocess_.py"

    # Validate scripts exist
    if [ ! -f "$subprocess_script" ]; then
        echo "Error: $subprocess_script not found"
        exit 1
    fi

    if [ "$method" = "multi" ] && [ ! -f "$multiprocess_script" ]; then
        echo "Error: $multiprocess_script not found"
        exit 1
    fi

    mkdir -p "$RESULT_DIR/$benchmark"

    local result_prefix="$RESULT_DIR/$method-$benchmark"
    rm -f "$result_prefix."{md,json}
    rm -rf "output/$benchmark"

    local script_path
    case "$method" in
    spec)
        script_path="$subprocess_script"
        ;;
    sub)
        script_path="$subprocess_script"
        ;;
    multi)
        script_path="$multiprocess_script"
        ;;
    esac

    local benchmark_cmd
    case "$method" in
    spec)
        benchmark_cmd="cd $DOCKER_ROOT && $DOCKER_ROOT/../../pash-spec.sh --python $script_path --window $HS_WINDOW -d $HS_DEBUG"
        ;;
    sub | multi)
        benchmark_cmd="cd $DOCKER_ROOT && python3 $script_path"
        ;;
    esac

    # Export environment variables for container functions
    export HS_METHOD="$method"
    export HS_BENCHMARK="$benchmark"
    export HS_BENCHMARK_CMD="$benchmark_cmd"
    export HS_STATE_FILE="$RESULT_DIR/.hs_container_state"

    cleanup_final() {
        if [ -f "$HS_STATE_FILE" ]; then
            local final_container
            final_container=$(cat "$HS_STATE_FILE")
            if [ -n "$final_container" ]; then
                echo "Cleaning up final container: $final_container"
                cleanup_container "$final_container"
            fi
            rm -f "$HS_STATE_FILE"
        fi
    }
    trap cleanup_final EXIT INT TERM

    echo "Running benchmark: $method on $benchmark ($HS_RUNS runs with fresh containers)"
    hyperfine \
        --runs "$HS_RUNS" \
        --prepare "sync; echo 3 | sudo tee /proc/sys/vm/drop_caches >/dev/null; prepare_container" \
        --export-json "$result_prefix.json" \
        --export-markdown "$result_prefix.md" \
        --show-output \
        --shell=bash \
        "run_benchmark_in_container"

    local dest="output/$method-$benchmark"
    rm -rf "$dest"
    mv "output/$benchmark" "$dest"

    echo "Results saved to $result_prefix.{json,md}"
    echo "Output saved to $dest"
}

echo "==================================================================="
echo "Method:     $METHOD"
echo "Benchmark:  $BENCHMARK"
echo "Runs:       $HS_RUNS"
echo "Debug:      $HS_DEBUG"
echo "Window:     $HS_WINDOW"
echo "==================================================================="
echo ""

echo "Building Docker images..."
docker build -q -t hs "$HS_TOP" || {
    echo "Error: Failed to build base image 'hs'"
    exit 1
}

docker build -q -t "$DOCKER_IMAGE" . || {
    echo "Error: Failed to build benchmark image '$DOCKER_IMAGE'"
    exit 1
}

echo ""

run_benchmark "$METHOD" "$BENCHMARK"
