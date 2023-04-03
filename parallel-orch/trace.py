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
    # Not sure this is always correct
    # but it doesn't affect the results
    CWD = os.getcwd()


class PathRef:

    def __init__(self, ref, path, permissions, no_follow):
        self.ref = ref
        self.path = path
        self.is_read, self.is_write, self.is_exec = self.resolve_permissions(permissions)
        self.is_nofollow = no_follow

    def resolve_permissions(self, permissions: str):
        if "r" in permissions:
            is_read = True
        else:
            is_read = False
        if "w" in permissions:
            is_write = True
        else:
            is_write = False
        if "x" in permissions:
            is_exec = True
        else:
            is_exec = False
        return is_read, is_write, is_exec
    
    def __str__(self):
        return f"PathRef({self.ref}, {self.path}, {'r' if self.is_read else '-'}{'w' if self.is_write else '-'}{'x' if self.is_exec else '-'} {'no follow' if self.is_nofollow else ''})"

    def get_resolved_path(self):
        # Remove dupliate prefixes
        if not self.path.startswith("/"):
            modified_path = "/" + self.path
        else:
            modified_path = self.path
    
        commonprefix = os.path.commonprefix([self.ref, modified_path])
        ref_without_prefix = self.ref.replace(commonprefix, "", 1)        
        path_without_prefix = modified_path.replace(commonprefix, "", 1)

        if path_without_prefix.startswith("/"):
            path_without_prefix = path_without_prefix.replace("/", "", 1)

        return os.path.join(commonprefix, ref_without_prefix, path_without_prefix).replace("/./", "/")



def log_resolved_trace_items(resolved_dict):
    for k, v in resolved_dict.items():
        try:
            logging.debug(f" {k}: {v}")
        except:
            logging.debug(f'{k}: {v}')

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

    open_config = re.split('\(|\)', open_config_suffix)[0]
    # WARNING: HACK: hard-coded replacement 
    open_config = open_config.replace("truncate create", "").rstrip()
    return open_config

def get_path_ref_no_follow(trace_item):
    return "nofollow" in trace_item

def is_path_ref_read(trace_item: PathRef):
    return trace_item.is_read
        
def is_path_ref_write(trace_item: PathRef):
    return trace_item.is_write

def is_path_ref_execute(trace_item: PathRef):
    return trace_item.is_write

def is_path_ref_empty(trace_item: PathRef):
    return not trace_item.is_read and not trace_item.is_write and not trace_item.is_exec

def get_path_ref_name(trace_item):
    assert(is_new_path_ref(trace_item))
    return trace_item.split(", ")[1].replace('"', '')

def get_path_ref_ref(trace_item):
    assert(is_new_path_ref(trace_item))
    return trace_item.split(", ")[0].split("(")[1]

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
            if " = " in line:
                lhs_ref = int(get_no_command_ref_id(line).strip().lstrip("r"))
                rhs_ref = get_no_command_ref_ref(line).strip().lstrip("r")
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
                if int(assignment[1].strip().lstrip("r")) in refs_dict:
                    refs_dict[int(assignment[0].strip().lstrip("r"))] = refs_dict[int(assignment[1].strip().lstrip("r"))]
        # Parses pathrefs
        elif is_new_path_ref(line):
            line = remove_command_prefix(line).strip()
            lhs_ref = int(get_path_ref_id(line).strip().lstrip("r"))
            ref = int(get_path_ref_ref(line).strip().lstrip("r"))
            name = get_path_ref_name(line).strip()
            open_config = get_path_ref_open_config(line).strip()
            no_follow = get_path_ref_no_follow(line)
            path_ref = PathRef(ref, name, open_config, no_follow)
            refs_dict[lhs_ref] = path_ref
    return refs_dict
    
def traverse_path_ref(refs_dict: dict, ref: PathRef):
    if isinstance(ref, PathRef) and not ref.is_nofollow and isinstance(refs_dict[ref.ref], PathRef):
        return traverse_path_ref(refs_dict, refs_dict[ref.ref])
    else:
        return ref.ref

def resolve_rw_set_refs(refs_dict):
    for ref_id, ref in refs_dict.items():
        if isinstance(ref, PathRef):
            refs_dict[ref_id].ref = traverse_path_ref(refs_dict, ref)
    return refs_dict

def replace_path_ref_terminal_nodes(refs_dict: dict):
    for ref in refs_dict.values():
        if isinstance(ref, PathRef) and not ref.is_nofollow:
            # HACK: This is hard-coded stdout
            if ref.ref not in refs_dict:
                ref.ref = refs_dict[4].value
            else:
                if isinstance(refs_dict[ref.ref], Ref):
                    ref.ref = refs_dict[ref.ref].value
                else:
                    logging.debug(ref)
                    logging.debug("------------------------------")
                    ref.ref = os.getcwd()

## Parse the trace object and gather rw sets for this command
def parse_and_gather_cmd_rw_sets(trace_object) -> Tuple[set, set]:
    refs_dict = parse_rw_sets(trace_object)
    resolved_dict = resolve_rw_set_refs(refs_dict)
    replace_path_ref_terminal_nodes(resolved_dict)
    # log_resolved_trace_items(resolved_dict)

    read_set = set()
    write_set = []
    dir_set = []
    for i in range(len(resolved_dict)):
        if i not in resolved_dict:
            continue
        resolved_trace_object = resolved_dict[i]
        # We ignore Ref objects
        if isinstance(resolved_trace_object, Ref):
            continue
        if is_path_ref_read(resolved_trace_object):
            read_set.add(resolved_trace_object.get_resolved_path())
        if is_path_ref_write(resolved_trace_object):
            write_set.append(resolved_trace_object.get_resolved_path())
        # This is a sign that a directory declaration might exist
        if is_path_ref_empty(resolved_trace_object):
            if i > 0:
                if i - 1 in resolved_dict:
                    previous_resolved_trace_object = resolved_dict[i-1]
                    if isinstance(previous_resolved_trace_object, PathRef) and is_path_ref_write(previous_resolved_trace_object):
                        dir_set.append(resolved_trace_object.get_resolved_path())
                        write_set.pop()

    prefix = os.path.commonprefix(dir_set)
    suffixes = [dir.replace(prefix, "") for dir in dir_set]
    # Warning: HACK
    dir_string = prefix
    for dir in suffixes:
        dir_string = os.path.join(dir_string, dir)
        to_add = os.path.join(prefix, dir_string)
        if to_add.endswith("/"):
            write_set.append(to_add)
        else:
            write_set.append(to_add + "/")
    return read_set, set(write_set)

def parse_exit_code(trace_object) -> int:
    for line in reversed(trace_object):
        if "Exit(" in line:
            return int(line.split("Exit(")[1].rstrip(")\n"))
