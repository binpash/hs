import re
import sys
import os
from typing import Tuple
from enum import Enum
import logging

class Ref(Enum):

    STDIN = sys.stdin
    STDOUT = sys.stdout
    STDERR = sys.stderr
    ROOT = os.path.abspath(os.sep)
    # Maybe Replace instead with this
    CWD = os.getcwd()
    # CWD = "./"


class PathRef:

    def __init__(self, ref, path, permissions):
        self.ref = ref
        self.path = path
        self.is_read, self.is_write = self.resolve_permissions(permissions)

    def resolve_permissions(self, permissions: str):
        if "r" in permissions:
            is_read = True
        else:
            is_read = False
        if "w" in permissions:
            is_write = True
        else:
            is_write = False
        return is_read, is_write
    
    def __str__(self):
        return f"PathRef({self.ref}, {self.path}, {'r' if self.is_read else '-'}{'w' if self.is_write else '-'})"

    def get_resolved_path(self):
        return f"{self.ref}{self.path.lstrip('.')}"

# Parse the Riker trace structure
#
# TODO: This module will need to contain the definition 
# of the trace structure and its methods that we will use to parse it.


def remove_command_redir(cmd):
    return cmd.split(">")[0].rstrip()

def remove_command_prefix(line) -> str:
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
    return trace_item.split(", ")[1].replace('"', '')

def get_path_ref_ref(trace_item):
    assert(is_new_path_ref(trace_item))
    return trace_item.split(", ")[0].split("(")[1]

def is_command_prefix(line):
    if line.startswith(f"[Command"):
        return True
    return False

def is_no_command_prefix(line):
    if line.startswith(f"[No Command"):
        return True
    return False

def is_launch(line):
    return "Launch(" in line

def parse_launch_command(trace_item):
    assert(is_launch(trace_item))
    assignment_suffix = ", ".join(trace_item.split(", ")[1:])
    assignment_string = assignment_suffix[1:-2].split(",")
    assignments = [(x.split("=")) for x in assignment_string]
    return assignments

def parse_launch(trace_item):
    assert(is_launch(trace_item))

def get_lauch_name(trace_item):
    assert(is_launch(trace_item))
    launch_name_dirty = trace_item.split("],")[0]
    launch_name = launch_name_dirty.split("Command ")[1]
    return launch_name   

def get_no_command_ref_id(trace_item):
    return trace_item.split("=")[0].strip()

def get_no_command_ref_ref(trace_item):
    return trace_item.split("=")[1].strip()

def is_prefix_of_cmd(line, prefix):
    if prefix is not None and prefix in get_command_prefix(line):
        return True
    return False

def parse_rw_sets(trace_object):
    refs_dict = {}
    # In the first iteration, we get the refs
    for line in trace_object:
        # This branch will always execute first
        if is_no_command_prefix(line):
            line = remove_command_prefix(line)
            if "=" in line:
                lhs_ref = get_no_command_ref_id(line)
                rhs_ref = get_no_command_ref_ref(line)
                if rhs_ref == "CWD":
                    refs_dict[lhs_ref] = Ref.CWD
                elif rhs_ref == "ROOT":
                    refs_dict[lhs_ref] = Ref.ROOT
                elif rhs_ref == "STDERR":
                    refs_dict[lhs_ref] = Ref.STDERR
                elif rhs_ref == "STDIN":
                    refs_dict[lhs_ref] = Ref.STDIN
                elif rhs_ref == "STDOUT":
                    refs_dict[lhs_ref] = Ref.STDOUT
        # Parses launch assignments
        elif is_launch(line):
            assignments = parse_launch_command(remove_command_prefix(line))
            for assignment in assignments:
                refs_dict[assignment[0].strip()] = refs_dict[assignment[1].strip()]
        # Parses pathrefs
        elif is_new_path_ref(line):
            line = remove_command_prefix(line).strip()
            lhs_ref = get_path_ref_id(line).strip()
            ref = get_path_ref_ref(line).strip()
            name = get_path_ref_name(line).strip()
            open_config = get_path_ref_open_config(line).strip()
            path_ref = PathRef(ref, name, open_config)
            refs_dict[lhs_ref] = path_ref
    return refs_dict


def traverse_path_ref(refs_dict: dict, ref: PathRef):
    if isinstance(refs_dict[ref.ref], PathRef):
        return traverse_path_ref(refs_dict, refs_dict[ref.ref])
    else:
        return ref.ref


def replace_path_ref_terminal_nodes(refs_dict: dict):
    for ref in refs_dict.values():
        if isinstance(ref, PathRef):
            assert (isinstance(refs_dict[ref.ref], Ref))
            ref.ref = refs_dict[ref.ref].value
    

def resolve_rw_set_refs(refs_dict):
    for ref_id, ref in refs_dict.items():
        if isinstance(ref, PathRef):
            refs_dict[ref_id].ref = traverse_path_ref(refs_dict, ref)
    return refs_dict

## Parse the trace object and gather rw sets for this command
def parse_and_gather_cmd_rw_sets(trace_object) -> Tuple[set, set]:
    refs_dict = parse_rw_sets(trace_object)
    resolved_dict = resolve_rw_set_refs(refs_dict)
    replace_path_ref_terminal_nodes(resolved_dict)
    
    previous_trace_line = ""
    read_set = set()
    write_set = []
    dir_set = []
    for k, v in resolved_dict.items():
        try:
            logging.debug(f'{k}: {v.get_resolved_path()}')
        except:
            logging.debug(f'{k}: {v}')
    # for trace_item in trace_dict.items()
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
