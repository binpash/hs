#! /bin/sh
OUTPUT=${OUTPUT:-.}
hs_base=$(git rev-parse --show-toplevel)
SCRIPTS=${SCRIPTS:-$(dirname "$0")}
"$hs_base/deps/try/try" -y python3 "$SCRIPTS"/multi_files.py "$OUTPUT"/foo
