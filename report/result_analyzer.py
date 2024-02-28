import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import hashlib
import numpy as np
import sys
from datetime import datetime
from pprint import pprint
from datetime import datetime

class ResultAnalyzer:
    @staticmethod
    def process_results(orch_log):
        log_lines = orch_log.split("\n")
        prog_blocks = []
        performance_data = {}
        current_block = []
        block_start_time = None

        for line in log_lines:
            if line.startswith("INFO|") and "[PROG_LOG]" in line:
                parts = line.split("|")
                time_str = parts[1]
                log_content = parts[2].strip()
                if log_content == "[PROG_LOG]":
                    if current_block:
                        prog_blocks.append((block_start_time, current_block))
                        current_block = []
                    block_start_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S,%f")
                else:
                    state, node_id, command = log_content.replace("[PROG_LOG] ", "").split(",", 2)
                    current_block.append((node_id.strip(), state.strip()))
            elif line.startswith("INFO|") and "[PERFORMANCE_LOG]" in line:
                parts = line.split("]")[1].strip().split("||")
                unprocessed_time = line.split("]")[0].split("|")[1]
                log_time = datetime.strptime(unprocessed_time, "%Y-%m-%d %H:%M:%S,%f")
                key = parts[0].strip()
                optional_parts = parts[1:]
                time_from_start = ""
                step_time = ""
                message = ""

                for part in optional_parts:
                    if part.startswith("Time from start:"):
                        time_from_start = part.replace("Time from start:", "").strip()
                    elif part.startswith("Step time:"):
                        step_time = part.replace("Step time:", "").strip()
                    else:
                        message = part.strip()
                                
                if key not in performance_data:
                    performance_data[key] = []
                performance_data[key].append({
                    "log_time": log_time,
                    "time_from_start": time_from_start,
                    "step_time": step_time,
                    "message": message
                })

        # Process to create summary
        performance_summary = {}
        for key, entries in performance_data.items():
            entries.sort(key=lambda x: x['log_time'])  # Ensure chronological order
            last_initial_entry = None
            if key not in performance_summary:
                performance_summary[key] = []
                
            for entry in entries:
                if entry['step_time']:  # This entry is a second term of a pair
                    if last_initial_entry:
                        start_time = last_initial_entry['log_time']
                        end_time = entry['log_time']
                        step_time = entry['step_time']
                        performance_summary[key].append({
                            "start_time": start_time,
                            "end_time": end_time,
                            "step_time": float(step_time.strip("ms")),
                            "time_from_start": float(entry['time_from_start'].strip("ms")),
                            "message": entry['message']
                        })
                        last_initial_entry = None  # Reset for the next pair
                else:
                    # This entry is a potential first term of a pair, keep it and wait for its pair
                    if last_initial_entry:
                        # Keep the last of consecutive initial terms
                        performance_summary[key].append({
                            "start_time": last_initial_entry['log_time'],
                            "end_time": None,
                            "step_time": "",
                            "time_from_start": last_initial_entry['time_from_start'],
                            "message": last_initial_entry['message']
                        })
                    last_initial_entry = entry
            
            # Handle the last unpaired initial entry, if any
            if last_initial_entry:
                performance_summary[key].append({
                    "start_time": last_initial_entry['log_time'],
                    "end_time": None,
                    "step_time": "",
                    "time_from_start": last_initial_entry['time_from_start'],
                    "message": last_initial_entry['message']
                })

        # Append the last block if not empty
        if current_block:
            prog_blocks.append((block_start_time, current_block))

        return prog_blocks, performance_summary



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
    

def __main__():
    # Example usage

    with open(sys.argv[1], "r") as file:
        bash_output = file.read()
    pprint(ResultAnalyzer.process_results(bash_output)[1])
    pprint([len(x) for x in ResultAnalyzer.process_results(bash_output)[1].values()])
    
if __name__ == "__main__":
    __main__()