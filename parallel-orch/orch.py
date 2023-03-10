#!/bin/env python3

from argparse import ArgumentParser
from partial_program_order import Node, PartialProgramOrder, RWSet
import sys
import logging
import executor
import trace
import util

## TODO: For much later, ignore for now. We can discover W-R dependencies and stream their outputs
##       instead of just waiting for execution to complete.

# TODO: Currently cmd_execution_info does not create correct r/w sets for
#       commands with same first part but different redir.
#       Trace file also ignores redir.
#       Maybe convert cmd_execution_info to multiple value dictionary 
#       and also keep ref number for each command

def log_partial_program_order_graph(partial_program_order):
    logging.debug(f"=" * 18 + "|PARTIAL PROGRAM ORDER|" + "=" * 19)
    logging.debug(f"{partial_program_order}")
    logging.debug(f"=" * 60)

def parse_args(args=sys.argv[1:]):
    parser = ArgumentParser(description='Dynamic parallelizer scheduler')
    parser.add_argument("input_file", 
                        help="Path of the file that contains the commands to schedule")
    parser.add_argument("-t", "--riker_trace_file", 
                        default="rkr-trace.txt", 
                        help="the name of the riker trace file")
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
    
def generate_partial_program_order(input_cmds_to_run):
    # TODO: In the next iteration indexes will be given to us
    nodes = {i: Node(i, cmd) for i, cmd in enumerate(input_cmds_to_run)}
    edges = {}
    for i in range(1, len(input_cmds_to_run)):
        edges[i-1] = [i]
    edges[len(input_cmds_to_run) - 1] = []
    return PartialProgramOrder(nodes, edges)

def cmd_execution_info_simplified(cmd_execution_info):
    for cmd in cmd_execution_info.values():
        cmd.log_simplified()

def log_run_and_workset_info(partial_program_order, reps):
    logging.debug(f"=" * 60)
    logging.debug(f"RUN:{reps}")
    logging.debug(f"WORKSET:{partial_program_order.get_workset()}")
    logging.debug(f"COMMITTED:{partial_program_order.get_committed()}")
    logging.debug(f"FRONTIER:{partial_program_order.get_frontier()}")
    logging.debug(f"SPECULATED:{partial_program_order.get_speculated()}")
    logging.debug(f"=" * 60)


## cmd_to_id is a dictionary that maps full commands to their ids.
## command : id
def generate_cmd_to_id(cmd_exec_info):
    cmd_to_id = {}
    for cmd in cmd_exec_info.values():
        cmd_to_id[cmd.cmd] = cmd.id
    return cmd_to_id

def extract_rw_sets_from_traces(partial_program_order, trace_objects: dict):
    for node_id in partial_program_order.get_workset():
        trace_object = trace_objects[node_id]
        rw_set = gather_and_parse_rw(trace_object)
        partial_program_order.update_rw_set(node_id, rw_set)

## Gather and parse the reads and writes for each command
def gather_and_parse_rw(trace_object) -> RWSet:
    ## Parse the trace object and gather rw sets for this command
    read_set, write_set = trace.parse_and_gather_cmd_rw_sets(trace_object)
    return RWSet(read_set, write_set)

## FIXME: Read sets are not generated correctly for nested reads.
##        Find a way to do that correctly.
##        Solution can also apply to non-nested command reads
def add_launch_assignments_to_rw_sets(partial_program_order, trace_object):
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
                            # cmd_execution_info[launch_name].add_to_read_set(trace.get_path_ref_name(path_ref))
                            # TODO: HACK normally we should never find an id from a command name,
                            # and we should trace based on cmd_id
                            node_id = partial_program_order.get_node_id_from_cmd_no_redir(launch_name)
                            partial_program_order.add_to_read_set(node_id, trace.get_path_ref_name(path_ref))
                        if trace.is_path_ref_write(path_ref):
                            # cmd_execution_info[launch_name].add_to_write_set(trace.get_path_ref_name(path_ref))
                            node_id = partial_program_order.get_node_id_from_cmd_no_redir(launch_name)
                            partial_program_order.add_to_write_set(node_id, trace.get_path_ref_name(path_ref))

def workset_cmds_to_list(cmd_execution_info):
    cmds_to_run = []
    for cmd in cmd_execution_info.values():
        cmds_to_run.append(cmd.cmd)
    return cmds_to_run

def convert_cmd_exec_info_cmd_based_to_id_based_dict(cmd_execution_info_cmd_based_key):
    return {cmd_obj.id: cmd_obj for cmd_obj in cmd_execution_info_cmd_based_key.values()}

def execute_workset_and_find_rw_dependencies(partial_program_order: PartialProgramOrder):
    ## Warning! HACK: Remove these functions in later iteration
    ##                cmd_execution_info is converted to cmd-based dict (instead of id)
    trace_objects = run_and_trace_workset(partial_program_order)
    # Changes are made on the cmd-based structures
    extract_rw_sets_from_traces(partial_program_order, trace_objects)

## NOTE: There are two different types of commits, the sandbox commit,
##     which just means execute the command and see its effects,
##     and the orchestrator commit, which means that this command
##     has completed and will never run again (and all its prefix has also completed).
def run_and_trace_workset(partial_program_order: PartialProgramOrder):
    cmd_procs_and_trace_files = {}

    frontier_ids = [node_id for node_id in partial_program_order.get_workset() if partial_program_order.is_frontier(node_id)]
    frontier_cmds = [partial_program_order.get_node(node_id).get_cmd() for node_id in frontier_ids]
    # We are only working with sequences of commands
    # TODO: In a future iteration, remove this assumption
    assert(len(frontier_cmds) == 1)
    
    first_cmd_id = frontier_ids[0]
    first_cmd = frontier_cmds[0]

    ## Launch all commands to run and be traced
    first_command_trace_file = util.ptempfile()
    logging.debug("First command:", first_cmd, "trace will be saved in:", first_command_trace_file)
    process = executor.async_run_and_trace_command(first_cmd, first_command_trace_file)
    cmd_procs_and_trace_files[first_cmd_id] = (process, first_command_trace_file)

    non_frontier_ids = [node_id for node_id in partial_program_order.get_workset() if not partial_program_order.is_frontier(node_id)]
    non_frontier_cmds = [partial_program_order.get_node(node_id).get_cmd() for node_id in non_frontier_ids]

    for cmd_id in non_frontier_ids:
        cmd = partial_program_order.get_node(cmd_id).get_cmd()
        trace_file = util.ptempfile()
        logging.debug("Command:", cmd, "trace will be saved in:", trace_file)
        process = executor.async_run_and_trace_command_in_sandbox(cmd, trace_file)
        cmd_procs_and_trace_files[cmd_id] = (process, trace_file)
        
    ## Wait for all processes to be done executing
    for cmd_id in sorted(cmd_procs_and_trace_files.keys()):
        p, _file = cmd_procs_and_trace_files[cmd_id]
        ## TODO: Figure out a way to wait on any process
        ##       and not wait on them in sequence as we do now
        p.wait()

    ## Gather all traces
    trace_objects = {}
    for cmd_id, proc_and_trace_file in cmd_procs_and_trace_files.items():
        _proc, trace_file = proc_and_trace_file
        trace_object = executor.read_trace(trace_file)
        trace_objects[cmd_id] = trace_object

    ## Returns a dictionary of traces, one for each command id
    return trace_objects

def scheduling_algorithm(partial_program_order):
    # The workset contains all the command ids that are going to be traced in the current cycle
    partial_program_order.init_workset()
    # Count tracing cycles
    reps = 1
    ## TODO: This will change when we actually hook up with riker
    while len(partial_program_order.get_workset()) > 0:
        ## In every loop iteration we are guaranteed to decrease the workset by 1, 
        ## since the first command will not need to re-execute 
        execute_workset_and_find_rw_dependencies(partial_program_order)
        partial_program_order.log_rw_sets(logging)
        # Check dependencies and anti-dependencies and update speculated commands accordingly
        partial_program_order.resolve_dependencies()
        reps += 1
        log_run_and_workset_info(partial_program_order, reps)

def main():
    cmds_to_run = parse_input(args.input_file)
    partial_program_order = generate_partial_program_order(cmds_to_run)
    log_partial_program_order_graph(partial_program_order)
    scheduling_algorithm(partial_program_order)

logging.basicConfig(level=logging.WARNING, format="%(levelname)s:%(message)s")

args = parse_args()

OUTPUT_TRACE_FILE = args.riker_trace_file

if args.debug_level == 1:
    logging.getLogger().setLevel(logging.INFO)
elif args.debug_level >= 2:
    logging.getLogger().setLevel(logging.DEBUG)

if __name__ == "__main__":
    main()
