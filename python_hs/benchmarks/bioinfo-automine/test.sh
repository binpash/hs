#!/usr/bin/env bash

# to top directory of this script
cd -- "$(dirname -- "${BASH_SOURCE[0]}")" || exit

case "$1" in
spec)
    spec
    ;;
subprocess)
    subprocess
    ;;
full)
    spec
    subprocess
    ;;
*)
    echo "Usage: $0 {spec|subprocess|full}"
    exit 1
    ;;
esac
