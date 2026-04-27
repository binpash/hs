#!/usr/bin/env bash

hs_report_repo_top() {
    local start="${1:-$PWD}"

    if [[ -f "$start" ]]; then
        start="$(dirname "$start")"
    fi

    git -C "$start" rev-parse --show-toplevel --show-superproject-working-tree \
        | awk 'NF { print; exit }'
}

hs_docker() {
    if docker info >/dev/null 2>&1; then
        docker "$@"
        return
    fi

    if command -v sudo >/dev/null 2>&1 && sudo -n docker info >/dev/null 2>&1; then
        sudo docker "$@"
        return
    fi

    cat >&2 <<'EOF'
error: cannot talk to the Docker daemon.
Run this setup with sudo, add your user to the docker group, or set up Docker
so that `docker info` succeeds.
EOF
    return 1
}

hs_require_base_image() {
    local repo_top="${1:?repo top required}"
    local tag="${HS_BASE_IMAGE_TAG:-hs}"
    local inspect_tag="$tag"

    if [[ "$inspect_tag" != *:* ]]; then
        inspect_tag="${inspect_tag}:latest"
    fi

    if ! hs_docker image inspect "$inspect_tag" >/dev/null 2>&1; then
        cat >&2 <<EOF
error: base hS Docker image '$inspect_tag' does not exist.
Build it from the repository root first:
  docker build -t $tag .
EOF
        return 1
    fi

    echo "Using base hS Docker image '$inspect_tag'"
}

hs_build_benchmark_image() {
    local benchmark_dir="${1:?benchmark directory required}"
    local repo_top="${2:-$(hs_report_repo_top "$benchmark_dir")}"
    local benchmark_name="${3:-$(basename "$benchmark_dir")}"

    hs_require_base_image "$repo_top"
    echo "Building benchmark Docker image 'hs/$benchmark_name' from $benchmark_dir"
    hs_docker build -t "hs/$benchmark_name" "$benchmark_dir"
}

hs_parse_run_args() {
    HS_RUN_WINDOW=16
    HS_RUN_TARGET=both

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --window)
                if [[ $# -gt 1 ]]; then
                    HS_RUN_WINDOW="$2"
                    shift 2
                    continue
                fi
                ;;
            --window=*)
                HS_RUN_WINDOW="${1#--window=}"
                ;;
            --target)
                if [[ $# -gt 1 ]]; then
                    HS_RUN_TARGET="$2"
                    shift 2
                    continue
                fi
                ;;
            --target=*)
                HS_RUN_TARGET="${1#--target=}"
                ;;
        esac
        shift
    done
}

hs_write_run_metadata() {
    local output_dir="${1:?output dir required}"
    local benchmark_name="${2:?benchmark name required}"
    local test_name="${3:?test name required}"
    local image_name="${4:?image name required}"
    shift 4

    hs_parse_run_args "$@"
    mkdir -p "$output_dir"

    {
        printf 'benchmark=%s\n' "$benchmark_name"
        printf 'test=%s\n' "$test_name"
        printf 'window=%s\n' "$HS_RUN_WINDOW"
        printf 'target=%s\n' "$HS_RUN_TARGET"
        printf 'image=%s\n' "$image_name"
        printf 'timestamp_utc=%s\n' "$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
        printf 'args='
        printf '%q ' "$@"
        printf '\n'
    } > "$output_dir/run_metadata.env"
}

hs_update_summary_csv() {
    local report_dir="${1:?report dir required}"
    local summary_csv="$report_dir/output/results_summary.csv"

    if command -v python3 >/dev/null 2>&1; then
        python3 "$report_dir/summarize_results.py" --output "$summary_csv" >/dev/null
        echo "Summary CSV: $summary_csv"
    else
        echo "Warn: python3 not found; could not update results summary CSV." >&2
    fi
}
