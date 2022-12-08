import config
import subprocess

# This module executes a sequence of commands 
# and traces them with Riker. 
# TODO: isolate the execution of the [1:N] commands 
# with overlay.


## TODO: Modify this function to just run one command
def async_run_and_trace_command(command, trace_file):
    ## Call Riker to execute the command
    run_script = f'{config.PASH_SPEC_TOP}/parallel-orch/run_command.sh'
    process = subprocess.Popen(["/bin/bash", run_script, command, trace_file], stdout=subprocess.DEVNULL)
    return process

def async_run_and_trace_command_in_sandbox(command, trace_file):
    ## TODO: Run all the following in a sandbox
    process = async_run_and_trace_command(command, trace_file)
    return process

## Write a Rikerfile with these commands to execute them
def write_cmds_to_rikerfile(cmds_to_run):
    with open("Rikerfile", "w") as f:
        for cmd in cmds_to_run:
            f.write(cmd + "\n")

## Read trace and capture each command
def read_trace(trace_file):
    with open(trace_file) as f:
        return f.readlines()
