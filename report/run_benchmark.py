#!/usr/bin/env python3

import argparse
from pathlib import Path
import os
import time
import shutil
from subprocess import run, PIPE

def parse_arguments():
    parser = argparse.ArgumentParser(description="Run benchmark")
    parser.add_argument('--window', default=16, type=int, help='Window size to run hs with')
    parser.add_argument('--target', choices=['hs-only', 'sh-only', 'pash-only', 'both', 'all'],
                        default='both', help='To run with sh, hs, pash, or combinations')
    parser.add_argument('--log', choices=['enable', 'disable'], default="enable",
                        help='Whether to enable logging for hs')
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

def do_sh_run(test_base: Path, output_base: Path, env: dict, script_name: str, script_args: list):
    output_dir = output_base / 'sh'
    output_dir.mkdir(parents=True, exist_ok=True)
    env['OUTPUT_DIR'] = str(output_dir)

    cmd = ['/bin/sh', str(test_base / script_name)] + script_args
    print(f"Running sh command: {' '.join([str(c) for c in cmd])}")

    before = time.time()
    result = run(cmd, stdout=PIPE, stderr=PIPE, env=env)
    duration = time.time() - before

    if result.returncode != 0:
        print(f"Error: Non-zero return code from sh run")
    if len(result.stderr) > 0:
        print(f"Error: Non-empty stderr from sh run")
    
    

    with open(output_dir / "stdout", 'wb') as f:
        f.write(result.stdout)

    with open(output_dir / "stderr", 'wb') as f:
        f.write(result.stderr)

    with open(output_base / "sh_time", 'w') as f:
        f.write(f'{duration}\n')

    return result.returncode

def do_hs_run(test_base: Path, output_base: Path, hs_base: Path, window: int, env: dict, log: bool, script_name: str, script_args: list):
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
    cmd.extend(script_args)

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

    # Create a symlink for hs_log pointing to stderr
    hs_log_path = output_base / "hs_log"
    stderr_path = output_dir / "stderr"
    if hs_log_path.exists() or hs_log_path.is_symlink():
        hs_log_path.unlink()
    hs_log_path.symlink_to(stderr_path)

    return result.returncode

def do_pash_run(test_base: Path, output_base: Path, hs_base: Path, window: int, env: dict, script_name: str, script_args: list):
    output_dir = output_base / 'pash'
    output_dir.mkdir(parents=True, exist_ok=True)
    env['OUTPUT_DIR'] = str(output_dir)

    # PaSh executable is at PASH_TOP/pa.sh, where PASH_TOP is /srv/hs/deps/pash
    pash_executable = hs_base / 'deps' / 'pash' / 'pa.sh'

    if not pash_executable.exists():
        print(f"Error: The PaSh executable '{pash_executable}' does not exist.")
        exit(1)

    # Check for PaSh-compatible variant first (e.g., 1_1_pash.sh)
    script_path = test_base / script_name
    script_stem = script_path.stem  # e.g., "1_1" from "1_1.sh"
    script_suffix = script_path.suffix  # e.g., ".sh"
    pash_variant = test_base / f"{script_stem}_pash{script_suffix}"
    
    # Use PaSh variant if it exists, otherwise fall back to regular script
    if pash_variant.exists():
        script_to_run = pash_variant
        print(f"Using PaSh-compatible variant: {pash_variant.name}")
    else:
        script_to_run = script_path
        print(f"Using regular script: {script_name}")

    cmd = [str(pash_executable), '--width', str(window)]
    cmd.append(str(script_to_run))
    cmd.extend(script_args)

    print(f"Running pash command: {' '.join(cmd)}")

    before = time.time()
    result = run(cmd, stdout=PIPE, stderr=PIPE, env=env)
    duration = time.time() - before

    with open(output_dir / "stdout", 'wb') as f:
        f.write(result.stdout)

    with open(output_dir / "stderr", 'wb') as f:
        f.write(result.stderr)

    with open(output_base / "pash_time", 'w') as f:
        f.write(f'{duration}\n')

    return result.returncode

def compare_outputs(output_base: Path, dir1_name: str, dir2_name: str, error_file_name: str = 'error'):
    dir1_output_dir = output_base / dir1_name
    dir2_output_dir = output_base / dir2_name
    error_file = output_base / error_file_name

    outputs_match = True
    error_messages = []

    print(f"Comparing outputs in {dir1_output_dir} and {dir2_output_dir}")

    # Helper function to recursively gather file paths relative to a base directory, excluding specific files
    def get_all_files(base_dir: Path):
        exclude_files = {'stderr', 'hs_log'}
        return {
            str(f.relative_to(base_dir))
            for f in base_dir.rglob('*')
            if f.is_file() and f.name not in exclude_files
        }

    # Gather all files (including in subdirectories) excluding `stderr` and `hs_log`
    dir1_files = get_all_files(dir1_output_dir)
    dir2_files = get_all_files(dir2_output_dir)

    # Compare file lists
    if dir1_files != dir2_files:
        outputs_match = False
        error_messages.append(f'Generated files differ between {dir1_name} and {dir2_name} runs.\n')
        error_messages.append(f'Files in {dir1_name} run: {sorted(dir1_files)}\n')
        error_messages.append(f'Files in {dir2_name} run: {sorted(dir2_files)}\n')
    else:
        print(f"All files (excluding stderr and hs_log) match: {len(dir1_files)} files")

    # Compare contents of files present in both directories
    common_files = dir1_files & dir2_files
    for relative_path in common_files:
        dir1_file = dir1_output_dir / relative_path
        dir2_file = dir2_output_dir / relative_path

        with open(dir1_file, 'rb') as f1, open(dir2_file, 'rb') as f2:
            dir1_content = f1.read()
            dir2_content = f2.read()

        if dir1_content != dir2_content:
            outputs_match = False
            error_messages.append(f'Contents of file {relative_path} differ between {dir1_name} and {dir2_name} runs.\n')

    # Check for missing files
    missing_in_dir1 = dir2_files - dir1_files
    missing_in_dir2 = dir1_files - dir2_files
    for missing_file in missing_in_dir1:
        outputs_match = False
        error_messages.append(f'File {missing_file} is missing in {dir1_name} run.\n')
    for missing_file in missing_in_dir2:
        outputs_match = False
        error_messages.append(f'File {missing_file} is missing in {dir2_name} run.\n')

    # Write errors or create an empty error file if no errors
    if outputs_match:
        error_file.touch()
        print(f"PASS: Outputs match between {dir1_name} and {dir2_name}")
    else:
        with open(error_file, 'w') as errf:
            errf.writelines(error_messages)
            print(f"FAIL: Outputs differ between {dir1_name} and {dir2_name}")

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

    run_hs = args.target in ["hs-only", "both", "all"]
    run_sh = args.target in ["sh-only", "both", "all"]
    run_pash = args.target in ["pash-only", "all"]

    if not run_hs and not run_sh and not run_pash:
        print("Not running anything, please specify --target")
        exit(1)

    # Cleanup previous outputs
    cleanup_output_dir(output_base)

    script_args = args.script_args or []

    if run_sh:
        sh_returncode = do_sh_run(test_base, output_base, env, script_name, script_args)
    if run_hs:
        hs_returncode = do_hs_run(test_base, output_base, hs_base, args.window, env, args.log == 'enable', script_name, script_args)
    if run_pash:
        pash_returncode = do_pash_run(test_base, output_base, hs_base, args.window, env, script_name, script_args)
    
    # Comparison logic:
    # - "both": compare hs vs sh
    # - "all": compare hs vs sh and pash vs sh
    if args.target == "both" and run_sh and run_hs:
        compare_outputs(output_base, 'sh', 'hs')
    elif args.target == "all":
        if run_sh and run_hs:
            compare_outputs(output_base, 'sh', 'hs', 'error_hs')
        if run_sh and run_pash:
            compare_outputs(output_base, 'sh', 'pash', 'error_pash')

if __name__ == '__main__':
    main()