import config
import logging
import subprocess
import util
import os

from dataclasses import dataclass
from node import ConcreteNodeId

@dataclass
class ExecutorArgs:
    command: str
    concrete_node_id: ConcreteNodeId
    execution_id: int
    pre_execution_env_file: str
    speculate_mode: bool
    lower_sandboxes: list[str]

    trace_file: str = ""
    stdout_file: str = ""
    stderr_file: str = ""
    post_execution_env_file: str = ""
    sandbox_dir: str = ""
    tmp_dir: str = ""

# This module executes a sequence of commands
# and traces them with Riker.
# All commands are run inside an overlay sandbox.

def set_pgid():
    os.setpgid(0, 0)

def run_assignment_and_return_env_file(assignment: str, pre_execution_env_file: str):
    post_execution_env_file = util.ptempfile(prefix='hs_assignment_post_env')
    logging.debug(f'Running assignment: {assignment} | pre_execution_env_file: {pre_execution_env_file} | post_execution_env_file: {post_execution_env_file}')
    run_script = f'{config.PASH_SPEC_TOP}/parallel-orch/run_assignment.sh'
    args = ["/bin/bash", run_script, assignment, pre_execution_env_file, post_execution_env_file]
    process = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return post_execution_env_file

def async_run_and_trace_command_return_trace(args: ExecutorArgs):
    args.trace_file = util.ptempfile(prefix='hs_trace')
    args.stdout_file = util.ptempfile(prefix='hs_stdout')
    args.stderr_file = util.ptempfile(prefix='hs_stderr')
    args.post_execution_env_file = util.ptempfile(prefix='hs_post_env')
    args.sandbox_dir, args.tmp_dir = util.create_sandbox()
    logging.debug(f'Scheduler: Stdout file for: {args.concrete_node_id} is: {args.stdout_file}')
    logging.debug(f'Scheduler: Stderr file for: {args.concrete_node_id} is: {args.stderr_file}')
    logging.debug(f'Scheduler: Trace file for: {args.concrete_node_id}: {args.trace_file}')
    process = async_run_and_trace_command_return_trace_in_sandbox(args)
    return process, args

def async_run_and_trace_command_return_trace_in_sandbox_speculate(args: ExecutorArgs):
    process, args = async_run_and_trace_command_return_trace(args)
    return process, args

def async_run_and_trace_command_return_trace_in_sandbox(args: ExecutorArgs):
    ## Call Riker to execute the command
    run_script = f'{config.PASH_SPEC_TOP}/parallel-orch/run_command.sh'
    lower_dirs_str = ':'.join(args.lower_sandboxes)
    cmd = ["/bin/bash", run_script, args.command, args.trace_file, args.stdout_file, args.pre_execution_env_file, args.sandbox_dir, args.tmp_dir]
    if args.speculate_mode:
        cmd.append("speculate")
    else:
        cmd.append("standard")
    cmd.append(str(args.concrete_node_id))
    cmd.append(args.post_execution_env_file)
    cmd.append(str(args.execution_id))
    cmd.append(lower_dirs_str)
    # Save output to temporary files to not saturate the memory
    logging.debug(cmd)
    process = subprocess.Popen(cmd, stdout=None, stderr=None, preexec_fn=set_pgid)

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
