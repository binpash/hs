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
export RUNTIME_LIBRARY_DIR="$PASH_SPEC_TOP/parallel-orch"
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
export PASH_REDIR="&2"

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
    arg_log_file=""
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
  --log_file FILE          Log file path (default: stderr)
  --window N               Speculative window size (passed to scheduler)
  -h, --help               Show this help message and exit

Examples:
  hs script.sh                      Run script.sh with speculative execution
  hs -c "cat file | grep foo"       Run a command
  hs -d 2 script.sh                 Run with debug level 2
  hs --window 10 script.sh          Run with larger speculation window
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
            --log_file)
                arg_log_file="$next_arg"
                export PASH_REDIR="$next_arg"
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
        if [ "$PASH_REDIR" == '&2' ]; then
            pash_redir_output() {
                >&2 "$@"
            }

            pash_redir_all_output() {
                >&2 "$@"
            }

            pash_redir_all_output_always_execute() {
                >&2 "$@"
            }
        else
            pash_redir_output() {
                >>"$PASH_REDIR" "$@"
            }

            pash_redir_all_output() {
                >>"$PASH_REDIR" 2>&1 "$@"
            }

            pash_redir_all_output_always_execute() {
                >>"$PASH_REDIR" 2>&1 "$@"
            }
        fi
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
    "$PASH_PYTHON" "$PASH_SPEC_TOP/parallel-orch/scheduler_server.py" "$@" &
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
        wait 2> /dev/null 1>&2
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

## 6. Start the scheduler server
start_server "${server_args[@]}"

## 7. Restore umask before executing user scripts
umask "$old_umask"

## 8. Build preprocessor arguments
declare -a preprocessor_args=()
preprocessor_args+=("--output" "$preprocessed_output")
[ -n "$arg_debug" ] && preprocessor_args+=("-d" "$arg_debug")
[ -n "$arg_log_file" ] && preprocessor_args+=("--log_file" "$arg_log_file")
preprocessor_args+=("$input_script")

## 9. Run the PaSh preprocessor
PYTHONPATH="$PASH_SPEC_TOP/preprocessor:$PYTHONPATH" \
    PASH_FROM_SH="Preprocessor" "$PASH_PYTHON" \
    "$PASH_SPEC_TOP/preprocessor/preprocessor.py" "${preprocessor_args[@]}"
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

if [ "$PASH_DEBUG_LEVEL" -le 1 ]; then
    rm -rf "${PASH_TMP_PREFIX}"
fi

## Cleanup cgroups
if [ -w /sys/fs/cgroup/ ]; then
    rmdir /sys/fs/cgroup/frontier 2>/dev/null || true
fi

(exit "$pash_exit_code")
