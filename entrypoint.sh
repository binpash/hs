#!/bin/bash
base=$(dirname $0)
source ${base}/.venv/bin/activate

## Docker gives the container a fresh sysfs with neither bpffs nor tracefs
## mounted, and fstrace needs both: /sys/fs/bpf to pin its programs and maps,
## and /sys/kernel/tracing for tracepoint attachment. Mount them ourselves
## (needs --privileged, which the benchmark harness already uses) instead of
## assuming the host or runtime did it.
mountpoint -q /sys/fs/bpf || mount -t bpf bpf /sys/fs/bpf || \
    echo "entrypoint: failed to mount bpffs on /sys/fs/bpf; fstrace will not work" >&2
mountpoint -q /sys/kernel/tracing || mount -t tracefs tracefs /sys/kernel/tracing || \
    echo "entrypoint: failed to mount tracefs on /sys/kernel/tracing; fstrace will not work" >&2

## Overlay upperdirs cannot live on the container's overlayfs rootfs, so back
## the sandbox base with a single tmpfs for the container's lifetime (one
## mount here instead of try mounting one per sandbox).
mkdir -p /hs-sandbox
mountpoint -q /hs-sandbox || mount -t tmpfs -o mode=1777 tmpfs /hs-sandbox || \
    echo "entrypoint: failed to mount tmpfs on /hs-sandbox; sandboxes may fail on overlayfs rootfs" >&2

## A failed install must be loud: every speculated command silently falls
## back to unsafe serial re-execution without it.
if ! fstrace install; then
    echo "entrypoint: fstrace install FAILED; hs will run without speculation tracing" >&2
fi
exec "$@"
