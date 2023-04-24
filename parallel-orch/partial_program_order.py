import logging
import os
import executor
import trace
import sys

class CompletedNodeInfo:
    def __init__(self, exit_code, variable_file, stdout_file):
        self.exit_code = exit_code
        self.variable_file = variable_file
        self.stdout_file = stdout_file

    def get_exit_code(self):
        return self.exit_code

    def get_variable_file(self):
        return self.variable_file

    def get_stdout_file(self):
        return self.stdout_file

    def __str__(self):
        return f'CompletedNodeInfo(ec:{self.get_exit_code()}, vf:{self.get_variable_file()}, stdout:{self.get_stdout_file()})'

class Node:
    def __init__(self, id, cmd):
        self.cmd = cmd
        self.id = id
        self.cmd_no_redir = trace.remove_command_redir(self.cmd)

    def __str__(self):
        # return f"ID: {self.id}\nCMD: {self.cmd}\nR: {self.read_set}\nW: {self.write_set}"
        return self.cmd

    def __repr__(self):
        # return f"ID: {self.id}\nCMD: {self.cmd}\nR: {self.read_set}\nW: {self.write_set}"
        return f'N({self.cmd})'

    def get_cmd(self) -> str:
        return self.cmd

    def get_cmd_no_redir(self) -> str:
        return self.cmd_no_redir
    
    ## Note: This information is valid only after a node is committed.
    ##       It might be set even before that, but it should only be retrieved when
    ##         a node is committed.
    def set_completed_info(self, completed_node_info: CompletedNodeInfo):
        self.completed_node_info = completed_node_info
    
    def get_completed_node_info(self) -> CompletedNodeInfo:
        return self.completed_node_info


class RWSet:

    def __init__(self, read_set: set, write_set: set):
        self.read_set = read_set
        self.write_set = write_set

    def add_to_read_set(self, item: str):
        self.read_set.add(item)

    def add_to_write_set(self, item: str):
        self.write_set.add(item)

    def get_read_set(self) -> set:
        return self.read_set

    def get_write_set(self) -> set:
        return self.write_set

    def __str__(self):
        return f"RW(R:{self.get_read_set()}, W:{self.get_write_set()})"

class PartialProgramOrder:

    def __init__(self, nodes, edges):
        self.nodes = nodes
        # TODO: consider changing values to sets instead of lists
        self.adjacency = edges
        self.init_inverse_adjacency()
        ## self.committed is an add-only set, we never remove
        self.committed = set()
        ## Nodes that are in the frontier can only move to committed
        self.frontier = self.get_source_nodes()
        self.speculated = set()
        self.rw_sets = {node_id: None for node_id in self.nodes.keys()}
        self.workset = []
        ## A dictionary from cmd_ids that are currently executing that contains their trace_files
        self.commands_currently_executing = {}
        ## A dictionary that contains information about completed nodes
        ## from cmd_id -> CompletedNodeInfo 
        ## Note: this dictionary does not contain information
        self.completed_node_info = {}
        self.to_be_resolved = {}
        self.waiting_to_be_resolved = set()
        ## Contains the most recent sandbox directory paths
        self.sandbox_dirs = {}
        ## Commands that were killed by riker
        ## we should keep those in the workset but not execute them
        ## until they reach the frontier
        self.stopped = set()
        self.committed_order = []
        self.commit_state = {}
    
    def __str__(self):
        return f"NODES: {len(self.nodes.keys())} | ADJACENCY: {self.adjacency}"

    def get_source_nodes(self) -> list:
        sources = set()
        for to_id, from_ids in self.inverse_adjacency.items():
            if len(from_ids) == 0:
                sources.add(to_id)
        return list(sources)

    def init_workset(self):
        self.workset = self.get_all_non_committed()

    ## Check if the partial order is done
    def is_completed(self) -> bool:
        return len(self.get_all_non_committed()) == 0

    def get_workset(self) -> list:
        return self.workset
    
    def get_committed(self) -> list:
        return sorted(list(self.committed))

    def get_frontier(self) -> list:
        return sorted(list(self.frontier))

    def get_speculated(self) -> set:
        return sorted(list(self.speculated))

    def init_inverse_adjacency(self):
        self.inverse_adjacency = {i: [] for i in self.nodes.keys()}
        for from_id, to_ids in self.adjacency.items():
            for to_id in to_ids:
                self.inverse_adjacency[to_id].append(from_id)

    # ## TODO: (When there is time) Define a function that checks that the graph is valid
    def valid(self):
        ## TODO: Check that committed is prefix closed w.r.t partial order
        self.all_frontier_nodes_after_committed_nodes()
        self.frontier_and_committed_intersect()
        self.speculated_intersects_with_frontier_or_committed()
        return True

    # Check if all frontier nodes are after committed nodes
    def all_frontier_nodes_after_committed_nodes(self):
        return max(self.committed) < min(self.frontier)

    # Checks if frontier and committed intersect
    def frontier_and_committed_intersect(self):
        return len(set.intersection(set(self.get_committed()), set(self.get_frontier()))) > 0
    
    # Checks if speculated intersects with committed and frontier
    def speculated_intersects_with_frontier_or_committed(self):
        return len(set.intersection(set(self.get_speculated()), set(self.get_frontier()))) > 0 \
            or len(set.intersection(set(self.get_speculated()), set(self.get_committed()))) > 0

    def __len__(self):
        return len(self.nodes)

    def get_node(self, node_id:int) -> Node:
        return self.nodes[node_id]

    def get_all_non_committed(self) -> list:
        return self.get_transitive_closure(self.frontier)

    def get_next(self, node_id:int) -> list:
        return self.adjacency[node_id]
    
    def get_transitive_closure(self, target_node_ids:list) -> list:
        all_next_transitive = set(target_node_ids)
        next_work = target_node_ids.copy()
        while len(next_work) > 0:
            node_id = next_work.pop()
            successors = set(self.get_next(node_id))
            new_next = successors - all_next_transitive
            all_next_transitive = all_next_transitive.union(successors)
            next_work.extend(new_next)
        return list(all_next_transitive)

    def get_transitive_closure_if_can_be_resolved(self, can_be_resolved: list, target_node_ids: list) -> list:
        all_next_transitive = set(target_node_ids)
        next_work = target_node_ids.copy()
        while len(next_work) > 0:
            node_id = next_work.pop()
            successors = {next_node_id for next_node_id in self.get_next(node_id) if next_node_id in can_be_resolved}
            new_next = successors - all_next_transitive
            all_next_transitive = all_next_transitive.union(successors)
            next_work.extend(new_next)
        return list(all_next_transitive)

    def is_frontier(self, node_id: int) -> bool:
        return node_id in self.frontier
    
    def update_rw_set(self, node_id, rw_set):
        self.rw_sets[node_id] = rw_set

    def get_rw_set(self, node_id) -> RWSet:
        return self.rw_sets[node_id]
    
    def get_rw_sets(self) -> dict:
        return self.rw_sets

    def add_to_read_set(self, node_id: int, item: str):
        self.rw_sets[node_id].add_to_read_set(item)

    def add_to_write_set(self, node_id: int, item: str):
        self.rw_sets[node_id].add_to_write_set(item)

    # TODO: HACK delete this method ASAP
    def get_node_id_from_cmd_no_redir(self, cmd_no_redir: str) -> int:
        for node_id, node in self.nodes.items():
            if node.get_cmd_no_redir() == cmd_no_redir:
                return node_id
        assert(False)


    # Check if the specific command can be resolved.
    # TODO: this does not truly follow partial program order, we should implement it correctly
    def cmd_can_be_resolved(self, node_id: int) -> bool:
        # If the command we evaluate has no earlier command currently executing, it can be resolved this round
        if len(self.get_currently_executing()) > 0:
            return node_id <= min(self.get_currently_executing())
        else:
            return True
    
    def find_cmds_to_resolve(self, cmd_ids_to_check: list):
        cmds_to_resolve = []
        logging.debug(f" > Uncommitted commands done executing to be checked: {cmd_ids_to_check}")
        for cmd_id in cmd_ids_to_check:
            # We check if we can resolve any possible dependencies
            # If we can't, we have to wait for another cycle
            if not self.cmd_can_be_resolved(cmd_id):
                if cmd_id not in self.waiting_to_be_resolved:
                    logging.debug(f" > Adding node {cmd_id} to waiting list")
                    self.waiting_to_be_resolved.add(cmd_id)
                else:
                    logging.debug(f" > Keeping node {cmd_id} to waiting list")
            # If we are in this branch it means that we can resolve the dependencies of the current command
            else:
                cmds_to_resolve.append(cmd_id)
                # We remove the command from the waiting to be resolved set
                if cmd_id in self.waiting_to_be_resolved:
                    logging.debug(f" > Removing node {cmd_id} from waiting list")
                    self.waiting_to_be_resolved.remove(cmd_id)
                else:
                    logging.debug(f" > Node {cmd_id} is able to be resolved")
        return sorted(cmds_to_resolve)


    def resolve_dependencies(self, cmds_to_resolve):
        # Init stuff
        new_workset = set()
        for second_cmd_id in sorted(cmds_to_resolve):
            first_cmd_ids = sorted([cmd_id for cmd_id in self.to_be_resolved[second_cmd_id] if cmd_id not in self.stopped])
            for first_cmd_id in first_cmd_ids:
                if second_cmd_id not in new_workset:
                    ## If it is None, it means that it has not executed at all,
                    ## so we need to add it in the workset
                    if self.get_rw_set(second_cmd_id) is None:
                        logging.debug(f' > Command: {second_cmd_id} was added to the workset, because it was never executed before')
                        new_workset.add(second_cmd_id)
                        self.speculated.discard(second_cmd_id)
                    ## Only forward dependencies bother us now
                    elif self.has_forward_dependency(first_cmd_id, second_cmd_id):
                        logging.debug(f' > Command {second_cmd_id} was added to the workset, due to a forward dependency with {first_cmd_id}')
                        new_workset.add(second_cmd_id)
                        self.speculated.discard(second_cmd_id)
                    else:
                        logging.debug(f' > No dependencies between {first_cmd_id} and {second_cmd_id}')
        return new_workset

    ## Resolve all the forward dependencies and update the workset
    ## Forward dependency is when a command's output is the same
    ## as the input of a following command
    def resolve_dependencies_continuous_and_move_frontier(self, new_node_id):
        self.log_partial_program_order_info()
        # We want to check every single command that has already finished executing but
        # not yet able to be resolved
        logging.debug(f"Finding sets of commands that can be resolved after {new_node_id} finished executing")
        if new_node_id not in self.stopped:
            cmds_to_resolve = self.find_cmds_to_resolve(sorted(list(self.waiting_to_be_resolved.union({new_node_id}))))
        else:
            logging.debug(f"Node {new_node_id} exited with an error. Not resolving dependencies")
            if new_node_id in self.workset:
                self.workset.remove(new_node_id)
            cmds_to_resolve = []
        logging.debug(f"Commands to check for dependencies this round are: {sorted(cmds_to_resolve)}")
        logging.debug(f"Commands that cannot be resolved this round are: {sorted(self.waiting_to_be_resolved)}")
        
        # If no commands can be resolved this round, 
        # do nothing and wait until a new command finishes executing
        if len(cmds_to_resolve) == 0:
            logging.debug("No resolvable nodes were found in this round, nothing will change...")
            return []
        # We want to resolve dependencies with already speculated cmds as well
        cmds_to_resolve = sorted(list(set(cmds_to_resolve).union(set(self.speculated))))

        logging.debug(f"Commands to be checked for dependencies: {sorted(cmds_to_resolve)}")
        logging.debug(" --- Starting dependency resolution --- ")
        new_workset = self.resolve_dependencies(cmds_to_resolve)

        logging.debug(" > Modifying speculated set accordingly")
        old_speculated = self.speculated.copy()
        # Speculated is a command without dependencies, not stopped or not in frontier
        self.speculated = {cmd_id for cmd_id in cmds_to_resolve if cmd_id not in new_workset and cmd_id not in self.frontier and cmd_id not in self.stopped}
        
        logging.debug(" > Modifying workset accordingly")
        # New workset contains previous unresolved commands and resolved commands with dependencies that have not been stopped
        self.workset = [cmd_id for cmd_id in self.workset if cmd_id not in cmds_to_resolve and cmd_id not in self.stopped]
        self.workset.extend(list(new_workset))

        # Keep the previous committed state
        old_committed = self.committed.copy()

        # We want stopped commands to not enter the workset again yet
        assert(set(self.workset).isdisjoint(self.stopped))

        self.step_forward(old_speculated, old_committed)
        # self.log_partial_program_order_info()
        return self.committed - old_committed

    def rerun_stopped(self):
        new_stopped = self.stopped.copy()
        for cmd_id in self.stopped:
            if cmd_id in self.frontier:
                self.workset.append(cmd_id)
                logging.debug(f"Removing {cmd_id}")
                new_stopped.remove(cmd_id)
        self.stopped = new_stopped

    def step_forward(self, old_speculated, old_committed):
        logging.debug(" > Committing frontier")
        self.commit_frontier()
        logging.debug(" > Moving frontier forward")
        self.move_frontier_forward(old_speculated)
        self.rerun_stopped()
        self.populate_to_be_resolved_dict(old_committed)

    # Add frontier commands to committed set
    def commit_frontier(self):
        # Second condition below may be unecessary
        for frontier_node in self.frontier:
            if frontier_node not in self.workset:
                self.save_commit_state_of_cmd(frontier_node)
        self.committed.update({frontier_node for frontier_node in self.frontier if frontier_node not in self.workset})

    def move_frontier_forward(self, old_speculated: set):
        new_frontier = []
        for node in self.frontier:
            if node not in self.workset: 
                new_frontier.extend(self.get_next_non_speculated(node, old_speculated))
            # If node is being executed again, we cannot progress further
            else:
                new_frontier.extend([node])
        self.frontier = new_frontier

    def get_next_non_speculated(self, start, old_speculated: set):
            traversal_workset = self.get_next(start)
            next_non_speculated = []
            while len(traversal_workset) > 0:
                node_id = traversal_workset.pop()
                if node_id in old_speculated.union(self.speculated):
                    assert(node_id not in self.workset)
                    logging.debug(f"Committing speculated node: {node_id}")
                    self.speculated.discard(node_id)
                    self.save_commit_state_of_cmd(node_id)
                    self.committed.add(node_id)
                    traversal_workset.extend(self.get_next(node_id))
                else:
                    next_non_speculated.append(node_id)
            return list(next_non_speculated)
    

    ## For a file - dir forward dependency to exist,
    ## we need the succeding command to attempt to read anything that is a subpath of the
    ## write set of the preceeding command.
    ## e.g. in: W1: {/foo/}  | R2: {/f1, /foo/f2, /foo/bar/f3}
    ## /foo/f2 and /foo/bar/f3 will trigger the dependency check.
    def has_dir_file_dependency(self, first_cmd_set, second_cmd_set):
        # Get all directory paths without the "/" in the end
        dirs = {dir_path[:-1] for dir_path in first_cmd_set if dir_path.endswith("/")}
        # Get all files in a separate set
        to_check = {filepath for filepath in second_cmd_set if not filepath.endswith("/")}
        for dir in dirs:
            for other_path in to_check:
                if self.is_subpath(dir, other_path):
                    return True
        return False
    
    def is_subpath(self, dir, other_path):
        other_path.startswith(os.path.abspath(dir)+os.sep)

    def has_forward_dependency(self, first_id, second_id):
        first_write_set = set(self.rw_sets[first_id].get_write_set())
        second_read_set = set(self.rw_sets[second_id].get_read_set())
        if not first_write_set.isdisjoint(second_read_set):
            logging.debug("Forward dep")
            return True

        elif self.has_dir_file_dependency(first_write_set, second_read_set):
            logging.debug("file forward dep")
            return True
        else:
            return False

    ## TODO: Eventually, in the future, let's add here some form of limit
    def schedule_work(self, limit=0):
        self.run_all_frontier_cmds()
        self.schedule_all_workset_non_frontier_cmds()

    def schedule_all_workset_non_frontier_cmds(self):
        non_frontier_ids = [node_id for node_id in self.get_workset() 
                            if not self.is_frontier(node_id)]
        for cmd_id in non_frontier_ids:
            # We also need for a cmd to not be waiting to be resolved.
            if not cmd_id in self.commands_currently_executing and not cmd_id in self.waiting_to_be_resolved:
                self.speculate_cmd_non_blocking(cmd_id)

    def run_all_frontier_cmds(self):
        logging.debug("Starting execution on the whole frontier")
        cmd_ids = self.get_frontier()
        for cmd_id in cmd_ids:
            # If frontier cmd is still executing, don't re-execute it
            if not cmd_id in self.commands_currently_executing:
                # We also re-execute stopped frontier cmds,
                # therefore, they are no longer stopped
                logging.debug(f" Removing {cmd_id} from stopped")
                self.stopped.discard(cmd_id)
                self.run_cmd_non_blocking(cmd_id)

    ## Run a command and add it to the dictionary of executing ones
    def run_cmd_non_blocking(self, node_id: int):
        ## A command should only be run if it's in the frontier, otherwise it should be spec run
        assert(self.is_frontier(node_id))
        node = self.get_node(node_id)
        cmd = node.get_cmd()
        logging.debug(f'Running command: {node_id} {self.get_node(node_id)}')
        proc, trace_file, stdout, stderr, variable_file = executor.async_run_and_trace_command_return_trace(cmd, node_id)
        logging.debug(f'Read trace from: {trace_file}')
        self.commands_currently_executing[node_id] = (proc, trace_file, stdout, stderr, variable_file)

    ## Run a command and add it to the dictionary of executing ones
    def speculate_cmd_non_blocking(self, node_id: int):
        node = self.get_node(node_id)
        cmd = node.get_cmd()
        logging.debug(f'Speculating command: {node_id} {self.get_node(node_id)}')
        proc, trace_file, stdout, stderr, variable_file = executor.async_run_and_trace_command_return_trace_in_sandbox(cmd, node_id)
        logging.debug(f'Read trace from: {trace_file}')
        self.commands_currently_executing[node_id] = (proc, trace_file, stdout, stderr, variable_file)

    def command_execution_completed(self, node_id: int, riker_exit_code:int, sandbox_dir: str):
        logging.debug(f" --- Node {node_id}, just finished execution ---")
        self.sandbox_dirs[node_id] = sandbox_dir
        ## TODO: Store variable file somewhere so that we can return when wait
        proc, trace_file, stdout, stderr, variable_file = self.commands_currently_executing.pop(node_id)
        # Handle stopped by riker due to network access
        if int(riker_exit_code) == 159:
            logging.debug(f" > Adding {node_id} to stopped because it tried to access the network.")
            self.stopped.add(node_id)
        trace_object = executor.read_trace(sandbox_dir, trace_file)
        cmd_exit_code = trace.parse_exit_code(trace_object)

        ## Save the completed node info. Note that if the node doesn't commit
        ##  this information will be invalid and rewritten the next time execution
        ##  is completed for this node.
        completed_node_info = CompletedNodeInfo(cmd_exit_code, variable_file, stdout)
        self.nodes[node_id].set_completed_info(completed_node_info)

        # Handle any other cmd exit with error
        # TODO: for now we just postpone them until we reach the frontier
        #       afterwards we might want to reattempt to speculate them
        if cmd_exit_code != 0 and node_id not in self.frontier:
            logging.debug(f" > Adding {node_id} to stopped because it exited with an error.")
            self.stopped.add(node_id)
        else:
            read_set, write_set = trace.parse_and_gather_cmd_rw_sets(trace_object)
            rw_set = RWSet(read_set, write_set)
            self.update_rw_set(node_id, rw_set)
        to_commit = self.resolve_dependencies_continuous_and_move_frontier(node_id)
        if len(to_commit) == 0:
            logging.debug(" > No nodes to be committed this round")
        else:
            logging.debug(f" > Nodes to be committed this round: {to_commit}")
            self.commit_cmd_workspaces(to_commit)
            self.print_cmd_stderr(stderr)

    def print_cmd_stderr(self, stderr):
        # stdout.seek(0)
        # print(stdout.read().decode(), end="")
        stderr.seek(0)
        print(stderr.read().decode(), file=sys.stderr, end="")

    def commit_cmd_workspaces(self, to_commit_ids):
        for cmd_id in to_commit_ids:
            workspace = self.sandbox_dirs[cmd_id]
            if workspace != "":
                logging.debug(f" (!) Committing workspace of cmd {cmd_id} found in {workspace}")
                commit_workspace_out = executor.commit_workspace(workspace)
                logging.debug(commit_workspace_out.decode())
            else:
                logging.debug(f" (!) No need to commit workspace of cmd {cmd_id} as it was run in the main workspace")

    def log_rw_sets(self):
        logging.debug("====== RW Sets " + "=" * 65)
        for node_id, rw_set in self.rw_sets.items():
            logging.debug(f"ID:{node_id} | R.size:{len(rw_set.get_read_set()) if rw_set is not None else None} | W:{rw_set.get_write_set() if rw_set is not None else None}")

    def log_partial_program_order_info(self):
        logging.debug(f"=" * 80)
        logging.debug(f"WORKSET:        {self.get_workset()}")
        logging.debug(f"COMMITTED:      {self.get_committed()}")
        logging.debug(f"FRONTIER:       {self.get_frontier()}")
        logging.debug(f"SPECULATED:     {self.get_speculated()}")
        logging.debug(f"EXECUTING:      {list(self.commands_currently_executing.keys())}")
        logging.debug(f"STOPPED:        {list(self.stopped)}")
        logging.debug(f"WAITING:        {sorted(list(self.waiting_to_be_resolved))}")
        logging.debug(f"TO RESOLVE:     {self.to_be_resolved}")
        self.log_rw_sets()
        logging.debug(f"=" * 80)

    ## TODO: Document how this finds the to be resolved dict
    def populate_to_be_resolved_dict(self, old_committed):
        logging.debug("Populating the resolved dictionary for all nodes")
        for node_id in self.nodes:
            if node_id in self.committed:
                logging.debug(f" > Node: {node_id} is committed, emptying its dict")
                self.to_be_resolved[node_id] = []
                continue
            # We don't want to modify the set of nodes to check for dependencies for this node
            # as it started running before previous cmds had started executing
            elif node_id in self.waiting_to_be_resolved:
                logging.debug(f" > Node: {node_id} is waiting to be resolved, skipping...")
                continue
            elif node_id in self.get_currently_executing():
                logging.debug(f" > Node: {node_id} is currently executing, skipping...")
                continue
            else:
                logging.debug(f" > Node: {node_id} is not executing or waiting to be resolved so we modify its set.")
                self.to_be_resolved[node_id] = []
                traversal = []
                ## KK 2023-04-24: Previously old_committed was used here
                ##                but this doesn't make sense because we are only modifying
                ##                the to_be_resolved of currently executing commands.
                # relevant_committed = old_committed
                relevant_committed = self.committed
                if node_id not in relevant_committed:
                    to_add = self.inverse_adjacency[node_id].copy()
                    traversal = to_add.copy()
                    to_be_resolved_nodes_ids = to_add.copy()
                while len(traversal) > 0:
                    current_node_id = traversal.pop(0)
                    if current_node_id not in relevant_committed:
                        to_add = self.inverse_adjacency[current_node_id]
                        to_be_resolved_nodes_ids.extend(to_add)
                        traversal.extend(to_add)
                self.to_be_resolved[node_id] = to_be_resolved_nodes_ids.copy()
                self.to_be_resolved[node_id] = list(set(self.to_be_resolved[node_id]) - set(relevant_committed))
                logging.debug(f' |> New to be resolved set: {self.to_be_resolved[node_id]}')

    def get_currently_executing(self) -> list:
        return sorted(list(self.commands_currently_executing.keys()))
    
    def save_commit_state_of_cmd(self, cmd_id):
        self.committed_order.append(cmd_id)
        self.commit_state[cmd_id] = set(self.committed) - set(self.to_be_resolved[cmd_id])

    def log_committed_cmd_state(self):
        logging.info("---------- Committed Order -----------")
        logging.info(" " + " -> ".join(map(str, self.committed_order)))
        logging.info("---------- Committed State -----------")
        for cmd in sorted(self.committed):
            if len(self.commit_state[cmd]) == 0:
                logging.info(f" CMD {cmd} on\t\tSTART")
            else:
                logging.info(f" CMD {cmd} after:\t{', '.join(map(str, self.commit_state[cmd]))}")
        logging.info("--------------------------------------")



def parse_cmd_from_file(file_path: str) -> str:
    with open(file_path) as f:
        cmd = f.read()
    return cmd

def parse_edge_line(line: str) -> "tuple[int, int]":
    from_str, to_str = line.split(" -> ")
    return (int(from_str), int(to_str))

def parse_partial_program_order_from_file(file_path: str) -> PartialProgramOrder:
    with open(file_path) as f:
        raw_lines = f.readlines()
    
    ## Filter comments and remove new lines
    lines = [line.rstrip() for line in raw_lines
             if not line.startswith("#")]

    ## The first line is the directory in which cmd_files are
    cmds_directory = str(lines[0])
    logging.debug(f'Cmds are stored in: {cmds_directory}')

    ## The last line is the number of nodes
    number_of_nodes = int(lines[-1])
    logging.debug(f'Number of po cmds: {number_of_nodes}')

    ## The rest of the lines are edge_lines
    edge_lines = lines[1:-1]
    logging.debug(f'Edges: {edge_lines}')

    nodes = {}
    for i in range(number_of_nodes):
        file_path = f'{cmds_directory}/{i}'
        cmd = parse_cmd_from_file(file_path)
        nodes[i] = Node(i, cmd)

    edges = {i : [] for i in range(number_of_nodes)}
    for edge_line in edge_lines:
        from_id, to_id = parse_edge_line(edge_line)
        edges[from_id].append(to_id)
    
    return PartialProgramOrder(nodes, edges)
