#! /bin/sh
OUTPUT=${OUTPUT:-.}
SCRIPTS=${SCRIPTS:-$(dirname "$0")}
touch "$OUTPUT"/giant
python3 "$SCRIPTS"/giant_file.py "$OUTPUT"/giant 100
