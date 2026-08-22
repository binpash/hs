#!/usr/bin/env bash

##
## hs: PaSh Speculative Execution Entry Point
##
## This script combines pash-spec.sh, pa-spec.sh, and pash_spec_init_setup.sh
## into a single unified entry point for speculative execution.
##

###############################################################################
# Environment Setup
###############################################################################

## Find the source code top directory
export PASH_SPEC_TOP=${PASH_SPEC_TOP:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}
export PASH_TOP="${PASH_TOP:-$PASH_SPEC_TOP}"

## Runtime directories
export RUNTIME_DIR="$PASH_SPEC_TOP/jit_runtime"
export RUNTIME_LIBRARY_DIR="$PASH_SPEC_TOP/executor"
export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:/usr/local/lib/"

## Setup cgroups for memory protection (if writable)
if [ -w /sys/fs/cgroup/ ]; then
    mkdir -p /sys/fs/cgroup/frontier
    total_mem=$(free | awk '/Mem:/ { print $2 }')
    protected_mem=$(python3 -c "print(int(${total_mem}*0.75) << 10)")
    chmod 666 /sys/fs/cgroup/cgroup.procs
    chmod 666 /sys/fs/cgroup/frontier/cgroup.procs
    if [ $(whoami) == "root" ]; then
        bash -c "echo $protected_mem > /sys/fs/cgroup/frontier/memory.min"
    fi
fi

## Register signal handlers
trap kill_all SIGTERM SIGINT

kill_all() {
    kill -s SIGKILL 0
    kill -s SIGKILL "$daemon_pid" 2>/dev/null
}

## Save umask
old_umask=$(umask)
umask u=rwx,g=rx,o=rx

## Get bash version
export PASH_BASH_VERSION="${BASH_VERSINFO[@]:0:3}"

## Create temporary directory and communication FIFOs
if [ -n "$PASH_TMP_DIR" ]; then
    mkdir -p "$PASH_TMP_DIR/tmp/pash_spec"
    export PASH_SPEC_TMP_PREFIX="$(mktemp -d "$PASH_TMP_DIR/tmp/pash_spec/pash_XXXXXXX")"
else
    mkdir -p /tmp/pash_spec
    export PASH_SPEC_TMP_PREFIX="$(mktemp -d /tmp/pash_spec/pash_XXXXXXX)"
fi

## Set PASH_TMP_PREFIX with trailing slash for compatibility
export PASH_TMP_PREFIX="${PASH_SPEC_TMP_PREFIX}/"

export PASH_TIMESTAMP="$(date +"%y-%m-%d-%T")"
export RUNTIME_IN_FIFO="${PASH_TMP_PREFIX}/runtime_in_fifo"
export RUNTIME_OUT_FIFO="${PASH_TMP_PREFIX}/runtime_out_fifo"
rm -f "$RUNTIME_IN_FIFO" "$RUNTIME_OUT_FIFO"
mkfifo "$RUNTIME_IN_FIFO" "$RUNTIME_OUT_FIFO"

## Scheduler socket
export PASH_SPEC_SCHEDULER_SOCKET="${PASH_SPEC_TMP_PREFIX}/scheduler_socket"
export PASH_SPEC_NODE_DIRECTORY="${PASH_TMP_PREFIX}/speculative/partial_order/"

## Default flag values
export pash_speculative_flag=1
export PASH_DEBUG_LEVEL=1

## hs writes four log streams of its own, one per producer, each separately
## redirectable:
##
##   HS_JIT_LOG          (--jit-log)          the JIT runtime's shell-side
##                                            records, written through the
##                                            pash_redir_* helpers below. Only
##                                            emitted above debug level 1.
##   HS_SCHEDULER_LOG    (--scheduler-log)    the scheduler daemon's Python log.
##   HS_PREPROCESSOR_LOG (--preprocessor-log) the preprocessor's Python log.
##   HS_INTERNAL_LOG     (--internal-log)     stdout/stderr of the internal
##                                            tooling hs shells out to (try,
##                                            strace, Python tracebacks, ...).
##                                            This has no log format of its own
##                                            and is what would otherwise land
##                                            on the traced script's stderr.
##
## '&2' means "this stream is stderr", the default for all four. Each flag can
## point its stream at a file instead, or at /dev/null to discard it, and
## --combined-log points all four at one file.
##
## Streams are opened by path (see pash_open_log_streams), so any two that name
## the same file share a single descriptor and interleave cleanly instead of
## fighting over two handles.
export HS_JIT_LOG="&2"
export HS_SCHEDULER_LOG="&2"
export HS_PREPROCESSOR_LOG="&2"
export HS_INTERNAL_LOG="&2"

###############################################################################
# Argument Parsing
###############################################################################

pash_init_arg_defaults() {
    input_script=""
    shell_name="hs"
    declare -g -a script_args=()
    command_mode=""
    command_text=""

    # Shell flags
    allexport_flag="+a"
    verbose_flag=""
    xtrace_flag=""

    # Options
    arg_debug=""
    arg_window=""

    # Help flag
    show_help=0
}

pash_show_help() {
    cat << 'EOF'
Usage: hs [OPTIONS] [-c COMMAND | SCRIPT_FILE] [ARGS...]

PaSh Speculative Execution

Options:
  -c, --command COMMAND    Execute COMMAND instead of reading from a script file
  -a                       Export all variables (equivalent to bash -a)
  -v                       Verbose mode (equivalent to bash -v)
  -x                       Trace mode (equivalent to bash -x)
  -d, --debug LEVEL        Debug level (default: 1)
  --window N               Speculative window size (passed to scheduler)
  -h, --help               Show this help message and exit

Log streams (all default to stderr; pass /dev/null to discard one):
  --jit-log FILE           JIT runtime records (needs -d 2 or higher)
  --scheduler-log FILE     Scheduler daemon log
  --preprocessor-log FILE  Preprocessor log
  --internal-log FILE      stdout/stderr of internal tooling (try, strace, ...)
  --combined-log FILE      Point all four streams at FILE
  --log_file FILE          Deprecated alias for --combined-log

Streams pointed at the same file share one descriptor. Redirect all four and
the script's own stdout/stderr carry nothing but the script's own output.

Examples:
  hs script.sh                      Run script.sh with speculative execution
  hs -c "cat file | grep foo"       Run a command
  hs -d 2 script.sh                 Run with debug level 2
  hs --window 10 script.sh          Run with larger speculation window
  hs -d 2 --combined-log hs.log s.sh   Keep every hs log out of s.sh's output
EOF
}

pash_parse_args() {
    local i=1
    local arg next_i next_arg
    local positional_only=0

    while [ $i -le $# ]; do
        arg="${!i}"
        next_i=$((i+1))
        next_arg="${!next_i}"

        if [ "$positional_only" -eq 1 ]; then
            script_args+=("$arg")
            i=$((i+1))
            continue
        fi

        case "$arg" in
            -h|--help)
                show_help=1
                ;;
            -c|--command)
                command_mode="-c"
                command_text="$next_arg"
                i=$next_i
                positional_only=1
                ;;
            -a)
                allexport_flag="-a"
                ;;
            +a)
                allexport_flag="+a"
                ;;
            -v)
                verbose_flag="-v"
                ;;
            -x)
                xtrace_flag="-x"
                ;;
            -d|--debug)
                arg_debug="$next_arg"
                export PASH_DEBUG_LEVEL="$next_arg"
                i=$next_i
                ;;
            --jit-log)
                export HS_JIT_LOG="$next_arg"
                i=$next_i
                ;;
            --scheduler-log)
                export HS_SCHEDULER_LOG="$next_arg"
                i=$next_i
                ;;
            --preprocessor-log)
                export HS_PREPROCESSOR_LOG="$next_arg"
                i=$next_i
                ;;
            --internal-log)
                export HS_INTERNAL_LOG="$next_arg"
                i=$next_i
                ;;
            --combined-log|--log_file)
                ## --log_file is the historical spelling; it only covered the
                ## first three streams, but the internal tooling output it left
                ## on stderr was never wanted either, so it now means all four.
                export HS_JIT_LOG="$next_arg"
                export HS_SCHEDULER_LOG="$next_arg"
                export HS_PREPROCESSOR_LOG="$next_arg"
                export HS_INTERNAL_LOG="$next_arg"
                i=$next_i
                ;;
            --window)
                arg_window="$next_arg"
                i=$next_i
                ;;
            *)
                if [ -z "$input_script" ] && [ -z "$command_mode" ]; then
                    input_script="$arg"
                    shell_name="$arg"
                    positional_only=1
                else
                    script_args+=("$arg")
                fi
                ;;
        esac
        i=$((i+1))
    done

    # In -c mode, first positional arg becomes shell_name ($0)
    if [ -n "$command_mode" ] && [ ${#script_args[@]} -gt 0 ]; then
        shell_name="${script_args[0]}"
        script_args=("${script_args[@]:1}")
    fi
}

pash_handle_command_mode() {
    if [ -n "$command_text" ]; then
        local command_file
        command_file=$(mktemp "${PASH_TMP_PREFIX}/command_XXXXXX.sh")
        printf '%s' "$command_text" > "$command_file"
        input_script="$command_file"
    fi
}

###############################################################################
# Logging Functions
###############################################################################

## Map of already-opened log targets: canonical path -> file descriptor.
## Two --*-log flags naming the same file resolve to the same descriptor, so
## hs never holds two independent handles on one log.
declare -A pash_log_fd_by_path=()

## Open one log stream, leaving its descriptor in $pash_opened_fd.
## '&2' resolves to fd 2 without opening anything. A file target is truncated
## the first time it is seen in this run, then opened for append, so every
## producer sharing it appends into one fresh log.
pash_open_log_stream() {
    local target="$1"
    local path fd

    if [ "$target" == '&2' ]; then
        pash_opened_fd=2
        return 0
    fi

    ## Canonicalize so ./x, x and /abs/x share one descriptor. readlink -f
    ## resolves a not-yet-existing final component, which is the common case.
    path=$(readlink -f -- "$target" 2>/dev/null) || path="$target"
    [ -n "$path" ] || path="$target"

    if [ -n "${pash_log_fd_by_path[$path]:-}" ]; then
        pash_opened_fd="${pash_log_fd_by_path[$path]}"
        return 0
    fi

    ## Truncating /dev/null and friends is harmless; truncating a regular file
    ## is what gives each run a fresh log.
    : > "$path" 2>/dev/null
    exec {fd}>>"$path" || {
        echo "hs: cannot open log file '$target'" 1>&2
        exit 1
    }
    pash_log_fd_by_path[$path]=$fd
    pash_opened_fd=$fd
}

## Resolve all four streams. Each HS_*_LOG keeps its path (the JIT stream is
## re-pointed by path inside sandboxes, where descriptors do not reach) and
## gains an HS_*_LOG_FD companion for direct writes.
pash_open_log_streams() {
    pash_open_log_stream "$HS_JIT_LOG";          HS_JIT_LOG_FD=$pash_opened_fd
    pash_open_log_stream "$HS_SCHEDULER_LOG";    HS_SCHEDULER_LOG_FD=$pash_opened_fd
    pash_open_log_stream "$HS_PREPROCESSOR_LOG"; HS_PREPROCESSOR_LOG_FD=$pash_opened_fd
    pash_open_log_stream "$HS_INTERNAL_LOG";     HS_INTERNAL_LOG_FD=$pash_opened_fd
    export HS_JIT_LOG_FD HS_SCHEDULER_LOG_FD HS_PREPROCESSOR_LOG_FD HS_INTERNAL_LOG_FD
}

pash_setup_logging() {
    if [ "$PASH_DEBUG_LEVEL" -le 1 ]; then
        pash_redir_output() {
            :
        }

        pash_redir_all_output() {
            :
        }

        pash_redir_all_output_always_execute() {
            > /dev/null 2>&1 "$@"
        }
    else
        ## Outside a sandbox the JIT stream is the descriptor hs opened.
        ## Inside one, run_command.sh clears HS_JIT_LOG_FD and points
        ## HS_JIT_LOG at a per-node file, so the helpers fall back to
        ## appending by path.
        pash_redir_output() {
            if [ -n "${HS_JIT_LOG_FD:-}" ]; then
                >&"$HS_JIT_LOG_FD" "$@"
            else
                >>"$HS_JIT_LOG" "$@"
            fi
        }

        pash_redir_all_output() {
            if [ -n "${HS_JIT_LOG_FD:-}" ]; then
                >&"$HS_JIT_LOG_FD" 2>&"$HS_JIT_LOG_FD" "$@"
            else
                >>"$HS_JIT_LOG" 2>&1 "$@"
            fi
        }

        pash_redir_all_output_always_execute() {
            pash_redir_all_output "$@"
        }
    fi

    export -f pash_redir_output
    export -f pash_redir_all_output
    export -f pash_redir_all_output_always_execute

    pash_declare_vars() {
        local vars_file="${1?File not given}"
        declare -p > "$vars_file"
    }
    export -f pash_declare_vars
}

###############################################################################
# Communication Functions
###############################################################################

pash_setup_communication() {
    pash_wait_until_unix_socket_listening() {
        local server_name=$1
        local socket=$2
        local i=0
        local maximum_retries=1000
        until echo "Daemon Start" 2> /dev/null | nc -U "$socket" >/dev/null 2>&1; do
            sleep 0.01
            i=$((i+1))
            if [ $i -eq $maximum_retries ]; then
                echo "Error: Maximum retries: $maximum_retries exceeded when waiting for server: ${server_name} to bind to socket: ${socket}!" 1>&2
                exit 1
            fi
        done
    }

    pash_communicate_unix_socket() {
        local server_name=$1
        local socket=$2
        local message=$3
        pash_redir_output echo "Sending msg to ${server_name}: $message"
        daemon_response=$(echo "$message" | nc -U "${socket}")
        pash_redir_output echo "Got response from ${server_name}: $daemon_response"
        echo "$daemon_response"
    }

    export -f pash_wait_until_unix_socket_listening
    export -f pash_communicate_unix_socket
}

###############################################################################
# Scheduler Functions (from pash_spec_init_setup.sh)
###############################################################################

pash_spec_communicate_scheduler() {
    local message=$1
    pash_communicate_unix_socket "PaSh-Spec-scheduler" "${PASH_SPEC_SCHEDULER_SOCKET}" "${message}"
}

pash_spec_communicate_scheduler_just_send() {
    pash_spec_communicate_scheduler "$1"
}

pash_spec_wait_until_scheduler_listening() {
    pash_wait_until_unix_socket_listening "PaSh-Spec-scheduler" "${PASH_SPEC_SCHEDULER_SOCKET}"
}

start_server() {
    ## The daemon's own stdout/stderr become the internal-tooling stream, and
    ## every command it later executes inherits them: executor.py spawns
    ## run_command.sh with stdout/stderr=None, so try's and strace's output
    ## follows the daemon's descriptors rather than the traced script's.
    "$PASH_PYTHON" "$PASH_SPEC_TOP/scheduler/scheduler_server.py" "$@" \
        >&"$HS_INTERNAL_LOG_FD" 2>&"$HS_INTERNAL_LOG_FD" &
    export daemon_pid=$!
    ## Wait until daemon has established connection
    pash_spec_wait_until_scheduler_listening
}

cleanup_server() {
    local daemon_pid=$1
    ## Only wait for daemon if it lives (it might be dead, rip)
    if ps -p "$daemon_pid" > /dev/null
    then
        ## Send and receive from daemon
        msg="Done"
        daemon_response=$(pash_spec_communicate_scheduler "$msg")
        ## Job-control notices ("Terminated", ...) are hs's noise, not the
        ## script's; keep them on the internal stream.
        wait >&"$HS_INTERNAL_LOG_FD" 2>&"$HS_INTERNAL_LOG_FD"
    fi
}

export -f pash_spec_communicate_scheduler
export -f pash_spec_communicate_scheduler_just_send
export -f pash_spec_wait_until_scheduler_listening
export -f start_server
export -f cleanup_server

###############################################################################
# Python Setup
###############################################################################

get_pash_python() {
    # Check for pash-spec venv - use explicit path from PASH_SPEC_TOP
    local venv_dir="$PASH_SPEC_TOP/python_pkgs/bin"
    if [ -x "$venv_dir/python" ]; then
        echo "$venv_dir/python"
    elif [ -x "$venv_dir/python3" ]; then
        echo "$venv_dir/python3"
    else
        # Fallback to system python
        echo "python3"
    fi
}
export PASH_PYTHON=$(get_pash_python)

###############################################################################
# Main Execution
###############################################################################

## 1. Parse arguments
pash_init_arg_defaults
pash_parse_args "$@"

## Show help and exit if requested
if [ "$show_help" -eq 1 ]; then
    pash_show_help
    exit 0
fi

## 2. Setup functions
pash_open_log_streams
pash_setup_logging
pash_setup_communication

## 3. Handle -c command mode
pash_handle_command_mode

## 4. Create temporary file for preprocessed output
preprocessed_output=$(mktemp "${PASH_TMP_PREFIX}/preprocessed_XXXXXX.sh")

## 5. Build server arguments (only --window if specified)
declare -a server_args=()
[ -n "$arg_debug" ] && server_args+=("-d" "$arg_debug")
[ -n "$arg_window" ] && server_args+=("--window" "$arg_window")
## The daemon logs to the descriptor hs already opened rather than reopening
## the path, so a --combined-log run interleaves cleanly with every other
## producer sharing that descriptor.
server_args+=("--log-fd" "$HS_SCHEDULER_LOG_FD")

## 6. Start the scheduler server
start_server "${server_args[@]}"

## 7. Restore umask before executing user scripts
umask "$old_umask"

## 8. Build preprocessor arguments
declare -a preprocessor_args=()
preprocessor_args+=("--output" "$preprocessed_output")
[ -n "$arg_debug" ] && preprocessor_args+=("-d" "$arg_debug")
preprocessor_args+=("--log-fd" "$HS_PREPROCESSOR_LOG_FD")
preprocessor_args+=("$input_script")

## 9. Run the PaSh preprocessor. Its own stdout/stderr (tracebacks, warnings
## from the parser) are internal tooling output, not the script's.
PYTHONPATH="$PASH_SPEC_TOP/preprocessor:$PYTHONPATH" \
    PASH_FROM_SH="Preprocessor" "$PASH_PYTHON" \
    "$PASH_SPEC_TOP/preprocessor/preprocessor.py" "${preprocessor_args[@]}" \
    >&"$HS_INTERNAL_LOG_FD" 2>&"$HS_INTERNAL_LOG_FD"
pash_exit_code=$?

## 10. If preprocessing succeeded, execute the preprocessed script
if [ "$pash_exit_code" -eq 0 ]; then
    bash_flags="$allexport_flag $verbose_flag $xtrace_flag"
    # shellcheck disable=SC2086
    bash $bash_flags -c "source $preprocessed_output" "$shell_name" "${script_args[@]}"
    pash_exit_code=$?
fi

## 11. Cleanup
cleanup_server "${daemon_pid}"

## Teardown noise ("Device or resource busy" when a sandbox mount outlives the
## run) is hs's, not the script's: send it to the internal stream.
if [ "$PASH_DEBUG_LEVEL" -le 1 ]; then
    rm -rf "${PASH_TMP_PREFIX}" 2>&"$HS_INTERNAL_LOG_FD"
fi

## Cleanup cgroups
if [ -w /sys/fs/cgroup/ ]; then
    rmdir /sys/fs/cgroup/frontier 2>/dev/null || true
fi

(exit "$pash_exit_code")
