#! /bin/sh
OUTPUT=${OUTPUT:-.}
SCRIPTS=${SCRIPTS:-./scripts}
$try python3 "$SCRIPTS"/multi_files.py "$OUTPUT"/foo
