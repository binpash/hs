#!/bin/bash
base=$(dirname $0)
source ${base}/.venv/bin/activate

## Per-run /tmp. run_base backs /tmp with a host directory shared by every
## run (the data disk's tmp/), and what lands there -- hs's scratch (kept by
## the harness's -d 2), try's mount logs, the inputs overlay below -- is
## root-owned and would pile up. So each container gets its own subdirectory
## bound over /tmp, named by run_base (HS_RUN_ID) so it can be found on the
## host, and removed at exit unless HS_KEEP=1 (run --keep).
## Skipped quietly without CAP_SYS_ADMIN (unprivileged docker runs).
run_tmp=/tmp/${HS_RUN_ID:-hs-run.$$}
mkdir -p "$run_tmp"
if ! mount --bind "$run_tmp" /tmp 2>/dev/null; then
    rmdir "$run_tmp"; run_tmp=
fi

## Benchmark inputs. run_base bind-mounts the host's report/resources READ-ONLY
## at /hs-inputs so no run can touch the downloaded data. What the benchmarks
## see at report/resources is built from it in three steps, each of which
## turned out to be necessary for hs's sandbox to be able to write there
## (max_temp regenerates $RESOURCE_DIR/<year>.txt on every run):
##
##  1. An idmapped bind (util-linux >= 2.39) re-presenting the host owner as
##     root. try runs the sandbox in a user namespace that maps only root, so
##     files owned by anyone else are unmapped inside it (EOVERFLOW on write).
##  2. An overlay whose lower is that mount and whose upper is a throwaway
##     directory under /tmp (host disk, via run_base): writes go to the upper
##     and vanish with the container; the host copy is never touched.
##  3. Mounted at a TOP-LEVEL path, /hs-resources, with report/resources a
##     symlink to it. try overlays each top-level directory; a mount nested
##     inside one is passed through and is not writable from the sandbox.
##
## Skipped entirely when nothing is mounted at /hs-inputs (plain docker runs,
## and ./setup, which mounts resources read-write at report/resources itself).
if mountpoint -q /hs-inputs; then
    owner_uid=$(stat -c %u /hs-inputs); owner_gid=$(stat -c %g /hs-inputs)
    cow=/tmp/hs-inputs-cow
    mkdir -p /hs-inputs-idmap /hs-resources "$cow/upper" "$cow/work"
    lower=/hs-inputs
    if mount --bind --map-users "$owner_uid:0:1" --map-groups "$owner_gid:0:1" /hs-inputs /hs-inputs-idmap; then
        lower=/hs-inputs-idmap
    else
        echo "entrypoint: idmapped bind failed (needs util-linux >= 2.39); benchmarks that write into their inputs will not work" >&2
    fi
    if mount -t overlay overlay \
        -o "lowerdir=$lower,upperdir=$cow/upper,workdir=$cow/work" /hs-resources; then
        :
    else
        echo "entrypoint: overlay over inputs failed; using the read-only mount" >&2
        mount --bind -o ro "$lower" /hs-resources
    fi
    rm -rf /srv/hs/report/resources
    ln -s /hs-resources /srv/hs/report/resources
    inputs_cow=$cow
fi

## Tear down what this run put on the host-backed /tmp, where we still have
## the rights: the inputs overlay (its upper holds everything the benchmark
## wrote into its inputs, multi-GB for max_temp), then the per-run /tmp.
## With HS_KEEP=1 all of it stays for debugging.
if [ -n "${inputs_cow:-}" ] || [ -n "$run_tmp" ]; then
    "$@"; status=$?
    if [ "${HS_KEEP:-0}" != 1 ]; then
        [ -n "${inputs_cow:-}" ] && { umount /hs-resources 2>/dev/null; rm -rf "$inputs_cow"; }
        [ -n "$run_tmp" ] && { umount /tmp 2>/dev/null; rm -rf "$run_tmp"; }
    fi
    exit $status
fi
exec "$@"
