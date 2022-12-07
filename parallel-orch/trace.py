import re

# Parse the Riker trace structure
#
# TODOO: This module will need to contain the definition 
# of the trace structure and its methods that we will use to parse it.

## TODO: We should change trace structure to support full command

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

def get_path_ref_name(trace_item):
    assert(is_new_path_ref(trace_item))
    open_config = trace_item.split(", ")[1].replace('"', '')
    return open_config

def is_line_for_commands(cmds, line):
    for cmd in cmds:
        if line.startswith(f"[Command {cmd}]:"):
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

def extract_rw_sets_from_trace(cmd_execution_info, workset, trace):
    # For each command we get read and write initial sets
    # For now this works only for reads
    # Warning! HACK
    for cmd in [remove_command_redir(cmd) for cmd in workset]:
        cmd_execution_info = gather_and_parse_rw(cmd, cmd_execution_info, trace)
    return add_launch_assignments_to_rw_sets(cmd_execution_info, trace)

## Gather and parse the reads and writes for each command
def gather_and_parse_rw(cmd, cmd_execution_info, trace):
    relevant_trace_lines = [line for line in trace
                            if is_line_for_commands([cmd], line)]
    relevant_trace_items = [remove_command_prefix(line) for line in relevant_trace_lines]

    new_path_ref_items = [item for item in relevant_trace_items if is_new_path_ref(item)]

    read_set = [get_path_ref_name(item) for item in new_path_ref_items 
                if is_path_ref_read(item)]
    write_set = [get_path_ref_name(item) for item in new_path_ref_items 
                if is_path_ref_write(item)]
    
    # Update the sets in cmd_execution_info
    cmd_execution_info[cmd].update_read_set(read_set)
    cmd_execution_info[cmd].update_write_set(write_set)
    return cmd_execution_info

## FIXME: Read sets are not generated correctly for nested reads.
##        Find a way to do that correctly.
##        Solution can also apply to non-nested command reads
def add_launch_assignments_to_rw_sets(cmd_execution_info, trace):
    open_refs = {}
    for line in trace:
            if is_new_path_ref(line):
                command_prefix = get_command_prefix(line)
                trace_item = remove_command_prefix(line)
                ref_id = get_path_ref_id(trace_item)
                if command_prefix in open_refs:
                    open_refs[command_prefix][ref_id] = trace_item
                else:
                    open_refs[command_prefix] = {ref_id: trace_item}
            # TODO: handle "No Command" somehow
            elif is_no_command_prefix(line):
                pass
            elif is_launch(line):
                command_prefix = get_command_prefix(line)
                trace_item = remove_command_prefix(line)
                launch_name = get_lauch_name(trace_item)
                launch_assignments = get_launch_assignments(trace_item)
                for lhs, rhs in launch_assignments:
                    if rhs in open_refs[command_prefix]:
                        path_ref = open_refs[command_prefix][rhs]
                        if is_path_ref_read(path_ref):
                            cmd_execution_info[launch_name].add_to_read_set(get_path_ref_name(path_ref))
                        if is_path_ref_write(path_ref):
                            cmd_execution_info[launch_name].add_to_write_set(get_path_ref_name(path_ref))
    return cmd_execution_info