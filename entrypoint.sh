#!/bin/bash
base=$(dirname $0)
source ${base}/.venv/bin/activate
mount -t bpf bpffs /sys/fs/bpf 2>/dev/null || true
exec "$@"
