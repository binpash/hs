import config
import logging
import subprocess
import util
import os

# This module executes a sequence of commands 
# and traces them with Riker. 
# All commands are run inside an overlay sandbox.

def run_assignment_and_return_env_file(assignment: str, pre_execution_env_file: str):
    post_execution_env_file = util.ptempfile(prefix='hs_assignment_post_env')
    logging.debug(f'Running assignment: {assignment} | pre_execution_env_file: {pre_execution_env_file} | post_execution_env_file: {post_execution_env_file}')
    run_script = f'{config.PASH_SPEC_TOP}/parallel-orch/run_assignment.sh'
    args = ["/bin/bash", run_script, assignment, pre_execution_env_file, post_execution_env_file]
    process = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return post_execution_env_file

def async_run_and_trace_command_return_trace(command, concrete_node_id, execution_id, pre_execution_env_file, speculate_mode=False):
    trace_file = util.ptempfile(prefix='hs_trace')
    stdout_file = util.ptempfile(prefix='hs_stdout')
    stderr_file = util.ptempfile(prefix='hs_stderr')
    post_execution_env_file = util.ptempfile(prefix='hs_post_env')
    sandbox_dir, tmp_dir = util.create_sandbox()
    logging.debug(f'Scheduler: Stdout file for: {concrete_node_id} is: {stdout_file}')
    logging.debug(f'Scheduler: Stderr file for: {concrete_node_id} is: {stderr_file}')
    logging.debug(f'Scheduler: Trace file for: {concrete_node_id}: {trace_file}')
    process = async_run_and_trace_command_return_trace_in_sandbox(command, execution_id, trace_file, concrete_node_id, stdout_file, stderr_file, pre_execution_env_file, post_execution_env_file, sandbox_dir, tmp_dir, speculate_mode)
    return process, trace_file, stdout_file, stderr_file, pre_execution_env_file, post_execution_env_file, sandbox_dir

def async_run_and_trace_command_return_trace_in_sandbox_speculate(command, execution_id, concrete_node_id, pre_execution_env_file):
    process, trace_file, stdout_file, stderr_file, post_execution_env_file, sandbox_dir = async_run_and_trace_command_return_trace(command, execution_id, concrete_node_id, pre_execution_env_file, speculate_mode=True)
    return process, trace_file, stdout_file, stderr_file, post_execution_env_file, sandbox_dir

def async_run_and_trace_command_return_trace_in_sandbox(command, execution_id, trace_file, concrete_node_id, stdout_file, stderr_file, pre_execution_env_file, post_execution_env_file, sandbox_dir, tmp_dir, speculate_mode=False):
    ## Call Riker to execute the command
    run_script = f'{config.PASH_SPEC_TOP}/parallel-orch/run_command.sh'
    args = ["/bin/bash", run_script, command, trace_file, stdout_file, pre_execution_env_file, sandbox_dir, tmp_dir]
    if speculate_mode:
        args.append("speculate")
    else:
        args.append("standard")
    args.append(str(concrete_node_id))
    args.append(post_execution_env_file)
    args.append(str(execution_id))
    # Save output to temporary files to not saturate the memory
    logging.debug(args)
    process = subprocess.Popen(args, stdout=None, stderr=None)
    
    # For debugging
    # process = subprocess.Popen(args)
    return process

def commit_workspace(workspace_path):
    ## Call commit-sandbox.sh to commit the uncommitted sandbox to the main workspace 
    run_script = f'{config.PASH_SPEC_TOP}/deps/try/try'
    args = ["/bin/bash", run_script, "commit", workspace_path]
    process = subprocess.check_output(args)
    return process

## Read trace and capture each command
def read_trace(sandbox_dir, trace_file):
    if sandbox_dir == "":
        path = trace_file
    else:
        path = f"{sandbox_dir}/upperdir/{trace_file}"
    logging.debug(f'Reading trace from: {path}')
    with open(path) as f:
        return f.read().split('\n')[:-1]
    
def read_env_file(env_file, sandbox_dir=None):
    if sandbox_dir is None:
        path = env_file
    else:
        path = f"{sandbox_dir}/upperdir/{env_file}"
    logging.debug(f'Reading env from: {path}')
    out = subprocess.check_output([f"{os.getenv('PASH_TOP')}/compiler/orchestrator_runtime/pash_filter_vars.sh", path])
    return out.decode("utf-8")
