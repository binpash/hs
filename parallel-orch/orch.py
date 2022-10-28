from pprint import pprint
import subprocess
import re

OUTPUT_TRACE_FILE="rkr-trace.txt"

cmds_to_run = [
    "grep foo in1 > out1",
    "grep foo out1 > out11",
    "grep foo out11 > out111",
]

## Just work with files in this pool for now
## TODO: Extend to work with all file references
file_name_pool = ["in1", "out1", "out11", "out111"]


cmds_no_redirs = [cmd.split(">")[0].rstrip() for cmd in cmds_to_run]
# print(cmds_no_redirs)


class Cmd_exec_info:

    def __init__(self, cmd):
        self.cmd = cmd
        self.read_set = {}
        self.write_set = {}

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
        print("Cmd:", self.cmd)
        print("Simplified read set:", [ref_name for ref_name in self.read_set
                                                if ref_name in file_name_pool])
        print("Simplified write set:", [ref_name for ref_name in self.write_set
                                                if ref_name in file_name_pool])


# create Cmd_exec_info objects for each parsed cmd
cmd_exec_info = {cmd : Cmd_exec_info(cmd) for cmd in cmds_no_redirs}

## Write a Rikerfile with these commands to execute them
with open("Rikerfile", "w") as f:
    for cmd in cmds_to_run:
        f.write(cmd + " & \n")

## TODO: When running commands make sure to take care of backward dependencies
##       Maybe by blocking write calls and not letting them happen or sth else.

## Call Riker to execute the remaining commands all in parallel
subprocess.run(["rkr", "--show"])

## Call Riker to get the trace
## TODO: Normally we would like to plug in Riker and get the actual Trace data structure
subprocess.run(["rkr", "trace", "-o", OUTPUT_TRACE_FILE])

## Read trace and capture each command
with open(OUTPUT_TRACE_FILE) as f:
    trace = f.readlines()

## Parse trace
## TODO: This will change when we actually hook up with riker

def is_line_for_commands(cmds, line):
    for cmd in cmds:
        if line.startswith(f"[Command {cmd}]:"):
            return True
    return False


filtered_trace = [line for line in trace
                  if is_line_for_commands(cmds_no_redirs, line)]

# def remove_command_prefix(line):
#     return line.split(f"[Command {cmd}]: ")[1].rstrip()

def remove_command_prefix(line):
    return line.split(f"]: ")[1].rstrip()

def is_new_path_ref(trace_item):
    return "PathRef" in trace_item

def get_path_ref_id(trace_item):
    return trace_item.split("=")[0].strip()

def get_path_ref_open_config(trace_item):
    assert(is_new_path_ref(trace_item))
    ## WARNING: HACK
    
    open_config_suffix = trace_item.split(", ")[2]
    open_config = re.split('\(|\)', open_config_suffix)[0].rstrip()
    # print(open_config_suffix)
    # print(open_config)
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
    # print(open_config)
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

def check_if_forward_dependent(first, second):
    for write_file in first.write_set:
        if write_file in second.read_set:
            print(f"> {second} depends on {first} through file: {write_file}")

def check_deps(workset):
    new_workset = {}
    for i, cmd in enumerate(workset.values()): 
        print("Examining:", i, cmd)
        for dependent_cmd in list(workset.values())[i+1:]:
            check_if_forward_dependent(cmd, dependent_cmd)
            new_workset[dependent_cmd.cmd] = dependent_cmd
    return new_workset


## Gather and parse the reads and writes for each command
def gather_and_parse_rw(cmd):
    print("Working on:", cmd)
    relevant_trace_lines = [line for line in trace
                            if is_line_for_commands([cmd], line)]
    relevant_trace_items = [remove_command_prefix(line) for line in relevant_trace_lines]

    new_path_ref_items = [item for item in relevant_trace_items if is_new_path_ref(item)]

    read_set = [get_path_ref_name(item) for item in new_path_ref_items 
                if is_path_ref_read(item)]
    write_set = [get_path_ref_name(item) for item in new_path_ref_items 
                if is_path_ref_write(item)]
    
    # Update the sets in cmd_exec_info
    cmd_exec_info[cmd].update_read_set(read_set)
    cmd_exec_info[cmd].update_write_set(write_set)



for cmd in cmds_no_redirs:
       gather_and_parse_rw(cmd) 

for cmd in cmd_exec_info.values():
    print(cmd)


open_refs = {}
for line in trace:
    if is_new_path_ref(line):
        trace_item = remove_command_prefix(line)
        ref_id = get_path_ref_id(trace_item)
        open_refs[ref_id] = trace_item
    elif is_launch(line):
        print(line)
        # pprint(open_refs)
        trace_item = remove_command_prefix(line)
        launch_name = get_lauch_name(trace_item)
        launch_assignments = get_launch_assignments(trace_item)
        for lhs, rhs in launch_assignments:
            if rhs in open_refs:
                path_ref = open_refs[rhs]
                if is_path_ref_read(path_ref):
                    print(rhs)
                    # Find that command in read sets and then the file in them
                    cmd_exec_info[launch_name].add_to_read_set(get_path_ref_name(path_ref))
                if is_path_ref_write(path_ref):
                    print(rhs)
                    # Find that command in write sets and then the file in them
                    cmd_exec_info[launch_name].add_to_write_set(get_path_ref_name(path_ref))



for cmd in cmd_exec_info.values():
    cmd.print_simplified()




for cmd in check_deps(cmd_exec_info).values():
    cmd.print_simplified()

