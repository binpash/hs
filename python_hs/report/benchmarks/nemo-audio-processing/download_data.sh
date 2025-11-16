#!/usr/bin/env bash

set -euo pipefail

URLS=(
    "http://www.openslr.org/resources/12/train-clean-100.tar.gz"
    "http://www.openslr.org/resources/12/train-clean-360.tar.gz"
    "http://www.openslr.org/resources/12/train-other-500.tar.gz"
    "http://www.openslr.org/resources/12/dev-clean.tar.gz"
    "http://www.openslr.org/resources/12/dev-other.tar.gz"
    "http://www.openslr.org/resources/12/test-clean.tar.gz"
    "http://www.openslr.org/resources/12/test-other.tar.gz"
    "https://www.openslr.org/resources/31/dev-clean-2.tar.gz"
    "https://www.openslr.org/resources/31/train-clean-5.tar.gz"
)

setup() {
    # to top directory of this script
    cd -- "$(dirname -- "${BASH_SOURCE[0]}")" || exit
    # to the report directory
    cd ../../ || exit

    local data_dir="data/nemo-audio-processing"
    mkdir -p "$data_dir"
    cd "$data_dir" || exit
}

curl_conf() {
    printf 'url = %s\n' "${URLS[@]}"
}

download() {
    curl -fLZ -C - --remote-name-all --progress-bar -K -
}

extract() {
    for url in "${URLS[@]}"; do
        local filename="${url##*/}"
        [[ -f "$filename" ]] && tar -xzf "$filename"
    done
}
preprocess() {
    ./preprocess
}

main() {
    setup
    curl_conf | download
    extract
    preprocess
}

main

