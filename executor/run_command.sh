#!/bin/bash

## TODO: Not sure if it is OK and ideal to give this a string
export CMD_STRING=${1?No command was given to execute}
export TRACE_FILE=${2?No trace file path given}
export STDOUT_FILE=${3?No stdout file given}
export LATEST_ENV_FILE=${4?No env file to run with given}
export SANDBOX_DIR=${5?No sandbox dir given}
export TMPDIR=${6?No tmp dir given}
export EXEC_MODE=${7?No execution mode given}
export CMD_ID=${8?No command id given}
export POST_EXEC_ENV=${9?No Riker env file given}
export EXECUTION_ID=${10?No execution id given}
LOWER_DIRS=${11?No lower dirs}

## KK 2023-04-24: Not sure this should be run every time we run a command
## GL 2023-07-08: Tests seem to pass without it
## KK 2026-02-08: Functions now exported from parent hs script, no need to source
# source "$PASH_SPEC_TOP/jit_runtime/pash_spec_init_setup.sh"

if [ "standard" == "$EXEC_MODE" ]; then
    [ -w /sys/fs/cgroup/frontier/cgroup.procs ] && echo $$ > /sys/fs/cgroup/frontier/cgroup.procs
elif [ "speculate" == "$EXEC_MODE" ]; then
    renice 20 -p $$ >/dev/null
fi

## The JIT runtime scripts that run inside the sandbox (via the template
## script) log through pash_redir_output. If PASH_REDIR points at the real
## log file, those writes happen under the overlay, which (a) puts the log
## file into this node's traced write set, making every speculated iteration
## conflict with every other one, and (b) commits the sandbox's stale copy of
## the log back over the real file, clobbering the scheduler's open handle.
## Point it at a per-node file next to the trace artifacts instead:
## /tmp/pash_spec is bind-mounted into the sandbox, so appends land directly
## in the host file (nothing enters the overlay or gets committed), and the
## scheduler's dep filter already ignores that prefix, so the file never
## creates conflicts between speculated iterations.
export PASH_REDIR="${TRACE_FILE}.jitlog"

## Pass system runtime mountpoints through to the sandbox instead of letting
## try overlay them. Both have (locked) nested submounts, so try's overlay
## mount fails on them and it falls back to a FUSE union helper — spawning
## and tearing down FUSE daemons per execution, which dominates sandbox
## setup cost under concurrent speculation. A recursive bind is cheap and
## safe here: /boot is not writable by an unprivileged sandbox, and /run is
## runtime state that the dependency filter ignores (try commit already
## skips /run/mount as well).
TRY_PASSTHROUGH_BINDS=""
for d in /run /boot; do
    [ -d "$d" ] && TRY_PASSTHROUGH_BINDS="$TRY_PASSTHROUGH_BINDS -B $d:$d"
done

## The sandbox base holds the overlay upperdirs/workdirs, so try must never
## use it as an overlay lowerdir (upper inside lower is rejected by the
## kernel). Binding it makes try's mount loop skip it.
SANDBOX_BASE="${HS_SANDBOX_BASE:-/hs-sandbox}"
TRY_PASSTHROUGH_BINDS="$TRY_PASSTHROUGH_BINDS -B $SANDBOX_BASE:$SANDBOX_BASE"

# mkdir -p /tmp/pash_spec/a
# mkdir -p /tmp/pash_spec/b
# export SANDBOX_DIR="$(mktemp -d /tmp/pash_spec/a/sandbox_XXXXXXX)/"
# export TEMPDIR="$(mktemp -d /tmp/pash_spec/b/sandbox_XXXXXXX)"
# echo tempdir $TEMPDIR
# echo sandbox $SANDBOX_DIR

# fstrace wraps the *whole* try invocation and therefore runs OUTSIDE try's
# mount/pid/user namespaces. This is deliberate:
#   * eBPF routes events by global PID; out here fork() yields the global PID,
#     and the kernel's process_fork hook propagates the trace token across
#     try's `unshare` to every sandboxed descendant.
#   * fstrace needs CAP_BPF/CAP_PERFMON in the init user namespace to create
#     and poll its ring buffer — capabilities it does not have inside try's
#     unprivileged user namespace.
#   * the .r/.w/.missed stream files are now written in the host mount
#     namespace, the same one the scheduler reads them from, so no FIFO/overlay
#     bind-mount gymnastics are required.
# fstrace de-escalates only the traced child to the invoking user, so try still
# runs unprivileged exactly as before.
#
# --exec-marker / -M: fstrace suppresses events until try opens EXEC_MARKER,
# which try does right before running the program. This keeps try's sandbox
# construction (its ~18 overlay mounts etc.) out of the trace — only the
# program's own file effects are recorded. The path is a shared constant with
# FSTRACE_EXEC_MARKER in fstrace's BPF (deps/fstrace/src/bpf/hs_trace.bpf.c).
EXEC_MARKER="/var/fstrace/initialized"
fstrace --mode both \
    --exec-marker \
    --trace-file "${TRACE_FILE}" \
    --dep-file /dev/null \
    --stream-read  --stream-read-file  "${TRACE_FILE}.r" \
    --stream-write --stream-write-file "${TRACE_FILE}.w" \
    --missed-file "${TRACE_FILE}.missed" \
    -- ${RUNTIME_LIBRARY_DIR}/fd_util -f "${LATEST_ENV_FILE}.fds" -p ${STDOUT_FILE} bash "${PASH_SPEC_TOP}/deps/try/try" -D "${SANDBOX_DIR}" -L "${LOWER_DIRS}" -B /tmp/pash_spec:/tmp/pash_spec ${TRY_PASSTHROUGH_BINDS} -M "${EXEC_MARKER}" "${PASH_SPEC_TOP}/executor/template_script_to_execute.sh"
exit_code=$?
## Only used for debugging
# ls -R "${SANDBOX_DIR}/upperdir" 1>&2
# out=`head -3 $SANDBOX_DIR/upperdir/$TRACE_FILE`
## Send a message to the scheduler socket
## Assumes "${PASH_SPEC_SCHEDULER_SOCKET}" is set and exported

## Pass the proper exit code
msg="CommandExecComplete:${CMD_ID}|Exec id:${EXECUTION_ID}|Sandbox dir:${SANDBOX_DIR}|Trace file:${TRACE_FILE}|Tempdir:${TEMPDIR}"
daemon_response=$(pash_spec_communicate_scheduler_just_send "$msg") # Blocking step, daemon will not send response until it's safe to continue
(exit $exit_code)
