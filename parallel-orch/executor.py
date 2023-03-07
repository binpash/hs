import config
import subprocess

# This module executes a sequence of commands 
# and traces them with Riker. 
# TODO: isolate the execution of the [1:N] commands 
# with overlay.

## TODO: Modify this function to just run one command
def async_run_and_trace_command(command, trace_file, sandbox_mode=False):
    ## Call Riker to execute the command
    run_script = f'{config.PASH_SPEC_TOP}/parallel-orch/run_command.sh'
    args = ["/bin/bash", run_script, command, trace_file]
    if sandbox_mode:
        args.append("sandbox")
    else:
        print(" -- Standard mode")
        args.append("standard")
    process = subprocess.Popen(args, stdout=subprocess.DEVNULL)
    return process

def async_run_and_trace_command_in_sandbox(command, trace_file):
    ## TODO: Run all the following in a sandbox
    process = async_run_and_trace_command(command, trace_file, sandbox_mode=True)
    return process

## Read trace and capture each command
def read_trace(trace_file):
    with open(trace_file) as f:
        return f.readlines()
