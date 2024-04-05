import os
import csv

class ReportGenerator:
    @staticmethod
    def save_log_data(log_data, output_dir, filename):
        with open(os.path.join(output_dir, filename), 'w') as file:
            file.write(log_data)

    @staticmethod
    def calculate_time_differences(bash_time, orch_time):
        min_time = min(bash_time, orch_time) if bash_time != 0 and orch_time != 0 else 1
        percent_diff = ((bash_time - orch_time) / min_time) * 100
        times_diff = max(bash_time, orch_time) / min_time

        return percent_diff, round(times_diff, 2)

    @staticmethod
    def print_results(benchmark_name, bash_time, orch_time, same_results, diff_lines, verbose=False):
        percent_diff, times_diff = ReportGenerator.calculate_time_differences(bash_time, orch_time)

        speed_comparison = "hs is faster" if bash_time > orch_time else "hs is slower"

        if verbose:
            print(f"Results for benchmark: {benchmark_name}")
            if bash_time != 0:
                print(f"Bash Execution Time: {bash_time:.02f}s")
            if orch_time != 0:
                print(f"hs Execution Time: {orch_time:.02f}s")
                print(f"Valid: {'Yes' if same_results else 'No - see below'}")
            for line in diff_lines:
                print(line)
            if bash_time != 0 and orch_time != 0:
                comparison_result = f"{speed_comparison} than Bash ({times_diff}x {'faster' if bash_time > orch_time else 'slower'})"
        else:
            print(f"{benchmark_name:20s} | Valid: {'Yes |' if len(diff_lines) == 0 else 'No'}", end=" ")
            if len(diff_lines) == 0:
                if bash_time != 0 and orch_time != 0:
                    comparison_result = f"hs is {times_diff}x {'faster' if bash_time > orch_time else 'slower'}"

        if bash_time != 0 and orch_time != 0:
            print(comparison_result)

    @staticmethod
    def generate_csv_report(results, output_dir, filename):
        with open(os.path.join(output_dir, filename), 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Benchmark", "Bash Execution Time", "hs Execution Time", "Valid", "Comparison"])
            for result in results:
                percent_diff, times_faster = ReportGenerator.calculate_time_differences(result[1], result[2])
                speed_comparison = "hs is faster than Bash" if result[1] > result[2] else "hs is slower than Bash"
                comparison = f"{'' if result[1] > result[2] else '-'}{times_faster:2f}x"
                writer.writerow([result[0], result[1], result[2], result[3], comparison])
