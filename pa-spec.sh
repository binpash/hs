#!/usr/bin/env bash

##
## pa-spec.sh: Simplified PaSh entry point for speculative execution only
##
## This is a stripped-down version of pa.sh that only supports speculative mode.
## It removes all unused flags and compilation server logic.
##

# Get the directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# PASH_SPEC_TOP is this directory
export PASH_SPEC_TOP="$SCRIPT_DIR"

# PASH_TOP kept for compatibility - now points to pash-spec root
export PASH_TOP="${PASH_TOP:-$PASH_SPEC_TOP}"

# Runtime directories - use local jit_runtime
export RUNTIME_DIR="$PASH_SPEC_TOP/jit_runtime"
export RUNTIME_LIBRARY_DIR="$PASH_SPEC_TOP/parallel-orch"

export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:/usr/local/lib/"

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
export PASH_TMP_PREFIX="$(mktemp -d /tmp/pash_spec_XXXXXXX)/"
export PASH_TIMESTAMP="$(date +"%y-%m-%d-%T")"
export RUNTIME_IN_FIFO="${PASH_TMP_PREFIX}/runtime_in_fifo"
export RUNTIME_OUT_FIFO="${PASH_TMP_PREFIX}/runtime_out_fifo"
rm -f "$RUNTIME_IN_FIFO" "$RUNTIME_OUT_FIFO"
mkfifo "$RUNTIME_IN_FIFO" "$RUNTIME_OUT_FIFO"

## Scheduler socket (set by pash-spec.sh, but provide default)
export PASH_SPEC_SCHEDULER_SOCKET="${PASH_SPEC_SCHEDULER_SOCKET:-${PASH_TMP_PREFIX}/scheduler_socket}"

## Default flag values - always in speculative mode
export pash_speculative_flag=1
export PASH_DEBUG_LEVEL=1
export PASH_REDIR="&2"

###############################################################################
# Argument Parsing (Simplified - only used flags)
###############################################################################

pash_init_arg_defaults() {
    input_script=""
    shell_name="pash-spec"
    declare -g -a script_args=()
    command_mode=""
    command_text=""

    # Shell flags
    allexport_flag="+a"
    verbose_flag=""
    xtrace_flag=""

    # Used flags
    arg_debug=""
    arg_log_file=""
    arg_window=""

    # Help flag
    show_help=0
}

pash_show_help() {
    cat << 'EOF'
Usage: pa-spec.sh [OPTIONS] [-c COMMAND | SCRIPT_FILE] [ARGS...]

PaSh Speculative Execution (Simplified)

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
  pa-spec.sh script.sh              Run script.sh with speculative execution
  pa-spec.sh -c "cat file | grep foo"   Run a command
  pa-spec.sh -d 2 script.sh         Run with debug level 2
  pa-spec.sh --window 10 script.sh  Run with larger speculation window
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

## 3. Source speculative setup (defines start_server, cleanup_server)
source "$RUNTIME_DIR/pash_spec_init_setup.sh"

## 4. Handle -c command mode
pash_handle_command_mode

## 5. Create temporary file for preprocessed output
preprocessed_output=$(mktemp "${PASH_TMP_PREFIX}/preprocessed_XXXXXX.sh")

## 6. Build server arguments (only --window if specified)
declare -a server_args=()
[ -n "$arg_debug" ] && server_args+=("-d" "$arg_debug")
[ -n "$arg_window" ] && server_args+=("--window" "$arg_window")

## 7. Start the scheduler server
start_server "${server_args[@]}"

## 8. Restore umask before executing user scripts
umask "$old_umask"

## 9. Build preprocessor arguments
declare -a preprocessor_args=()
preprocessor_args+=("--output" "$preprocessed_output")
[ -n "$arg_debug" ] && preprocessor_args+=("-d" "$arg_debug")
[ -n "$arg_log_file" ] && preprocessor_args+=("--log_file" "$arg_log_file")
preprocessor_args+=("--speculative")
preprocessor_args+=("$input_script")

## 10. Run the PaSh preprocessor (standalone)
PYTHONPATH="$PASH_SPEC_TOP/preprocessor:$PYTHONPATH" \
    PASH_FROM_SH="PaSh preprocessor" "$PASH_PYTHON" \
    "$PASH_SPEC_TOP/preprocessor/pash_preprocessor.py" "${preprocessor_args[@]}"
pash_exit_code=$?

## 11. If preprocessing succeeded, execute the preprocessed script
if [ "$pash_exit_code" -eq 0 ]; then
    bash_flags="$allexport_flag $verbose_flag $xtrace_flag"
    # shellcheck disable=SC2086
    bash $bash_flags -c "source $preprocessed_output" "$shell_name" "${script_args[@]}"
    pash_exit_code=$?
fi

## 12. Cleanup
cleanup_server "${daemon_pid}"

if [ "$PASH_DEBUG_LEVEL" -le 1 ]; then
    rm -rf "${PASH_TMP_PREFIX}"
fi

(exit "$pash_exit_code")
