#! /bin/sh
OUTPUT=${OUTPUT:-.}
SCRIPTS=${SCRIPTS:-./scripts}
touch "$OUTPUT"/giant
python3 "$SCRIPTS"/giant_file.py "$OUTPUT"/giant 100
