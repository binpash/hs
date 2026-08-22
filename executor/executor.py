"""Executor component — launches commands in sandboxes and traces them."""

import logging
import subprocess
import os

from dataclasses import dataclass
from executor_util import ptempfile, ptempdir, create_sandbox, copy, PASH_SPEC_TOP


@dataclass
class ExecCtxt:
    process: subprocess.Popen
    trace_file: str
    outfds: str
    stderr: str
    pre_env_file: str
    post_env_file: str
    sandbox_dir: str

@dataclass
class ExecResult:
    exit_code: int
    proc_id: int

@dataclass
class ExecArgs:
    command: str
    concrete_node_id: "ConcreteNodeId"
    execution_id: int
    pre_execution_env_file: str
    speculate_mode: bool
    lower_sandboxes: list[str]


def set_pgid():
    os.setpgid(0, 0)


# hs opens its log streams as descriptors and exports HS_*_LOG_FD so the JIT
# runtime can write to them directly. Those descriptors do not survive the
# close_fds spawn below, so children must fall back to appending by path --
# otherwise every pash_redir_output call fails with "Bad file descriptor".
# Scrubbing the variables here covers every process the scheduler starts.
_LOG_FD_VARS = ("HS_JIT_LOG_FD", "HS_SCHEDULER_LOG_FD",
                "HS_PREPROCESSOR_LOG_FD", "HS_INTERNAL_LOG_FD")


def child_env():
    """Environment for a subprocess that does not inherit hs's log descriptors."""
    env = os.environ.copy()
    for var in _LOG_FD_VARS:
        env.pop(var, None)
    return env

def run_assignment_and_return_env_file(assignment: str, pre_execution_env_file: str):
    post_execution_env_file = ptempfile(prefix='hs_assignment_post_env')
    logging.debug(f'Running assignment: {assignment} | pre_execution_env_file: {pre_execution_env_file} | post_execution_env_file: {post_execution_env_file}')
    run_script = f'{PASH_SPEC_TOP}/executor/run_assignment.sh'
    args = ["/bin/bash", run_script, assignment, pre_execution_env_file, post_execution_env_file]
    process = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             text=True, env=child_env())
    copy(pre_execution_env_file + '.fds', post_execution_env_file + '.fds')
    return post_execution_env_file

def run_trace_sandboxed(args: ExecArgs):
    run_script = f'{PASH_SPEC_TOP}/executor/run_command.sh'

    trace_file  = ptempfile(prefix='hs_trace')
    outfiles_dir = ptempdir(prefix='hs_outfiles')
    stderr_file = ptempfile(prefix='hs_stderr')
    logging.debug(f'Scheduler: Trace file for: {args.concrete_node_id}: {trace_file}')
    logging.debug(f'Scheduler: Stdout file for: {args.concrete_node_id} is: {outfiles_dir}')
    logging.debug(f'Scheduler: Stderr file for: {args.concrete_node_id} is: {stderr_file}')

    sandbox_dir, tmp_dir = create_sandbox()
    post_execution_env_file = ptempfile(prefix='hs_post_env')
    lower_dirs_str = ':'.join(args.lower_sandboxes)
    speculate_mode = "speculate" if args.speculate_mode else "standard"

    cmd = ["/bin/bash", run_script, args.command, trace_file, outfiles_dir, args.pre_execution_env_file, sandbox_dir, tmp_dir, speculate_mode, str(args.concrete_node_id), post_execution_env_file, str(args.execution_id), lower_dirs_str ]
    logging.debug(cmd)
    # stdout/stderr=None: inherit the daemon's, which hs pointed at the
    # internal-tooling log, so try's and strace's output goes there instead of
    # onto the traced script's stderr.
    process = subprocess.Popen(cmd, stdout=None, stderr=None,
                               preexec_fn=set_pgid, env=child_env())

    return ExecCtxt(process, trace_file, outfiles_dir, stderr_file, args.pre_execution_env_file, post_execution_env_file, sandbox_dir)

def commit_workspace(workspace_path):
    run_script = f'{PASH_SPEC_TOP}/deps/try/try'
    args = ["/bin/bash", run_script, "-i", "/run/mount", "commit", workspace_path]
    process = subprocess.check_output(args)
    return process

def read_trace(sandbox_dir, trace_file):
    if sandbox_dir == "":
        path = trace_file
    else:
        path = f"{sandbox_dir}/upperdir/{trace_file}"
    logging.debug(f'Reading trace from: {path}')
    with open(path) as f:
        return f.read().split('\n')[:-1]
