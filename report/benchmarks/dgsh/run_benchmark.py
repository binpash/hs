#!/usr/bin/env python3

import argparse
from pathlib import Path
import os
import time
import shutil
from subprocess import run, PIPE

def parse_arguments():
    parser = argparse.ArgumentParser(description="Run benchmark")
    parser.add_argument('--window', default=5, type=int, help='Window size to run hs with')
    parser.add_argument('--target', choices=['hs-only', 'sh-only', 'both'],
                        default='both', help='To run with sh or hs')
    parser.add_argument('--log', choices=['enable', 'disable'], default="enable",
                        help='Whether to enable logging for hs')
    parser.add_argument('--script_name', required=True, help='Name of the script to run')
    parser.add_argument('--test_base', required=True, help='Base directory of the test')
    parser.add_argument('--hs_base', required=True, help='Base directory of hs')
    parser.add_argument('--env_vars', nargs='*', default=[], help='Environment variables to set')
    return parser.parse_args()

def cleanup_output_dir(output_base: Path):
    print(f"Cleaning up output directory: {output_base}")
    if output_base.exists() and output_base.is_dir():
        shutil.rmtree(output_base)
    output_base.mkdir(parents=True, exist_ok=True)

def do_sh_run(test_base: Path, output_base: Path, env: dict, script_name: str):
    output_dir = output_base / 'sh'
    output_dir.mkdir(parents=True, exist_ok=True)
    env['OUTPUT_DIR'] = str(output_dir)

    cmd = ['/bin/sh', test_base / script_name]
    print(f"Running sh command: {' '.join([str(c) for c in cmd])}")

    before = time.time()
    result = run(cmd, stdout=PIPE, stderr=PIPE, env=env)
    duration = time.time() - before

    with open(output_dir / "stdout", 'wb') as f:
        f.write(result.stdout)

    with open(output_dir / "stderr", 'wb') as f:
        f.write(result.stderr)

    with open(output_base / "sh_time", 'w') as f:
        f.write(f'{duration}\n')

    return result.returncode

def do_hs_run(test_base: Path, output_base: Path, hs_base: Path, window: int, env: dict, log: bool, script_name: str):
    output_dir = output_base / 'hs'
    output_dir.mkdir(parents=True, exist_ok=True)
    env['OUTPUT_DIR'] = str(output_dir)

    hs_executable = hs_base / 'pash-spec.sh'

    if not hs_executable.exists():
        print(f"Error: The hs executable '{hs_executable}' does not exist.")
        exit(1)

    cmd = [str(hs_executable), '--window', str(window)]
    if log:
        cmd.extend(['-d', '2'])
    cmd.append(str(test_base / script_name))

    print(f"Running hs command: {' '.join(cmd)}")

    before = time.time()
    result = run(cmd, stdout=PIPE, stderr=PIPE, env=env)
    duration = time.time() - before

    with open(output_dir / "stdout", 'wb') as f:
        f.write(result.stdout)

    with open(output_dir / "stderr", 'wb') as f:
        f.write(result.stderr)

    with open(output_base / "hs_time", 'w') as f:
        f.write(f'{duration}\n')

    return result.returncode

def compare_outputs(output_base: Path):
    sh_output_dir = output_base / 'sh'
    hs_output_dir = output_base / 'hs'
    error_file = output_base / 'error'

    outputs_match = True

    print(f"Comparing outputs in {sh_output_dir} and {hs_output_dir}")

    # Compare stdout
    with open(sh_output_dir / "stdout", 'rb') as f1, open(hs_output_dir / "stdout", 'rb') as f2:
        sh_stdout = f1.read()
        hs_stdout = f2.read()

    if sh_stdout != hs_stdout:
        outputs_match = False
        with open(error_file, 'w') as errf:
            errf.write('Stdout differs between sh and hs runs.\n')

    # Compare generated files in OUTPUT_DIR/sh and OUTPUT_DIR/hs
    sh_files = list(sh_output_dir.glob('*'))
    hs_files = list(hs_output_dir.glob('*'))

    # Exclude stdout and stderr files from comparison
    sh_file_names = {f.name for f in sh_files if f.name not in ['stdout', 'stderr']}
    hs_file_names = {f.name for f in hs_files if f.name not in ['stdout', 'stderr']}

    if sh_file_names != hs_file_names:
        outputs_match = False
        with open(error_file, 'a') as errf:
            errf.write('Generated files differ between sh and hs runs.\n')
            errf.write(f'Files in sh run: {sorted(sh_file_names)}\n')
            errf.write(f'Files in hs run: {sorted(hs_file_names)}\n')

    # Compare contents of files with same names
    common_files = sh_file_names & hs_file_names
    for fname in common_files:
        sh_file = sh_output_dir / fname
        hs_file = hs_output_dir / fname
        with open(sh_file, 'rb') as f1, open(hs_file, 'rb') as f2:
            sh_content = f1.read()
            hs_content = f2.read()
        if sh_content != hs_content:
            outputs_match = False
            with open(error_file, 'a') as errf:
                errf.write(f'Contents of file {fname} differ between sh and hs runs.\n')

    if outputs_match and error_file.exists():
        error_file.unlink()

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

    # Output base directory
    local_name = os.sep.join(test_base.parts[-2:])
    output_base = hs_base / "report" / "output" / local_name

    run_hs = args.target in ["hs-only", "both"]
    run_sh = args.target in ["sh-only", "both"]

    if not run_hs and not run_sh:
        print("Not running anything, please specify --target")
        exit(1)

    # Cleanup previous outputs
    cleanup_output_dir(output_base)

    if run_sh:
        sh_returncode = do_sh_run(test_base, output_base, env, script_name)
    if run_hs:
        hs_returncode = do_hs_run(test_base, output_base, hs_base, args.window, env, args.log == 'enable', script_name)
    if run_sh and run_hs:
        compare_outputs(output_base)

if __name__ == '__main__':
    main()