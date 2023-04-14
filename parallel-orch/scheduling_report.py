import os
import dateutil
import datetime



## TODO
def handle_executing_add(message):
    pass

def handle_executing_sandbox_add(message):
    pass

def handle_executing_remove(message):
    pass

def handle_workset_add(message):
    pass

def handle_workset_remove(message):
    pass

def handle_frontier_add(message):
    pass

def handle_frontier_remove(message):
    pass

def handle_stopped_add(message):
    pass

def handle_stopped_remove(message):
    pass

def handle_waiting_add(message):
    pass

def handle_waiting_remove(message):
    pass

def handle_commit(message):
    pass


class SchedulerAction(Enum):
    ExecutingAdd = handle_executing_add
    ExecutingSandboxAdd = handle_executing_sandbox_add
    ExecutingRemove = handle_executing_remove
    WorksetAdd = handle_workset_add
    WorksetRemove = handle_workset_remove
    FrontierAdd = handle_frontier_add
    FrontierRemove = handle_frontier_remove
    StoppedAdd = handle_stopped_add
    StoppedRemove = handle_stopped_remove
    WaitingAdd = handle_waiting_add
    WaitingRemove = handle_waiting_remove
    Commit = handle_commit


class PathSpecTraceObject:

    def __init__(self, timestamp: datetime.datetime, action: str, message):
        self.action = action
        self.message = message
        self.timestamp = timestamp

    def __str__(self):
        return f"PathSpecTraceObject({self.timestamp}, {self.action}, {self.message})"

# TODO
class SchedulingStateSet:

    def __init__(self):
        pass


def parse_trace_objects(trace_file):
    with open(trace_file) as logfile:
        lines = logfile.read().split("\n")
    lines = [tuple(line.split("|")[1:]) for line in lines if line.startswith("TRACE|")]
    trace_objects = [PathSpecTraceObject(dateutil.parser.parse(timestamp), action, message) for timestamp, action, message in lines]
    return trace_objects





def main():
    trace_file = os.path.join(os.getcwd(), "logs", "log.txt")
    lines = parse_trace_objects(trace_file)
    for l in lines:
        print(l)

if __name__ == "__main__":
    main()