"""
Simple subprocess.run in a loop example.

Taken from https://www.biostars.org/p/174807/, with modifications.
"""

import os
import subprocess

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
prevent_java_conflicts = (
    "-XX:-UsePerfData -XX:-CreateCoredumpOnCrash "
    "-XX:ErrorFile=/dev/null "
    "-XX:+UnlockDiagnosticVMOptions "
    "-XX:-DumpPrivateMappingsInCore "
    "-XX:-DumpSharedMappingsInCore "
)

for currentFile in os.listdir(Orig_file_dir):
    if currentFile.endswith(".fa"):
        input_file = Orig_file_dir + currentFile
        NT_output_file = NT_align_file_dir + currentFile[:-3] + "_NT_aligned.fa"
        AA_output_file = AA_align_file_dir + currentFile[:-3] + "_AA_aligned.fa"
        MACSE_command = f"java {prevent_java_conflicts} -jar tools/macse_v1.01b.jar -prog alignSequences -seq {input_file} -out_NT {NT_output_file} -out_AA {AA_output_file}"
        subprocess.run(MACSE_command, shell=True)
