from datetime import datetime
import hashlib

class ResultAnalyzer:
    @staticmethod
    def process_results(orch_log):
        log_lines = orch_log.split("\n")
        prog_blocks = []
        current_block = []
        block_start_time = None
        next_line = False
        
        for line in log_lines:
            if next_line and "---" in line:
                node_id = line.split("---")[1].strip().strip("@")
                current_block.append((node_id.strip(), state.strip()))
                next_line = False
            elif line.startswith("INFO|") and \
            "[PROG_LOG]" in line and \
            "] canon:" not in line and \
            "] spec:" not in line:
                parts = line.split("|")
                time_str = parts[1]
                log_content = " ".join(parts[2:]).strip()
                if log_content == "[PROG_LOG]":
                    # Start of a new block
                    if current_block:
                        prog_blocks.append((block_start_time, current_block))
                        current_block = []
                    block_start_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S,%f")
                elif "---" in line:
                    state = log_content.replace("[PROG_LOG] ", "").strip().split()[0]
                    node_id = log_content.split("---")[1].strip().strip("@")
                    current_block.append((node_id.strip(), state.strip()))
                else:
                    state = log_content.replace("[PROG_LOG] ", "").strip().split()[0]
                    next_line = True
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