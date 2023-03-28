import re
from typing import Tuple

# Parse the Riker trace structure
#
# TODO: This module will need to contain the definition 
# of the trace structure and its methods that we will use to parse it.

def remove_command_redir(cmd):
    return cmd.split(">")[0].rstrip()

def remove_command_prefix(line):
    return line.split(f"]: ")[1].rstrip()

def get_command_prefix(line):
    return line.split(f"]: ")[0].rstrip()[1:]

def is_no_command_prefix(line):
    return "No Command" in get_command_prefix(line)

def is_new_path_ref(trace_item):
    return "PathRef" in trace_item

def get_path_ref_id(trace_item):
    return trace_item.split("=")[0].strip()

def get_path_ref_open_config(trace_item):
    assert(is_new_path_ref(trace_item))
    ## WARNING: HACK
    open_config_suffix = trace_item.split(", ")[2]
    open_config = re.split('\(|\)', open_config_suffix)[0].rstrip()
    return open_config

def is_path_ref_read(trace_item):
    open_config = get_path_ref_open_config(trace_item)
    return (open_config[0] == "r")
        
def is_path_ref_write(trace_item):
    open_config = get_path_ref_open_config(trace_item)
    return (open_config[1] == "w")

def is_path_ref_empty(trace_item):
    open_config = get_path_ref_open_config(trace_item)
    return (open_config[1] == "-" and open_config[0] == "-")

def get_path_ref_name(trace_item):
    assert(is_new_path_ref(trace_item))
    open_config = trace_item.split(", ")[1].replace('"', '')
    return open_config


def is_command_prefix(line):
    if line.startswith(f"[Command"):
        return True
    return False

def is_launch(line):
    return "Launch(" in line

def get_launch_assignments(trace_item):
    assert(is_launch(trace_item))
    assignment_suffix = ", ".join(trace_item.split(", ")[1:])
    assignment_string = assignment_suffix[1:-2].split(",")
    assignments = [(x.split("=")) for x in assignment_string]
    return assignments

def get_lauch_name(trace_item):
    assert(is_launch(trace_item))
    launch_name_dirty = trace_item.split("],")[0]
    launch_name = launch_name_dirty.split("Command ")[1]
    return launch_name

## Parse the trace object and gather rw sets for this command
def parse_and_gather_cmd_rw_sets(trace_object) -> Tuple[set, set]:
    previous_trace_line = ""
    read_set = set()
    write_set = []
    dir_set = []
    for line in trace_object:
        line = line.rstrip()
        if is_command_prefix(line):
            relevant_trace_item = remove_command_prefix(line)
            if is_new_path_ref(relevant_trace_item):
                if is_path_ref_read(relevant_trace_item):
                    read_set.add(get_path_ref_name(relevant_trace_item))
                elif is_path_ref_write(relevant_trace_item):
                    write_set.append(get_path_ref_name(relevant_trace_item))
                elif is_path_ref_empty(relevant_trace_item):
                    if is_command_prefix(previous_trace_line):
                        previous_trace_item = remove_command_prefix(previous_trace_line)
                        if is_new_path_ref(previous_trace_item):
                            if is_path_ref_write(previous_trace_item):
                                dir_set.append(f"{get_path_ref_name(relevant_trace_item)}")
                                write_set.pop()
            previous_trace_line = line

    dir_string = ""
    for dir in dir_set:
        dir_string += dir + "/"
        write_set.append(dir_string)
    return read_set, set(write_set)
