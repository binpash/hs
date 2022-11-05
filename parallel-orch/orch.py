#!/bin/env python3

from argparse import ArgumentParser
import sys
import logging
from tracer import *
from trace import *

# TODO: Currently cmd_execution_info does not create correct r/w sets for
#       commands with same first part but different redir.
#       Trace file also ignores redir.
#       Maybe convert cmd_execution_info to multiple value dictionary 
#       and also keep ref number for each command

def parse_args(args=sys.argv[1:]):
    parser = ArgumentParser(description='Dynamic parallelizer scheduler')
    parser.add_argument("input_file", 
                        help="Path of the file that contains the commands to schedule")
    parser.add_argument("-t", "--riker_trace_file", 
                        default="rkr-trace.txt", 
                        help="the name of the riker trace file")
    # TODO: Extend to work with all file references
    parser.add_argument("-s", "--simple_print",
                        help="Print only r/w set filenames")
    parser.add_argument("-d", "--debug-level", 
                        type=int, 
                        default=0,
                        help="Set debugging level")
    return parser.parse_args(args)

def parse_input(input_file):
    with open(input_file, "r") as f:
        return f.read().splitlines()

def cmd_execution_info_simplified(cmd_execution_info):
    for cmd in cmd_execution_info.values():
        cmd.log_simplified()

def log_run_and_workset_info(reps, workset):
    logging.debug(f"=" * 60)
    logging.debug(f"RUN:{reps}")
    logging.debug(f"WORKSET:{workset}")
    logging.debug(f"=" * 60)

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

    def log_simplified(self):
        logging.debug(f"ID:{self.id}")
        logging.debug(f"CMD:{self.cmd}")
        logging.debug(f"R:{[ref_name for ref_name in self.read_set if ref_name in file_name_pool]}")
        logging.debug(f"W:{[ref_name for ref_name in self.write_set if ref_name in file_name_pool]}")

## cmd_execution_info is a dictionary containing information about each command.
## id : Cmd_exec_info (id, command, read set, write set, is commited)
def generate_cmd_execution_info(cmds_to_run):
    cmds_exec_info_format = [Cmd_exec_info(cmd) for cmd in cmds_to_run]
    return {cmd.id: cmd for cmd in cmds_exec_info_format}

## cmd_to_id is a dictionary that maps full commands to their ids.
## command : id
def generate_cmd_to_id(cmd_exec_info):
    cmd_to_id = {}
    for cmd in cmd_exec_info.values():
        cmd_to_id[cmd.cmd] = cmd.id
    return cmd_to_id

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
def check_forward_dependencies(cmd_execution_info, workset):
    new_workset = []    
    for i, cmd_id in enumerate(workset):
        for dependent_cmd_id in workset[i+1:]:
            # TODO: Optimization, maybe we could not run 
            # Configurable 
            # Priorities
            if dependent_cmd_id not in new_workset and \
               has_forward_dependency(cmd_execution_info, cmd_id, dependent_cmd_id):
                new_workset.append(dependent_cmd_id)
    return new_workset

def workset_cmds_to_list(cmd_execution_info):
    cmds_to_run = []
    for cmd in cmd_execution_info.values():
        cmds_to_run.append(cmd.cmd)
    return cmds_to_run

## Warning! HACK: Get rid of these functions on a later iteration.
## TODO: We should maybe use a more efficient way 
##       to pass the cmd_exec_info structure to trace      
def convert_cmd_exec_info_to_cmd_based_dict(cmd_execution_info):
    return {remove_command_redir(cmd_obj.cmd): cmd_obj for cmd_obj in cmd_execution_info.values()}

def convert_cmd_exec_info_cmd_based_to_id_based_dict(cmd_execution_info_cmd_based_key):
    return {cmd_obj.id: cmd_obj for cmd_obj in cmd_execution_info_cmd_based_key.values()}

def find_rw_dependencies_based_on_trace(cmd_exec_info_cmd_based_dict, cmd_execution_info, workset):
    ## HACK: Remove in later iteration 
    cmd_workset = [cmd_execution_info[cmd_id].cmd for cmd_id in workset]
    trace = run_and_trace_workset(cmd_workset, OUTPUT_TRACE_FILE)
    return extract_rw_sets_from_trace(cmd_exec_info_cmd_based_dict, cmd_workset, trace)

def scheduling_algorithm(cmds_to_run):
    ## create initial Cmd_exec_info objects for each parsed cmd
    ## TODO: this implementation does not allow duplicate commands in the workset, change it.
    cmd_execution_info = generate_cmd_execution_info(cmds_to_run)
    # We also need a dictionary that points from a command to this command's id
    cmd_to_id = generate_cmd_to_id(cmd_execution_info)
    # The workset contains all the command ids that are going to be traced in the current cycle
    workset = [cmd.id for cmd in cmd_execution_info.values()]
    # Count tracing cycles
    reps = 1
    ## Parse trace
    ## TODO: This will change when we actually hook up with riker
    while len(workset) > 0:
        log_run_and_workset_info(reps, workset)
        ## In every loop iteration we are guaranteed to decrease the workset by 1, 
        ## since the first command will not need to reexecute 
        ## TODO: Also need to deal with backward dependencies for the above to be absolutely true.
        ## Warning! HACK: Remove these functions in later iteration
        cmd_exec_info_cmd_based_dict = convert_cmd_exec_info_to_cmd_based_dict(cmd_execution_info)
        cmd_exec_info_cmd_based_dict = find_rw_dependencies_based_on_trace(cmd_exec_info_cmd_based_dict, cmd_execution_info, workset)
        cmd_execution_info_simplified(cmd_exec_info_cmd_based_dict)
        cmd_execution_info = convert_cmd_exec_info_cmd_based_to_id_based_dict(cmd_exec_info_cmd_based_dict)
        cmd_execution_info_simplified(cmd_execution_info)
        # Check forward dependencies and update workset accordingly
        workset = check_forward_dependencies(cmd_execution_info, workset)
        reps += 1

def main():
    cmds_to_run = parse_input(args.input_file)
    scheduling_algorithm(cmds_to_run)


logging.basicConfig(level=logging.WARNING, format="%(levelname)s:%(message)s")

## Just work with files in this pool for now
## TODO: Extend to work with all file references
file_name_pool = ["./output_orch/in1", "./output_orch/in2", "./output_orch/in3", 
                  "./output_orch/in4", "./output_orch/in5", "./output_orch/in6" ,
                  "./output_orch/out1", "./output_orch/out2", "./output_orch/out3", 
                  "./output_orch/out4", "./output_orch/out5", "./output_orch/out6"]

args = parse_args()

OUTPUT_TRACE_FILE = args.riker_trace_file

if args.debug_level == 1:
    logging.getLogger().setLevel(logging.INFO)
elif args.debug_level >= 2:
    logging.getLogger().setLevel(logging.DEBUG)


if __name__ == "__main__":
    main()
