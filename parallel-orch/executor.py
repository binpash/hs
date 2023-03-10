import config
import subprocess
import util

# This module executes a sequence of commands 
# and traces them with Riker. 
# Commands [1:N] are run inside an overlay sandbox.

def async_run_and_trace_command_return_trace(command, node_id, sandbox_mode=False):
    trace_file = util.ptempfile()
    process = async_run_and_trace_command(command, trace_file, node_id, sandbox_mode)
    return process, trace_file

def async_run_and_trace_command(command, trace_file, node_id, sandbox_mode=False):
    ## Call Riker to execute the command
    run_script = f'{config.PASH_SPEC_TOP}/parallel-orch/run_command.sh'
    args = ["/bin/bash", run_script, command, trace_file]
    if sandbox_mode:
        # print(" -- Sandbox mode")
        args.append("sandbox")
    else:
        # print(" -- Standard mode")
        args.append("standard")
    args.append(str(node_id))
    process = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # For debugging
    # process = subprocess.Popen(args)
    return process

def async_run_and_trace_command_in_sandbox(command, trace_file):
    process = async_run_and_trace_command(command, trace_file, sandbox_mode=True)
    return process

## Read trace and capture each command
def read_trace(trace_file):
    with open(trace_file) as f:
        return f.readlines()
