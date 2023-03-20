import logging

import executor
import trace

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
        self.to_be_resolved = set()
    
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
            return node_id < min(self.get_currently_executing())
        else:
            return True
    
    def find_cmds_to_resolve(self, cmd_ids_to_check: list):
        cmds_to_resolve = []
        logging.debug(f" > Uncommitted commands done executing to be checked: {cmd_ids_to_check}")
        for cmd_id in cmd_ids_to_check:
            # We check if we can resolve any possible dependencies
            # If we can't, we have to wait for another cycle
            if not self.cmd_can_be_resolved(cmd_id):
                if cmd_id not in self.to_be_resolved:
                    logging.debug(f" > Adding node {cmd_id} to waiting list")
                    self.to_be_resolved.add(cmd_id)
                else:
                    logging.debug(f" > Keeping node {cmd_id} to waiting list")
            # If we are in this branch it means that we can resolve the dependencies of the current command
            else:
                cmds_to_resolve.append(cmd_id)
                # We remove the command from the waiting to be resolved set
                if cmd_id in self.to_be_resolved:
                    logging.debug(f" > Removing node {cmd_id} from waiting list")
                    self.to_be_resolved.remove(cmd_id)
                else:
                    logging.debug(f" > Node {cmd_id} is able to be resolved")
        return sorted(cmds_to_resolve)


    ## Resolve all the forward dependencies and update the workset
    ## Forward dependency is when a command's output is the same
    ## as the input of a following command
    def resolve_dependencies_continuous(self, new_node_id):
        # We want to check every single command that has already finished executing but
        # not yet able to be resolved
        logging.debug("Finding sets of commands that can be resolved after {new_node_id} finished executing")
        cmds_to_resolve = self.find_cmds_to_resolve(sorted(list(self.to_be_resolved.union({new_node_id}))))
        logging.debug(f"Commands to check for dependencies this round are:  {sorted(cmds_to_resolve)}")
        logging.debug(f"Commands that can not be resolved this round are:   {sorted(self.to_be_resolved)}")
        
        # If no commands can be resolved this round, 
        # do nothing and wait until a new command finishes executing
        if len(cmds_to_resolve) == 0:
            logging.debug("No resolvable nodes were found in this round, nothing will change...")
            return

        # Init stuff
        independent_cmds_this_cycle = set(cmds_to_resolve)
        new_workset = set()
        old_workset = self.workset.copy()
        logging.debug(" --- Starting dependency resolution --- ")
        logging.debug(f"Commands to be checked for dependencies: {sorted(cmds_to_resolve)}")
        for first_cmd_id in cmds_to_resolve:
            # We don't want the first cmd, so we remove it from the transitive closure.
            transitive_closure = self.get_transitive_closure_if_can_be_resolved(cmds_to_resolve, [first_cmd_id])
            transitive_closure.remove(first_cmd_id)
            logging.debug(f" > Resolvable transitive closure for node {first_cmd_id} is: {transitive_closure}")
            # We look at the transitive closure instead of workset because we want to also check the speculated cmds that are not in the workset
            for second_cmd_id in transitive_closure:
                # If cmd already in new_workset there is no reason to check further, it will be rerun no matter what
                if second_cmd_id not in new_workset:
                    ## If it is None, it means that it has not executed at all,
                    ## so we need to add it in the workset
                    ## TODO: Check for overwork
                    if self.get_rw_set(second_cmd_id) is None:
                        logging.debug(f' > Command: {second_cmd_id} was added to the workset, because it was never executed before')
                        new_workset.add(second_cmd_id)
                    elif self.has_backward_dependency(first_cmd_id, second_cmd_id):
                        logging.debug(f' > Command {second_cmd_id} was added to the workset, due to a backward dependency with {first_cmd_id}')
                        new_workset.add(second_cmd_id)
                    elif self.has_write_dependency(first_cmd_id, second_cmd_id):
                        logging.debug(f' > Command {second_cmd_id} was added to the workset, due to a write dependency with {first_cmd_id}')
                        new_workset.add(second_cmd_id)
                    elif self.has_forward_dependency(first_cmd_id, second_cmd_id):
                        logging.debug(f' > Command {second_cmd_id} was added to the workset, due to a forward dependency with {first_cmd_id}')
                        new_workset.add(second_cmd_id)
        logging.debug(f"New workset after examining nodes {cmds_to_resolve} is: {new_workset}")
        logging.debug(" --- Done with dependency resolution --- ")
        
        old_speculated = self.speculated.copy()

        self.speculated = {cmd_id for cmd_id in cmds_to_resolve if cmd_id not in new_workset and cmd_id not in self.frontier}
        logging.debug(" > Modifying speculated set accordingly")
        # Set the new workset
        logging.debug(" > Modifying workset accordingly")

        self.workset = [cmd_id for cmd_id in self.workset if cmd_id not in cmds_to_resolve]
        self.workset.extend((list(new_workset)))
        self.workset = [cmd_id for cmd_id in self.workset if cmd_id not in cmds_to_resolve]
        self.workset.extend((list(new_workset)))
        
        old_committed = self.committed.copy()
        old_frontier = self.frontier.copy()
        
        self.step_forward(old_speculated)
        self.log_partial_program_order_info()

        logging.debug(f"Commands checked this cycle: {sorted(cmds_to_resolve)}")
        logging.debug(f"Workset    old: {old_workset}")
        logging.debug(f"Workset    new: {self.workset}")
        logging.debug(f"Speculated old: {old_speculated}")
        logging.debug(f"Speculated new: {self.committed}")
        logging.debug(f"Committed  old: {old_committed}")
        logging.debug(f"Committed  new: {self.committed}")
        logging.debug(f"Frontier   old: {old_frontier}")
        logging.debug(f"Frontier   new: {self.frontier}")

    def step_forward(self, old_speculated):
        logging.debug(" > Committing frontier")
        self.commit_frontier()
        logging.debug(" > Moving frontier forward")
        self.move_frontier_forward(old_speculated)

    # Add frontier commands to committed set
    def commit_frontier(self):
        # Second condition below may be unecessary
        self.committed.update({frontier_node for frontier_node in self.frontier})

    def move_frontier_forward(self, old_speculated: set):
        new_frontier = []
        for node in self.frontier:
            new_frontier.extend(self.get_next_non_speculated(node, old_speculated))
        
        self.frontier = new_frontier
        # self.frontier.node.extend(new_frontier)

    def get_next_non_speculated(self, start, old_speculated: set):
            traversal_workset = self.get_next(start)
            next_non_speculated = []
            while len(traversal_workset) > 0:
                node_id = traversal_workset.pop()
                if node_id in old_speculated.union(self.speculated):
                    logging.debug(f"Committing speculated node: {node_id}")
                    self.speculated.discard(node_id)
                    self.committed.add(node_id)
                    traversal_workset.extend(self.get_next(node_id))
                else:
                    next_non_speculated.append(node_id)
            return next_non_speculated
  
    def has_forward_dependency(self, first_id, second_id):
        first_write_set = set(self.rw_sets[first_id].get_write_set())
        second_read_set = set(self.rw_sets[second_id].get_read_set())
        return not first_write_set.isdisjoint(second_read_set)

    def has_backward_dependency(self, first_id, second_id):
        first_write_set = set(self.rw_sets[first_id].get_read_set())
        second_read_set = set(self.rw_sets[second_id].get_write_set())
        return not first_write_set.isdisjoint(second_read_set)

    def has_write_dependency(self, first_id, second_id):
        first_write_set = set(self.rw_sets[first_id].get_write_set())
        second_read_set = set(self.rw_sets[second_id].get_write_set())
        return not first_write_set.isdisjoint(second_read_set)

    ## TODO: Eventually, in the future, let's add here some form of limit
    def schedule_work(self, limit=0):
        if len(self.workset) > 0:
            self.run_all_frontier_cmds()
            self.schedule_all_workset_non_frontier_cmds()
        ## TODO: Use the partial order object to pick a few commands (for start let's do all)
        ##       and run them using the scheduler.
        ##
        ## TODO: When scheduling commands, run them with subprocess.run and make sure that at the end
        ##       they will try to connect to our scheduler socket $PASH_SPEC_SCHEDULER_SOCKET to let us
        ##       know that they are done.
        else:
            logging.debug("Workset is empty, nothing to be scheduled")
        pass

    def schedule_all_workset_non_frontier_cmds(self):
        non_frontier_ids = [node_id for node_id in self.get_workset() 
                            if not self.is_frontier(node_id)]
        for cmd_id in non_frontier_ids:
            # We also need for a cmd to not be waiting to be resolved.
            logging.debug(f">> Commands to speculatively execute: {[cmd_id for cmd_id in self.commands_currently_executing if cmd_id not in self.to_be_resolved]}")
            if not cmd_id in self.commands_currently_executing and not cmd_id in self.to_be_resolved:
                self.speculate_cmd_non_blocking(cmd_id)

    def run_all_frontier_cmds(self):
        logging.debug("Starting execution on the whole frontier")
        cmd_ids = self.get_frontier()
        for cmd_id in cmd_ids:
            if not cmd_id in self.commands_currently_executing:
                self.run_cmd_non_blocking(cmd_id)

    ## Run a command and add it to the dictionary of executing ones
    def run_cmd_non_blocking(self, node_id: int):
        ## A command should only be run if it's in the frontier, otherwise it should be spec run
        assert(self.is_frontier(node_id))
        node = self.get_node(node_id)
        cmd = node.get_cmd()
        logging.debug(f'Running command: {node_id} {self.get_node(node_id)}')
        proc, trace_file = executor.async_run_and_trace_command_return_trace(cmd, node_id)
        logging.debug(f'Read trace from: {trace_file}')
        self.commands_currently_executing[node_id] = (proc, trace_file)

    ## Run a command and add it to the dictionary of executing ones
    def speculate_cmd_non_blocking(self, node_id: int):
        node = self.get_node(node_id)
        cmd = node.get_cmd()
        logging.debug(f'Speculating command: {node_id} {self.get_node(node_id)}')
        proc, trace_file = executor.async_run_and_trace_command_return_trace_in_sandbox(cmd, node_id)
        logging.debug(f'Read trace from: {trace_file}')
        self.commands_currently_executing[node_id] = (proc, trace_file)

    def command_execution_completed(self, node_id: int):
        _proc, trace_file = self.commands_currently_executing.pop(node_id)
        trace_object = executor.read_trace(trace_file)
        read_set, write_set = trace.parse_and_gather_cmd_rw_sets(trace_object)
        rw_set = RWSet(read_set, write_set)
        self.update_rw_set(node_id, rw_set)

        ## TODO: Maybe we can just resolve dependencies of a single command and not the whole workset.
        logging.debug(f" --- Node {node_id}, just finished execution ---")
        # self.log_partial_program_order_info()
        self.resolve_dependencies_continuous(node_id)
        # self.log_partial_program_order_info()

    def log_rw_sets(self, logging):
        logging.debug("====== |RW Sets| ======")
        for node_id, rw_set in self.rw_sets.items():
            logging.debug(f"ID: {node_id}")
            logging.debug(f"Read: {rw_set.get_read_set()}")
            logging.debug(f"Write: {rw_set.get_write_set()}")

    def log_rw_sets(self):
        logging.debug("====== |RW Sets| ======")
        for node_id, rw_set in self.rw_sets.items():
            logging.debug(f"ID: {node_id}")
            logging.debug(f"Read: {len(rw_set.get_read_set()) if rw_set is not None else None}")
            logging.debug(f"Write: {len(rw_set.get_write_set()) if rw_set is not None else None}")

    def log_partial_program_order_info(self):
        logging.debug(f"=" * 60)
        logging.debug(f"WORKSET:    {self.get_workset()}")
        logging.debug(f"COMMITTED:  {self.get_committed()}")
        logging.debug(f"FRONTIER:   {self.get_frontier()}")
        logging.debug(f"SPECULATED: {self.get_speculated()}")
        logging.debug(f"EXECUTING:  {list(self.commands_currently_executing.keys())}")
        logging.debug(f"WAITING:    {sorted(list(self.to_be_resolved))}")
        logging.debug(f"=" * 60)

    def get_currently_executing(self) -> list:
        return sorted(list(self.commands_currently_executing.keys()))

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
