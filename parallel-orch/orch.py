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

## TODO: Make the exec info be a proper class
cmd_exec_info = {cmd : {"R":[], "W":[]} for cmd in cmds_no_redirs}
# print(cmd_exec_info)

## Write a Rikerfile with these commands to execute them
with open("Rikerfile", "w") as f:
    for cmd in cmds_to_run:
        f.write(cmd + " & \n")

## TODO: When running commands make sure to take care of backward dependencies
##       Maybe by blocking write calls and not letting them happen or sth else.

## Call Riker to execute the remaining commands all in parallel
# subprocess.run("rkr --show")

## Call Riker to get the trace
## TODO: Normally we would like to plug in Riker and get the actual Trace data structure
# subprocess.run(f"rkr trace -o {OUTPUT_TRACE_FILE}")

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

def remove_command_prefix(line):
    return line.split(f"[Command {cmd}]: ")[1].rstrip()

def is_new_path_ref(trace_item):
    return "PathRef" in trace_item

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

## Gather and parse the reads and writes for each command
for cmd in cmds_no_redirs:
    print("Working on:", cmd)
    relevant_trace_lines = [line for line in trace
                            if is_line_for_commands([cmd], line)]
    relevant_trace_items = [remove_command_prefix(line) for line in relevant_trace_lines]

    new_path_ref_items = [item for item in relevant_trace_items if is_new_path_ref(item)]
    # pprint(relevant_trace_items)
    # pprint(new_path_ref_items)

    read_set = [get_path_ref_name(item) for item in new_path_ref_items 
                if is_path_ref_read(item)]
    write_set = [get_path_ref_name(item) for item in new_path_ref_items 
                 if is_path_ref_write(item)]
    
    simplified_read_set = [ref_name for ref_name in read_set
                           if ref_name in file_name_pool]
    
    simplified_write_set = [ref_name for ref_name in write_set
                            if ref_name in file_name_pool]
    pprint(f"Read set: {simplified_read_set}")
    pprint(f"Write set: {simplified_write_set}")
    # exit()

pprint(trace)
