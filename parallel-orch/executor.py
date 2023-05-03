import config
import logging
import subprocess
import util
import tempfile

# This module executes a sequence of commands 
# and traces them with Riker. 
# Commands [1:N] are run inside an overlay sandbox.

def async_run_and_trace_command_return_trace(command, node_id, sandbox_mode=False):
    trace_file = util.ptempfile()
    ## KK 2023-04-24: @giorgo Is there a reason you used tempfile.NamedTemporaryFile and not util.ptempfile()?
    stdout_file = tempfile.NamedTemporaryFile(dir=config.PASH_SPEC_TMP_PREFIX)
    stdout_file = util.ptempfile()
    stderr_file = tempfile.NamedTemporaryFile(dir=config.PASH_SPEC_TMP_PREFIX)
    variable_file = util.ptempfile()
    logging.debug(f'Scheduler: Stdout file for: {node_id} is: {stdout_file}')
    logging.debug(f'Scheduler: Stderr file for: {node_id} is: {stderr_file}')
    logging.debug(f'Scheduler: Output variable file for: {node_id} is: {variable_file}')
    process = async_run_and_trace_command(command, trace_file, node_id, stdout_file, stderr_file, variable_file, sandbox_mode)
    return process, trace_file, stdout_file, stderr_file, variable_file

def async_run_and_trace_command_return_trace_in_sandbox(command, node_id):
    process, trace_file, stdout_file, stderr_file, variable_file = async_run_and_trace_command_return_trace(command, node_id, sandbox_mode=True)
    return process, trace_file, stdout_file, stderr_file, variable_file

def async_run_and_trace_command(command, trace_file, node_id, stdout_file, stderr_file, variable_file, sandbox_mode=False):
    ## Call Riker to execute the command
    run_script = f'{config.PASH_SPEC_TOP}/parallel-orch/run_command.sh'
    args = ["/bin/bash", run_script, command, trace_file, stdout_file, variable_file]
    if sandbox_mode:
        # print(" -- Sandbox mode")
        args.append("sandbox")
    else:
        # print(" -- Standard mode")
        args.append("standard")
    args.append(str(node_id))
    # Save output to temporary files to not saturate the memory
    process = subprocess.Popen(args, stdout=None, stderr=stderr_file)
    # For debugging
    # process = subprocess.Popen(args)
    return process

def commit_workspace(workspace_path):
    ## Call commit-sandbox.sh to commit the uncommitted sandbox to the main workspace 
    run_script = f'{config.PASH_SPEC_TOP}/overlay-sandbox/commit-sandbox.sh'
    args = ["/bin/bash", run_script, workspace_path]
    process = subprocess.check_output(args)
    return process

## Read trace and capture each command
def read_trace(sandbox_dir, trace_file):
    if sandbox_dir == "":
        path = trace_file
    else:
        path = f"{sandbox_dir}upperdir/{trace_file}"
    
    logging.debug(f'Reading trace from: {path}')
    with open(path) as f:
        return f.readlines()
