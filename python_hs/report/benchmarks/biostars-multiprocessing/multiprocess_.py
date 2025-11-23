"""
Multiprocessing version of biostars MACSE alignment.
Uses Pool.map to parallelize across .fa files.
"""

import os
import subprocess
from multiprocessing import Pool

Orig_file_dir = "data/biostars-multiprocessing/"
NT_align_file_dir = "output/biostars-multiprocessing/NT_aligned"
AA_align_file_dir = "output/biostars-multiprocessing/AA_aligned"

subprocess.run(["mkdir", "-p", NT_align_file_dir])
subprocess.run(["mkdir", "-p", AA_align_file_dir])

# Disable JVM features that cause false positive conflicts in speculative execution:
# -XX:-UsePerfData disables /tmp/hsperfdata files
# -XX:-CreateCoredumpOnCrash prevents writes to /proc/*/coredump_filter

# -XX:-DumpPrivateMappingsInCore and -XX:-DumpSharedMappingsInCore
# stops java from changing the core dump settings in /procs/self/coredump


def prevent_java_conflicts(perf_dir: str) -> str:
    return (
        f"-XX:PerfDataDir={perf_dir} "
        "-XX:-CreateCoredumpOnCrash "
        "-XX:ErrorFile=/dev/null "
        "-XX:+UnlockDiagnosticVMOptions "
        "-XX:-DumpPrivateMappingsInCore "
        "-XX:-DumpSharedMappingsInCore "
    )


def runMACSE(input_file, NT_output_file, AA_output_file):
    perf_dir = f"/tmp/hsperfdata_{os.path.splitext(input_file)[0]}"
    MACSE_command = f"java {prevent_java_conflicts(perf_dir)} -jar tools/macse_v1.01b.jar -prog alignSequences -seq {input_file} -out_NT {NT_output_file} -out_AA {AA_output_file}"
    subprocess.run(MACSE_command, shell=True)


def wrapRunMACSE(args):
    return runMACSE(*args)


args = [
    (
        Orig_file_dir + f,
        NT_align_file_dir + f[:-3] + "_NT_aligned.fa",
        AA_align_file_dir + f[:-3] + "_AA_aligned.fa",
    )
    for f in os.listdir(Orig_file_dir)
    if f.endswith(".fa")
]

p = Pool(16)
p.map(wrapRunMACSE, args)
