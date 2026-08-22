#!/usr/bin/env python3
"""Run one benchmark under each requested executor and compare the results.

Output layout, per test:

    output/<test>/<target>/          the program's OUTPUT_DIR -- and nothing else
    output/<test>/<target>_stdout    what the program wrote to stdout
    output/<test>/<target>_stderr    ... and to stderr
    output/<test>/<target>_time      wall clock seconds
    output/<test>/<target>_hashes    digest per output file (see output_manifest)
    output/<test>/hs_log             hs's own log
    output/<test>/hs_internal_log    stdout/stderr of hs's internal tooling
    output/<test>/strace_log         the strace trace of the sh run
    output/<test>/error              empty when sh and hs agree

The split matters: the harness used to write stdout, stderr and logs *into*
OUTPUT_DIR, so "compare every file in the output directory" compared harness
artifacts alongside program output and needed a growing exclusion list. Keeping
<target>/ pure means the default manifest ('**/*') is already exactly the
program's files, and a benchmark only needs an `outputs` manifest when its
results are somewhere else or need normalizing before hashing.
"""

import argparse
import os
import shutil
import sys
import time
from pathlib import Path
from subprocess import run

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import output_manifest

TARGETS = ['sh', 'hs', 'strace']


def parse_arguments():
    parser = argparse.ArgumentParser(description="Run benchmark")
    parser.add_argument('--window', default=16, type=int, help='Window size to run hs with')
    parser.add_argument('--target', nargs='+', choices=TARGETS,
                        default=['sh', 'hs'], help='Executors to run (sh, hs, strace)')
    parser.add_argument('--log', choices=['enable', 'disable'], default="enable",
                        help="Whether to write hs's own logs (they never reach the "
                             "script's stdout/stderr either way)")
    parser.add_argument('--script_name', required=True, help='Name of the script to run')
    parser.add_argument('--test_base', required=True, help='Base directory of the test')
    parser.add_argument('--hs_base', required=True, help='Base directory of hs')
    parser.add_argument('--env_vars', nargs='*', default=[], help='Environment variables to set')
    parser.add_argument('--suffix', help='Suffix for the output directory')
    parser.add_argument('--script-args', nargs=argparse.REMAINDER, help='Arguments to pass to the script')
    return parser.parse_args()


def cleanup_output_dir(output_base: Path):
    print(f"Cleaning up output directory: {output_base}")
    if output_base.exists() and output_base.is_dir():
        shutil.rmtree(output_base)
    output_base.mkdir(parents=True, exist_ok=True)


def artifact(output_base: Path, target: str, name: str) -> Path:
    """Path of a harness artifact for a target -- never inside its OUTPUT_DIR."""
    return output_base / f"{target}_{name}"


def execute(target: str, cmd: list, output_base: Path, env: dict) -> int:
    """Run one target and record its output as harness artifacts.

    OUTPUT_DIR is the target's own directory, so the files the program writes
    stay separated from everything the harness records about the run.

    The child writes straight into the stdout/stderr artifacts. Capturing
    through a pipe would buffer the whole stream in this process first, and
    benchmarks like dgsh and unix_50 send hundreds of megabytes to stdout.
    """
    output_dir = output_base / target
    output_dir.mkdir(parents=True, exist_ok=True)
    env = dict(env, OUTPUT_DIR=str(output_dir))

    cmd = [str(c) for c in cmd]
    print(f"Running {target} command: {' '.join(cmd)}")

    with open(artifact(output_base, target, 'stdout'), 'wb') as out, \
         open(artifact(output_base, target, 'stderr'), 'wb') as err:
        before = time.time()
        result = run(cmd, stdout=out, stderr=err, env=env)
        duration = time.time() - before

    artifact(output_base, target, 'time').write_text(f'{duration}\n')

    if result.returncode != 0:
        print(f"Warning: {target} run exited with {result.returncode}")
    return result.returncode


def sh_command(test_base: Path, script_name: str, script_args: list) -> list:
    return ['/bin/sh', test_base / script_name] + script_args


def hs_command(hs_base: Path, test_base: Path, script_name: str, script_args: list,
               window: int, log: bool, output_base: Path) -> list:
    hs_executable = hs_base / 'hs'
    if not hs_executable.exists():
        print(f"Error: The hs executable '{hs_executable}' does not exist.")
        exit(1)

    cmd = [hs_executable, '--window', str(window)]

    # Point every one of hs's log streams somewhere other than stderr, so the
    # captured stdout/stderr are exactly the traced program's and can be
    # compared against sh byte for byte. The three structured streams share one
    # file (hs opens it once and hands the same descriptor to each producer);
    # the internal-tooling stream -- try, strace, Python tracebacks -- stays
    # separate so a tool crash is not interleaved into the structured log.
    if log:
        structured = artifact(output_base, 'hs', 'log')
        internal = artifact(output_base, 'hs', 'internal_log')
        cmd.extend(['-d', '2'])
    else:
        structured = internal = Path('/dev/null')
    cmd.extend(['--jit-log', structured,
                '--scheduler-log', structured,
                '--preprocessor-log', structured,
                '--internal-log', internal])

    cmd.append(test_base / script_name)
    return cmd + script_args


def strace_command(test_base: Path, script_name: str, script_args: list,
                   output_base: Path) -> list:
    return ['strace', '-y', '-f', '--seccomp-bpf', '--trace=fork,clone,%file',
            '-o', artifact(output_base, 'strace', 'log'),
            '/bin/sh', test_base / script_name] + script_args


def record_hashes(target: str, output_base: Path, manifest, env: dict) -> list:
    """Digest the target's output files and save the per-file listing."""
    output_dir = output_base / target
    env = dict(env, OUTPUT_DIR=str(output_dir))
    lines = output_manifest.hash_outputs(output_dir, manifest, env)
    artifact(output_base, target, 'hashes').write_text(
        "".join(line + "\n" for line in lines))
    return lines


def compare_outputs(output_base: Path, manifest, env: dict):
    """Write `error`: empty if the sh and hs runs agree, else why they do not."""
    error_file = output_base / 'error'
    messages = []

    sh_hashes = record_hashes('sh', output_base, manifest, env)
    hs_hashes = record_hashes('hs', output_base, manifest, env)

    print(f"Comparing {len(sh_hashes)} output files selected by {manifest.source}")

    file_diffs = output_manifest.compare(sh_hashes, hs_hashes)
    if file_diffs:
        messages.append(f"Output files differ ({manifest.source}):")
        messages.extend(f"  {d}" for d in file_diffs)

    # stdout and stderr are program output too. hs keeps its own logs off both,
    # so any difference here is a real difference in what the script printed.
    # Digested by streaming rather than read into memory: these files are as
    # large as the benchmark's output.
    for stream in ('stdout', 'stderr'):
        sh_path = artifact(output_base, 'sh', stream)
        hs_path = artifact(output_base, 'hs', stream)
        if output_manifest.hash_file(sh_path) != output_manifest.hash_file(hs_path):
            messages.append(
                f"{stream} differs: sh {sh_path.stat().st_size} bytes,"
                f" hs {hs_path.stat().st_size} bytes"
                f" (see {sh_path.name} and {hs_path.name})")

    if messages:
        error_file.write_text("\n".join(messages) + "\n")
        print("FAIL: Outputs differ")
        for message in messages:
            print(f"  {message}")
    else:
        error_file.touch()
        digest = output_manifest.overall_digest(sh_hashes)
        print(f"PASS: Outputs match (digest {digest[:16]})")


def main():
    args = parse_arguments()
    test_base = Path(args.test_base).resolve()
    hs_base = Path(args.hs_base).resolve()
    script_name = args.script_name

    # Set environment variables
    env = os.environ.copy()
    for var in args.env_vars:
        key, value = var.split('=', 1)
        env[key] = value

    # Determine output base directory with optional suffix
    if test_base.parts[-2] == "benchmarks":
        local_name = test_base.parts[-1]
    else:
        local_name = os.sep.join(test_base.parts[-2:])
    if args.suffix:
        output_base = hs_base / "report" / "output" / f"{local_name}-{args.suffix}"
    else:
        output_base = hs_base / "report" / "output" / local_name

    targets = [t for t in TARGETS if t in args.target]
    if not targets:
        print("Not running anything, please specify --target")
        exit(1)

    manifest = output_manifest.Manifest.load(test_base)
    print(f"Output manifest: {manifest.source}")

    cleanup_output_dir(output_base)
    script_args = args.script_args or []

    for target in targets:
        if target == 'sh':
            cmd = sh_command(test_base, script_name, script_args)
        elif target == 'hs':
            cmd = hs_command(hs_base, test_base, script_name, script_args,
                             args.window, args.log == 'enable', output_base)
        else:
            cmd = strace_command(test_base, script_name, script_args, output_base)

        try:
            execute(target, cmd, output_base, env)
        except FileNotFoundError as e:
            print(f"Error: cannot run {target}: {e}")
            artifact(output_base, target, 'time').write_text('0\n')

    if 'sh' in targets and 'hs' in targets:
        compare_outputs(output_base, manifest, env)


if __name__ == '__main__':
    main()
