#!/bin/env python3

from enum import Enum
import os
import sys
from dateutil import parser
import plotly.express as px
from datetime import datetime, date, time


## TODO



class CommandState(Enum):
    EXECUTING = "Executing"
    EXECUTING_SANDBOXED = "Executing sandboxed"
    STOPPED_NETWORK = "Stopped: network"
    STOPPED_ERROR = "Stopped: ec!=0"
    WAITING = "Waiting"
    COMMITTED = "Committed"
    NO_STATE = "No state"

class PashSpecTraceObject:

    def __init__(self, timestamp: datetime, action: str, message):
        self.action = action
        self.message = message
        self.timestamp = timestamp.time()

    def __str__(self):
        return f"PashSpecTraceObject({self.timestamp}|{self.action}|{self.message})"

# TODO
class SchedulingStateSet:

    def handle_node(self, object):
        self.nodes = [node_id for node_id in object.message.split(",")]
        self.nodes.reverse()
        self.start_timestamp = object.timestamp
    
    def __init__(self):
        self.cmd_states = []
        self.unresolved_states = dict()
        self.nodes = []
        self.marks = []
        self.bash_timestamp = None
        self.start_timestamp = None

    def plot(self):
        self.cmd_states.sort(key=lambda x: x["Command_Id"])
        fig1 = px.timeline(self.cmd_states, 
                          y='Command_Id', 
                          x_start="Start", 
                          x_end="Finish", 
                          hover_data=['Command_Id', 'State'],
                          color="State",
                          category_orders={"0":1, "1":2, "2":3, "3":4, "4":5})
        fig1.update_layout(showlegend=True, xaxis_tickformat='%M:%S,%L', yaxis_title="Command ID", xaxis_title="Time (ms)")
        fig1.update_yaxes(categoryorder='array', categoryarray=self.nodes)
        fig1.update_traces(marker=dict(size=12,
                                      line=dict(width=2,
                                                color='DarkSlateGrey')),
                  selector=dict(mode='markers'))

        ## Add commit markers
        y = [mark["y"] for mark in self.marks if mark["event"] == "Commit"]
        x = [mark["x"] for mark in self.marks if mark["event"] == "Commit"]
        fig1.add_scatter(y=y, x=x,
            marker_symbol="diamond",
            marker=dict(color='Black', size=16),
            mode="markers",
            name="Commit")

        y = [mark["y"] for mark in self.marks if mark["event"] == CommandState.EXECUTING]
        x = [mark["x"] for mark in self.marks if mark["event"] == CommandState.EXECUTING]
        fig1.add_scatter(y=y, x=x,
            marker_symbol="circle",
            marker=dict(color='Black', size=16),
            mode="markers",
            name="Normal exec start")
        
        y = [mark["y"] for mark in self.marks if mark["event"] == CommandState.EXECUTING_SANDBOXED]
        x = [mark["x"] for mark in self.marks if mark["event"] == CommandState.EXECUTING_SANDBOXED]
        fig1.add_scatter(y=y, x=x,
            marker_symbol="circle",
            marker=dict(color='Red', size=16),
            mode="markers",
            name="Sandbox exec start")

        if self.bash_timestamp is not None:
            fig1.update_layout(shapes=[
            dict(
                type='line',
                yref='paper', y0=0, y1=1,
                xref='x', x0=self.bash_timestamp, x1=self.bash_timestamp
                )
            ])
        fig1.show()

    def add_task(self, node_id, start, end, state):
        self.cmd_states.append(dict(Command_Id=str(node_id), Start=start, Finish=end, State=state.value))


    def handle_executing_add(self, object):
        node_id = int(object.message)
        self.unresolved_states[node_id] = (object.timestamp, CommandState.EXECUTING)
        self.marks.append(dict(y=node_id, x=object.timestamp, event=CommandState.EXECUTING))

    def handle_executing_sandbox_add(self, object):
        node_id = int(object.message)
        self.unresolved_states[node_id] = (object.timestamp, CommandState.EXECUTING_SANDBOXED)
        self.marks.append(dict(y=node_id, x=object.timestamp, event=CommandState.EXECUTING_SANDBOXED))

    def handle_executing_remove(self, object):
        node_id = int(object.message)
        assert node_id in self.unresolved_states
        start, state = self.unresolved_states.pop(node_id)
        end = object.timestamp
        self.add_task(node_id, start, end, state)
        self.add_task(node_id, end, end, state)

    def handle_frontier_add(self, object):
        node_id = int(object.message)
        self.unresolved_states[node_id] = (object.timestamp, CommandState.FRONTIER)

    def handle_frontier_remove(self, object):
        pass

    def handle_stopped_add(self, object):
        node_str, reason = object.message.split(":")
        node_id = int(node_str)
        if reason == "error":
            self.unresolved_states[node_id] = (object.timestamp, CommandState.STOPPED_ERROR)
        elif reason == "network":
            self.unresolved_states[node_id] = (object.timestamp, CommandState.STOPPED_NETWORK)
        else:
            assert False

    def handle_stopped_remove(self, object):
        node_id = int(object.message)
        assert node_id in self.unresolved_states
        start, state = self.unresolved_states.pop(node_id)
        end = object.timestamp
        self.add_task(node_id, start, end, state)

    def handle_waiting_add(self, object):
        node_id = int(object.message)
        self.unresolved_states[node_id] = (object.timestamp, CommandState.WAITING)

    def handle_waiting_remove(self, object):
        node_id = int(object.message)
        assert node_id in self.unresolved_states
        start, state = self.unresolved_states.pop(node_id)
        end = object.timestamp
        self.add_task(node_id, start, end, state)

    def handle_commit(self, object):
        nodes = [str(node) for node in object.message.split(",")]
        for node in nodes:
            self.marks.append(dict(y=node, x=object.timestamp, event="Commit"))

    def handle_bash(self, object):
        self.bash_timestamp = datetime.strptime(object.message, "%M:%S.%f")
        print(datetime.strptime(object.message, "%M:%S.%f"))
        pass


def adjust_timestamp(state_set: SchedulingStateSet, trace_object):
    t = state_set.start_timestamp
    print(datetime(1900,1,1,0,0,0) + (datetime.combine(date.min, trace_object.timestamp) - datetime.combine(date.min, t)))
    trace_object.timestamp = datetime(1900,1,1,0,0,0) + (datetime.combine(date.min, trace_object.timestamp) - datetime.combine(date.min, t))

def parse_trace_objects(trace_file):
    with open(trace_file) as logfile:
        lines = logfile.read().split("\n")
    lines = [tuple(line.split("|")[1:]) for line in lines if line.startswith("TRACE|")]
    trace_objects = [PashSpecTraceObject(parser.parse(timestamp), action, message) for timestamp, action, message in lines]
    return trace_objects

def main():
    states = SchedulingStateSet()
    trace_file = os.path.join(os.path.abspath(sys.argv[1]))
    lines = parse_trace_objects(trace_file)
    for object in lines:
        action = object.action
        if action == "Nodes":
            states.handle_node(object)
        elif action == "ExecutingAdd":
            adjust_timestamp(states, object)
            states.handle_executing_add(object)
        elif action == "ExecutingSandboxAdd":
            adjust_timestamp(states, object)
            states.handle_executing_sandbox_add(object)
        if action == "ExecutingRemove":
            adjust_timestamp(states, object)
            states.handle_executing_remove(object)
        elif action == "StoppedAdd":
            adjust_timestamp(states, object)
            states.handle_stopped_add(object)
        elif action == "StoppedRemove":
            adjust_timestamp(states, object)
            states.handle_stopped_remove(object)
        elif action == "WaitingAdd":
            adjust_timestamp(states, object)
            states.handle_waiting_add(object)
        elif action == "WaitingRemove":
            adjust_timestamp(states, object)
            states.handle_waiting_remove(object)
        elif action == "Commit":
            adjust_timestamp(states, object)
            states.handle_commit(object)
        elif action == "Bash":
            states.handle_bash(object)
        else:
            pass
        #     print(f"No handle for {action} action implemented yet!")
    for o in states.cmd_states:
        print(o)
        # if isinstance(o.timestamp, time):
        #     o.timestamp = datetime.combine(date.min, o.timestamp)
    states.plot()

if __name__ == "__main__":
    main()