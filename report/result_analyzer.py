import difflib

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
