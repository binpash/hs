import difflib
import os
import csv

class ResultAnalyzer:
    @staticmethod
    def parse_logs_into_activities(log_data):
        info_lines = [line.replace("INFO:root:>|", "").split("|") for line in log_data.split("\n") if line.startswith("INFO:root:>|")]
        activities = []
        for line in info_lines:
            if len(line) == 4:
                activity = line[1]
                end_time = float(line[2].split(":")[1].rstrip("ms"))
                step_time = float(line[3].split(":")[1].rstrip("ms"))
                start_time = end_time - step_time
                activities.append((activity, start_time, step_time))
        return activities

    @staticmethod
    def compare_results(bash_output, orch_output):
        bash_lines = bash_output.splitlines()
        orch_lines = orch_output.splitlines()
        d = difflib.ndiff(bash_lines, orch_lines)
        return [diff for diff in d if diff.startswith('- ') or diff.startswith('+ ')]

    @staticmethod
    def analyze_node_execution_times(orch_output, benchmark_name, output_dir, verbose):
        node_times_dict = ResultAnalyzer.extract_node_times(orch_output)

        if verbose:
            ResultAnalyzer.print_node_execution_times(node_times_dict)

        ResultAnalyzer.generate_node_times_csv(node_times_dict, benchmark_name, output_dir)

    @staticmethod
    def print_node_execution_times(node_times_dict):
        print("-" * 40)
        print("Node Execution Times:")
        for node in sorted(node_times_dict.keys()):
            times = node_times_dict[node]
            num_executions = len(times)
            time_lost = sum(times) - times[-1] if times else 0
            times_str = ', '.join(f'{time:7.2f}ms' for time in times)
            print(f"Node {node:2d}: Executions: {num_executions}, Time Lost: {time_lost:7.2f}ms Times = {times_str} ")
        print("-" * 40)
        
    @staticmethod
    def generate_node_times_csv(node_times_dict, benchmark_name, output_dir):
        csv_filename = os.path.join(output_dir, f"{benchmark_name}_execution_times.csv")
        with open(csv_filename, 'w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["Node", "Execution Times (ms)", "Number of Executions", "Time Lost (ms)"])
            for node in sorted(node_times_dict.keys()):
                times = node_times_dict[node]
                num_executions = len(times)
                time_lost = sum(times) - times[-1] if times else 0
                writer.writerow([node, ', '.join(str(time) for time in times), num_executions, time_lost])

    @staticmethod
    def extract_node_times(orch_output):
        node_times_dict = {}

        relevant_lines = [line.replace("INFO:root:>|PartialOrder|RunNode,", "") 
                        for line in orch_output.split("\n") 
                        if line.startswith("INFO:root:>|PartialOrder|RunNode,") and "Step time:" in line]

        for line in relevant_lines:
            parts = line.split("|")
            node_id = int(parts[0])
            time = float(parts[2].split(":")[1][:-2])  # Extract step time

            if node_id not in node_times_dict:
                node_times_dict[node_id] = []
            node_times_dict[node_id].append(time)

        return node_times_dict
