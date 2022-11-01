from pprint import pprint
import subprocess
import re

OUTPUT_TRACE_FILE="rkr-trace.txt"
cmds_to_run = [
    "grep foo in1 > out1",
    "grep foo out1 > out11",
    "grep foo out11 > out111"
]

# TODO: Currently cmd_execution_info does not create correct r/w sets for
#       commands with same first part but different redir.
#       Trace file also ignores redir.
#       Maybe convert cmd_execution_info to multiple value dictionary 
#       and also keep ref number for each command

## Just work with files in this pool for now
## TODO: Extend to work with all file references
file_name_pool = ["in1", "out1", "out11", "out111", "in3", "in33", "out33", "out333"]


def cmd_execution_info_simplified(cmd_execution_info):
    for cmd in cmd_execution_info.values():
        cmd.print_simplified()

## Write a Rikerfile with these commands to execute them
def write_cmds_to_rikerfile(cmds_to_run):
    with open("Rikerfile", "w") as f:
        for cmd in cmds_to_run:
            f.write(cmd + " & \n")

## Read trace and capture each command
def read_rkr_trace():
    with open(OUTPUT_TRACE_FILE) as f:
        return f.readlines()

def is_line_for_commands(cmds, line):
    for cmd in cmds:
        if line.startswith(f"[Command {cmd}]:"):
            return True
    return False

class Cmd_exec_info:

    id_counter = 0

    def __init__(self, cmd):
        self.cmd = cmd
        self.cmd_no_redir = remove_command_redir(cmd)
        self.read_set = {}
        self.write_set = {}
        self.id = Cmd_exec_info.id_counter
        Cmd_exec_info.id_counter += 1


    def __str__(self):
        return f"Cmd: {self.cmd}\nRead set: {self.read_set}\nWrite set: {self.write_set}"

    def update_read_set(self, read_set):
        self.read_set = set(read_set)

    def add_to_read_set(self, ref):
        self.read_set.add(ref)

    def update_write_set(self, write_set):
        self.write_set = set(write_set)
    
    def add_to_write_set(self, ref):
        self.write_set.add(ref)

    def print_simplified(self):
        print("ID:", self.id)
        print("Cmd:", self.cmd)
        print("Simplified read set:", [ref_name for ref_name in self.read_set
                                                if ref_name in file_name_pool])
        print("Simplified write set:", [ref_name for ref_name in self.write_set
                                                if ref_name in file_name_pool])
        print()

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

def has_forward_dependency(cmd_execution_info, first, second):
    first_write_set = cmd_execution_info[first].write_set
    second_read_set = cmd_execution_info[second].read_set
    # We want the write set of the first command to not have 
    # common elements with the second command,
    # otherwise the second is forward-dependent
    return not first_write_set.isdisjoint(second_read_set)

## Resolve all the forward dependencies and update the workset
## Forward dependency is when a command's output is the same
## as the input of a following command
def check_forward_depepndencies(cmd_execution_info, workset):
    new_workset = []
    for i, cmd in enumerate(workset):
        for dependent_cmd in workset[i+1:]:
            if (dependent_cmd not in new_workset) and \
               (has_forward_dependency(cmd_execution_info, cmd, dependent_cmd)):
                new_workset.append(dependent_cmd)
    return new_workset

def workset_cmds_to_list(cmd_execution_info):
    cmds_to_run = []
    for cmd in cmd_execution_info.values():
        cmds_to_run.append(cmd.cmd)
    return cmds_to_run

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
def update_rw_sets(cmd_execution_info, trace):
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

def run_and_trace_workset(cmds_to_run):
    print("=" * 60)
    write_cmds_to_rikerfile(cmds_to_run)
    ## Call Riker to execute the remaining commands all in parallel
    subprocess.run(["rkr", "--show"])
    ## Call Riker to get the trace
    ## TODO: Normally we would like to plug in Riker and get the actual Trace data structure
    subprocess.run(["rkr", "trace", "-o", OUTPUT_TRACE_FILE])
    trace = read_rkr_trace()
    return trace

def find_rw_dependencies_based_on_trace(cmd_execution_info, cmds_to_run):
    trace = run_and_trace_workset(cmds_to_run)
    # For each command we get read and write initial sets
    # For now this works only for reads
    # Warning! HACK
    for cmd in [remove_command_redir(cmd) for cmd in cmds_to_run]:
        cmd_execution_info = gather_and_parse_rw(cmd, cmd_execution_info, trace)
    return update_rw_sets(cmd_execution_info, trace)

def scheduling_algorithm(cmds_to_run):
    ## create initial Cmd_exec_info objects for each parsed cmd
    ## TODO: this implementation does not allow duplicate commands in the workset, change it.
    cmd_execution_info = {remove_command_redir(cmd): Cmd_exec_info(cmd) for cmd in cmds_to_run}
    workset = list(cmd_execution_info.keys())
    ## TODO: When running commands make sure to take care of backward dependencies
    ##       Maybe by blocking write calls and not letting them happen or sth else.

    ## Parse trace
    ## TODO: This will change when we actually hook up with riker
    while len(workset) > 0:
        ## In every loop iteration we are guaranteed to decrease the workset by 1, 
        ## since the first command will not need to reexecute 
        ## TODO: Also need to deal with backward dependencies for the above to be absolutely true.
        cmd_execution_info = find_rw_dependencies_based_on_trace(cmd_execution_info, cmds_to_run)
        # cmd_execution_info_simplified(cmd_execution_info)
        # Check forward dependencies and update workset accordingly
        workset = check_forward_depepndencies(cmd_execution_info, workset)
        cmd_execution_info_simplified(cmd_execution_info)
        cmds_to_run = workset_cmds_to_list(cmd_execution_info)
        print(cmds_to_run)

scheduling_algorithm(cmds_to_run)
