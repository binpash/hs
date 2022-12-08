#!/bin/env python3

from argparse import ArgumentParser
import sys
import logging
import executor
import trace

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
        self.cmd_no_redir = trace.remove_command_redir(cmd)
        self.read_set = {}
        self.write_set = {}
        self.id = Cmd_exec_info.id_counter
        self.commited = False
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
        logging.debug(f"COMMITED:{self.commited}\n")


## Currently this abstracts a list of cmds
##
## In the future we will modify it to be a partial order
class Workset:
    def __init__(self, list_of_cmds):
        self.list_of_cmds = list_of_cmds

    def __len__(self):
        return len(self.list_of_cmds)

    def __iter__(self):
        return iter(self.list_of_cmds)

    def get_first(self):
        return self.list_of_cmds[0]

    def get_rest(self):
        return self.list_of_cmds[1:]    

    def insert_at_end(self, cmd_id):
        self.list_of_cmds.append(cmd_id)

    def get_all_enumerate(self):
        return enumerate(self.list_of_cmds)

    ## Needs to be called after get_all_enumerate
    def get_suffix(self, i):
        return self.list_of_cmds[i+1:]

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

def extract_rw_sets_from_trace(cmd_execution_info, workset, trace_object):
    # For each command we get read and write initial sets
    # For now this works only for reads
    # Warning! HACK
    for cmd in [trace.remove_command_redir(cmd) for cmd in workset]:
        cmd_execution_info = gather_and_parse_rw(cmd, cmd_execution_info, trace_object)
    return add_launch_assignments_to_rw_sets(cmd_execution_info, trace_object)

## Gather and parse the reads and writes for each command
def gather_and_parse_rw(cmd, cmd_execution_info, trace_object):
    ## Parse the trace object and gather rw sets for this command
    read_set, write_set = trace.parse_and_gather_cmd_rw_sets(cmd, trace_object)
    
    # Update the sets in cmd_execution_info
    cmd_execution_info[cmd].update_read_set(read_set)
    cmd_execution_info[cmd].update_write_set(write_set)
    return cmd_execution_info

## FIXME: Read sets are not generated correctly for nested reads.
##        Find a way to do that correctly.
##        Solution can also apply to non-nested command reads
def add_launch_assignments_to_rw_sets(cmd_execution_info, trace_object):
    open_refs = {}
    for line in trace_object:
            if trace.is_new_path_ref(line):
                command_prefix = trace.get_command_prefix(line)
                trace_item = trace.remove_command_prefix(line)
                ref_id = trace.get_path_ref_id(trace_item)
                if command_prefix in open_refs:
                    open_refs[command_prefix][ref_id] = trace_item
                else:
                    open_refs[command_prefix] = {ref_id: trace_item}
            # TODO: handle "No Command" somehow
            elif trace.is_no_command_prefix(line):
                pass
            elif trace.is_launch(line):
                command_prefix = trace.get_command_prefix(line)
                trace_item = trace.remove_command_prefix(line)
                launch_name = trace.get_lauch_name(trace_item)
                launch_assignments = trace.get_launch_assignments(trace_item)
                for lhs, rhs in launch_assignments:
                    if rhs in open_refs[command_prefix]:
                        path_ref = open_refs[command_prefix][rhs]
                        if trace.is_path_ref_read(path_ref):
                            cmd_execution_info[launch_name].add_to_read_set(trace.get_path_ref_name(path_ref))
                        if trace.is_path_ref_write(path_ref):
                            cmd_execution_info[launch_name].add_to_write_set(trace.get_path_ref_name(path_ref))
    return cmd_execution_info



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
    new_workset = Workset([])    
    for i, cmd_id in workset.get_all_enumerate():
        for dependent_cmd_id in workset.get_suffix(i):
            # TODO: Optimization, maybe we could not run 
            # Configurable 
            # Priorities
            if dependent_cmd_id not in new_workset and \
               has_forward_dependency(cmd_execution_info, cmd_id, dependent_cmd_id):
                new_workset.insert_at_end(dependent_cmd_id)
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
    return {trace.remove_command_redir(cmd_obj.cmd): cmd_obj for cmd_obj in cmd_execution_info.values()}

def convert_cmd_exec_info_cmd_based_to_id_based_dict(cmd_execution_info_cmd_based_key):
    return {cmd_obj.id: cmd_obj for cmd_obj in cmd_execution_info_cmd_based_key.values()}

def execute_workset_and_find_rw_dependencies(cmd_execution_info, workset):
    ## Warning! HACK: Remove these functions in later iteration
    ##                cmd_execution_info is converted to cmd-based dict (instead of id)
    cmd_exec_info_cmd_based_dict = convert_cmd_exec_info_to_cmd_based_dict(cmd_execution_info)
    

    trace_objects = run_and_trace_workset(workset, cmd_execution_info)

    ## TODO: Fix the rest of code to work with a trace dictionary 
    ##         from command ids to trace objects

    ## HACK: Just to make tests run for now we concatenate all traces into a big trace
    ##       to just run tests and code as it was.
    trace_object =  []
    for _, trace_obj in trace_objects.items():
        trace_object += trace_obj

    ## HACK: Convert workset from id list to cmd list. Same as above
    cmd_workset = [cmd_execution_info[cmd_id].cmd for cmd_id in workset]
    # Changes are made on the cmd-based structures
    cmd_exec_info_cmd_based_dict = extract_rw_sets_from_trace(cmd_exec_info_cmd_based_dict, cmd_workset, trace_object)
    ## HACK: Remove in later iteration 
    ## above conversion is reverted back to id based
    return convert_cmd_exec_info_cmd_based_to_id_based_dict(cmd_exec_info_cmd_based_dict)

## TODO: In order to be able to combine forward and backward dependencies
##       we need to execute all except the first cmd in a sandbox (and riker in the sandbox)
##       
##       We need to change this function to write the first cmd in a rikerfile
##       and then iterate on all others, run them in a sandbox and then put
##       them in a rikerfile there, and run them there.
##       
##       It is likely that this then requires work on the traces, modifying them
##       to be correct for the orch.
##
##       The other big thing is to then decide whether to commit each of the sandboxes
##       or not. If there is ANY dependency we want to not commit the sandbox.
##
##       NOTE: There are two different types of commits, the sandbox commit,
##             which just means execute the command and see its effects,
##             and the orchestrator commit, which means that this command
##             has completed and will never run again (and all its prefix has also completed).
def run_and_trace_workset(workset, cmd_execution_info):
    trace_objects = {}

    ## Get the first command in the workset and run it just with riker
    first_cmd_id = workset.get_first()
    first_cmd = cmd_execution_info[first_cmd_id].cmd

    ## TODO: Run this on the side, asynchronously and keep going, similarly to &
    trace_object = executor.run_and_trace_command(first_cmd, OUTPUT_TRACE_FILE)
    trace_objects[first_cmd_id] = trace_object

    for cmd_id in workset.get_rest():
        cmd = cmd_execution_info[cmd_id].cmd
        trace_object = executor.run_and_trace_command_in_sandbox(cmd, OUTPUT_TRACE_FILE)
        trace_objects[cmd_id] = trace_object

    ## Returns a dictionary of traces, one for each command id
    return trace_objects

def scheduling_algorithm(cmds_to_run):
    ## create initial Cmd_exec_info objects for each parsed cmd
    ## TODO: this implementation does not allow duplicate commands in the workset, change it.
    cmd_execution_info = generate_cmd_execution_info(cmds_to_run)
    ## We also need a dictionary that points from a command to this command's id
    ## For now we don't need this
    # cmd_to_id = generate_cmd_to_id(cmd_execution_info)

    # The workset contains all the command ids that are going to be traced in the current cycle
    workset = Workset([cmd.id for cmd in cmd_execution_info.values()])
    # Count tracing cycles
    reps = 1
    ## Parse trace
    ## TODO: This will change when we actually hook up with riker
    while len(workset) > 0:
        log_run_and_workset_info(reps, workset)
        ## In every loop iteration we are guaranteed to decrease the workset by 1, 
        ## since the first command will not need to re-execute 
        cmd_execution_info = execute_workset_and_find_rw_dependencies(cmd_execution_info, workset)
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
