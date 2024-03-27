from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import hashlib
import numpy as np

class ResultAnalyzer:
    @staticmethod
    def process_results(orch_log):
        log_lines = orch_log.split("\n")
        prog_blocks = []
        current_block = []
        block_start_time = None

        for line in log_lines:
            line: str
            if line.startswith("INFO|") and "[PROG_LOG]" in line and ("[PROG_LOG] canon:" not in line and "[PROG_LOG] spec:" not in line):
                parts = line.split("|")
                time_str = parts[1]
                log_content = parts[2].strip()
                if log_content == "[PROG_LOG]":
                    # Start of a new block
                    if current_block:
                        prog_blocks.append((block_start_time, current_block))
                        current_block = []
                    block_start_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S,%f")
                else:
                    # Continuing the current block
                    try:
                        state = log_content.replace("[PROG_LOG] ", "").split()[0]
                        node_id = log_content.split("--- ", 1)[-1]
                        # command = log_content.replace("[PROG_LOG] ", "").rsplit("--- ", 1,)[0].strip()
                        int(node_id.strip().strip("@"))
                        print(state)
                        current_block.append((node_id.strip().strip("@"), state.strip()))

                    except ValueError:
                        # print(f"Error parsing line: {line}")
                        pass

        # Append the last block if not empty
        if current_block:
            prog_blocks.append((block_start_time, current_block))

        return prog_blocks

    @staticmethod
    def compare_results(bash_output, orch_output, max_lines=1000):
        # Limit the number of lines to compare
        bash_lines = bash_output.splitlines()[:max_lines]
        orch_lines = orch_output.splitlines()[:max_lines]

        # Use a hash-based method for quick equality checks
        bash_hashes = {hashlib.md5(line.encode()).hexdigest(): line for line in bash_lines}
        orch_hashes = {hashlib.md5(line.encode()).hexdigest(): line for line in orch_lines}

        diffs = []
        for hash_value, line in bash_hashes.items():
            if hash_value not in orch_hashes:
                diffs.append(f'- {line}')
        for hash_value, line in orch_hashes.items():
            if hash_value not in bash_hashes:
                diffs.append(f'+ {line}')

        return diffs