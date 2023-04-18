#!/bin/env python3

from enum import Enum
import os
import sys
from dateutil import parser
import datetime
from collections import defaultdict
import plotly.express as ff
import plotly.graph_objects as go
from pprint import pprint


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

    def __init__(self, timestamp: datetime.datetime, action: str, message):
        self.action = action
        self.message = message
        self.timestamp = timestamp

    def __str__(self):
        return f"PashSpecTraceObject({self.timestamp}|{self.action}|{self.message})"

# TODO
class SchedulingStateSet:

    def handle_node(self, object):
        self.nodes = [node_id for node_id in object.message.split(",")]
        self.nodes.reverse()
    
    def __init__(self):
        self.cmd_states = []
        self.unresolved_states = dict()
        self.nodes = []
        self.marks = []

    def plot(self):
        self.cmd_states.sort(key=lambda x: x["Command_Id"])
        fig1 = ff.timeline(self.cmd_states, 
                          y='Command_Id', 
                          x_start="Start", 
                          x_end="Finish", 
                          hover_data=['Command_Id', 'State'],
                          color="State",
                          category_orders={"0":1, "1":2, "2":3, "3":4, "4":5})
        fig1.update_layout(showlegend=True, xaxis_tickformat='%M,%L', yaxis_title="Command ID", xaxis_title="Time (ms)")
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
            mode="markers")

        y = [mark["y"] for mark in self.marks if mark["event"] == CommandState.EXECUTING]
        x = [mark["x"] for mark in self.marks if mark["event"] == CommandState.EXECUTING]
        fig1.add_scatter(y=y, x=x,
            marker_symbol="circle",
            marker=dict(color='Black', size=16),
            mode="markers")
        
        y = [mark["y"] for mark in self.marks if mark["event"] == CommandState.EXECUTING_SANDBOXED]
        x = [mark["x"] for mark in self.marks if mark["event"] == CommandState.EXECUTING_SANDBOXED]
        fig1.add_scatter(y=y, x=x,
            marker_symbol="circle",
            marker=dict(color='Red', size=16),
            mode="markers")
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
        print(object.message)
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
        assert node_id in self.unresolved_states # and (self.unresolved_states[node_id] == CommandState.EXECUTING or self.unresolved_states[node_id] == CommandState.EXECUTING_SANDBOXED)
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

def parse_trace_objects(trace_file):
    now_time = datetime.datetime.now()
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
        print(object)
        action = object.action
        # print(f"_{action}_")
        if action == "Nodes":
            states.handle_node(object)
        elif action == "ExecutingAdd":
            states.handle_executing_add(object)
        elif action == "ExecutingSandboxAdd":
            states.handle_executing_sandbox_add(object)
        if action == "ExecutingRemove":
            states.handle_executing_remove(object)
        elif action == "StoppedAdd":
            states.handle_stopped_add(object)
        elif action == "StoppedRemove":
            states.handle_stopped_remove(object)
        elif action == "WaitingAdd":
            states.handle_waiting_add(object)
        elif action == "WaitingRemove":
            states.handle_waiting_remove(object)
        elif action == "Commit":
            states.handle_commit(object)
        else:
            pass
        #     print(f"No handle for {action} action implemented yet!")
    states.plot()

if __name__ == "__main__":
    main()