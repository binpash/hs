"""Executor component — launches commands in sandboxes and traces them."""

import logging
import subprocess
import os

from dataclasses import dataclass
from executor_util import ptempfile, ptempdir, create_sandbox, copy, PASH_SPEC_TOP


@dataclass
class ExecCtxt:
    process: subprocess.Popen
    trace_file: str   # base path; .r/.w are streaming files, .missed written at exit
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

def run_assignment_and_return_env_file(assignment: str, pre_execution_env_file: str):
    post_execution_env_file = ptempfile(prefix='hs_assignment_post_env')
    logging.debug(f'Running assignment: {assignment} | pre_execution_env_file: {pre_execution_env_file} | post_execution_env_file: {post_execution_env_file}')
    run_script = f'{PASH_SPEC_TOP}/executor/run_assignment.sh'
    args = ["/bin/bash", run_script, assignment, pre_execution_env_file, post_execution_env_file]
    process = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
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
    for suffix in ('.r', '.w'):
        # Streaming FIFOs for the read/write dependency sets. Both ends now live
        # in the host mount namespace: fstrace (the writer) wraps try from the
        # OUTSIDE (see run_command.sh), and the scheduler's reader threads are
        # outside try as well. No overlay/bind-mount coordination is needed.
        os.mkfifo(trace_file + suffix)
    post_execution_env_file = ptempfile(prefix='hs_post_env')
    lower_dirs_str = ':'.join(args.lower_sandboxes)
    speculate_mode = "speculate" if args.speculate_mode else "standard"

    cmd = ["/bin/bash", run_script, args.command, trace_file, outfiles_dir, args.pre_execution_env_file, sandbox_dir, tmp_dir, speculate_mode, str(args.concrete_node_id), post_execution_env_file, str(args.execution_id), lower_dirs_str ]
    logging.debug(cmd)
    process = subprocess.Popen(cmd, stdout=None, stderr=None, preexec_fn=set_pgid)

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
