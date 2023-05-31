import copy
import logging
import os
import sys

import analysis
import executor
import trace

from shasta.ast_node import AstNode, CommandNode

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

## This class is used for both loop contexts and loop iters
## The indices go from inner to outer
class LoopStack:
    def __init__(self, loop_contexts_or_iters=None):
        if loop_contexts_or_iters is None:
            self.loops = []
        else:
            self.loops = loop_contexts_or_iters

    def is_empty(self):
        return len(self.loops) == 0

    def __len__(self):
        return len(self.loops)

    ## Generates a new loop stack with the same length but 0s as values
    def new_zeroed_loop_stack(self):
        return [0 for i in self.loops]

    def get_outer(self):
        return self.loops[-1]

    def pop_outer(self):
        return self.loops.pop()
    
    def add_inner(self, loop_iter_id: int):
        self.loops.insert(0, loop_iter_id)

    def outer_to_inner(self):
        return self.loops[::-1]

    def index(self, loop_iter_id: int) -> int:
        return self.loops.index(loop_iter_id)

    def get(self, index: int):
        return self.loops[index]

    def __repr__(self):
        ## TODO: Represent it using 'it', 'it0', 'it1', etc
        ##       or -(iters)- in front of it.
        output = "-".join([str(it) for it in self.loops])
        return output

    def __eq__(self, other):
        if not len(self.loops) == len(other.loops):
            return False
        for i in range(len(self.loops)):
            if not self.loops[i] == other.loops[i]:
                return False
        return True


class NodeId:
    def __init__(self, id: int, loop_iters=None):
        self.id = id
        
        if loop_iters is None:
            self.loop_iters = LoopStack()
        else:
            assert(isinstance(loop_iters, LoopStack))
            self.loop_iters = loop_iters
    
    def has_iters(self):
        return not self.loop_iters.is_empty()
    
    def get_iters(self):
        return copy.deepcopy(self.loop_iters)

    def get_non_iter_id(self):
        return NodeId(self.id)

    ## Returns a new NodeId
    def generate_new_node_id_with_another_iter(self, new_iter: int):
        ## This node already contains iterations for the outer loops potentially
        ##  so we just need to add another inner iteration
        new_iters = copy.deepcopy(self.loop_iters)
        new_iters.add_inner(new_iter)

        new_node_id = NodeId(self.id, new_iters)
        return new_node_id

    def __repr__(self):
        ## TODO: Represent it using n.
        output = f'{self.id}'
        if not self.loop_iters.is_empty():
            output += f'+{self.loop_iters}'
        return output

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return self.loop_iters == other.loop_iters and self.id == other.id

    def __ne__(self, other):
        # Not strictly necessary, but to avoid having both x==y and x!=y
        # True at the same time
        return not(self == other)
    
    ## TODO: Define this correctly if it is to be used for something other than dictionary indexing
    def __lt__(self, obj):
        return (str(self) < str(obj))
  
    def __gt__(self, obj):
        return (str(self) > str(obj))
  
    # def __le__(self, obj):
    #     return ((self.b) <= (obj.b))
  
    # def __ge__(self, obj):
    #     return ((self.b) >= (obj.b))

def parse_node_id(node_id_str: str) -> NodeId:
    if "+" in node_id_str:
        node_id_int, iters_str = node_id_str.split("+")
        iters = [int(it) for it in iters_str.split("-")]
        return NodeId(int(node_id_int), LoopStack(iters))
    else:
        return NodeId(int(node_id_str), LoopStack())

class Node:
    id: NodeId
    cmd: str
    asts: "list[AstNode]"
    loop_context: LoopStack

    def __init__(self, id, cmd, asts, loop_context: LoopStack):
        self.id = id
        self.cmd = cmd
        self.asts = asts
        ## There can only be a single AST per node, and this
        ##  must be a command.
        assert(len(asts) == 1)
        assert(isinstance(asts[0], CommandNode))
        self.cmd_no_redir = trace.remove_command_redir(self.cmd)
        self.loop_context = loop_context
        ## Keep track of how many iterations of this loop node we have unrolled
        if not loop_context.is_empty():
            self.current_iters = loop_context.new_zeroed_loop_stack()

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
    
    def get_loop_context(self) -> LoopStack:
        return self.loop_context
    
    def in_loop(self) -> bool:
        return not self.loop_context.is_empty()

    ## KK 2023-05-17 Does this generate the correct iteration even in nested loops?
    def get_next_iter(self, loop_id: int) -> int:
        assert(self.in_loop())
        assert(self.loop_context.get_outer() == loop_id)
        loop_id_index_in_loop_context_stack = self.loop_context.index(loop_id)
        self.current_iters[loop_id_index_in_loop_context_stack] += 1
        return self.current_iters[loop_id_index_in_loop_context_stack]

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
        ## TODO: KK: Is it OK if we modify adjacency lists on the fly while processing the partial-order?
        ## TODO: Remember to modify inverse_adjacency
        ## self.committed is an add-only set, we never remove
        ## TODO: For loop modify committed, workset, frontier, stopped
        ## TODO: Add assertions that committed etc do not contain loop nodes
        self.committed = set()
        ## Nodes that are in the frontier can only move to committed
        self.frontier = []
        self.rw_sets = {node_id: None for node_id in self.nodes.keys()}
        self.workset = []
        ## A dictionary from cmd_ids that are currently executing that contains their trace_files
        self.commands_currently_executing = {}
        ## A dictionary that contains information about completed nodes
        ## from cmd_id -> CompletedNodeInfo 
        ## Note: this dictionary does not contain information
        ## TODO: Delete this
        self.completed_node_info = {}
        ## KK 2023-05-09 @Giorgo What is the difference of the following two?
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
        ## Counts the times a node was (re)executed
        self.executions = {node_id: 0 for node_id in self.nodes.keys()}
    
    def __str__(self):
        return f"NODES: {len(self.nodes.keys())} | ADJACENCY: {self.adjacency}"

    def get_source_nodes(self) -> list:
        sources = set()
        for to_id, from_ids in self.inverse_adjacency.items():
            if len(from_ids) == 0:
                sources.add(to_id)
        return list(sources)

    def get_standard_source_nodes(self) -> list:
        source_nodes = self.get_source_nodes()
        return self.filter_standard_nodes(source_nodes)

    ## This returns the minimum w.r.t. to the PO of a bunch of node_ids.
    ## In a real partial order, this could be many,
    def get_min(self, node_ids: "list[NodeId]") -> "list[NodeId]":
        potential_minima = set(copy.deepcopy(node_ids))
        for node_id in node_ids:
            tc = self.get_transitive_closure([node_id])
            ## Remove the node itself from its transitive closure
            tc.remove(node_id)
            ## If a node is found in the tc of another node, then
            ##  it is not a minimum
            for nid in tc:
                potential_minima.discard(nid)
        ## KK 2023-05-22 This will be removed at some point but I keep it here
        ##    for now for easier bug finding.
        # logging.debug(f"Potential minima: {potential_minima}")
        assert(len(potential_minima) == 1)
        return list(potential_minima)

    ## This returns all previous nodes of a sub partial order
    def get_sub_po_source_nodes(self, node_ids: "list[NodeId]") -> "list[NodeId]":
        # assert(self.is_closed_sub_partial_order(node_ids))
        source_nodes = list()
        node_set = set(node_ids)
        for node_id in node_ids:
            prev_ids_set = set(self.get_prev(node_id))
            ## KK 2023-05-04 is it ever the case that some (but not all) prev nodes might be outside. I don't think so
            if len(prev_ids_set) == 0 or \
                not prev_ids_set.issubset(node_set):
                source_nodes.append(node_id)
        
        ## KK 2024-05-03: I don't see how we can get multiple sources with the current structure
        assert(len(source_nodes) == 1)
        return source_nodes
    
    def get_sub_po_sink_nodes(self, node_ids: "list[NodeId]") -> "list[NodeId]":
        # assert(self.is_closed_sub_partial_order(node_ids))
        sink_nodes = list()
        node_set = set(node_ids)
        for node_id in node_ids:
            next_ids_set = set(self.get_next(node_id))
            ## KK 2023-05-04 is it ever the case that some (but not all) prev nodes might be outside. I don't think so
            if len(next_ids_set) == 0 or \
                not next_ids_set.issubset(node_set):
                sink_nodes.append(node_id)
        
        ## KK 2024-05-03: I don't see how we can get multiple sink with the current structure
        assert(len(sink_nodes) == 1)
        return sink_nodes

    ## This returns all previous nodes of a sub partial order
    def get_sub_po_prev_nodes(self, node_ids: "list[NodeId]") -> "list[NodeId]":
        # assert(self.is_closed_sub_partial_order(node_ids))
        prev_nodes = set()
        node_set = set(node_ids)
        for node_id in node_ids:
            prev_ids_set = set(self.get_prev(node_id))
            prev_nodes = prev_nodes.union(prev_ids_set - node_set)
        
        ## KK 2024-05-03: I don't see how we can get multiple sources with the current structure
        assert(len(prev_nodes) <= 1)
        return list(prev_nodes)

    ## TODO: Implement this correctly. I have thought of a naive algorithm that
    ##       does a BFS forward and backward for each node and if we first see a
    ##       node outside of the set and then one inside it means that the subset is not closed.
    def is_closed_sub_partial_order(self, node_ids: "list[NodeId]") -> bool:
        # node_set = set(node_ids)
        # visited_set = set()
        # for node_id in node_ids:
        #     prev_ids_set = set(self.get_prev(node_id))
        #     next_id_set = set(self.get_next(node_id))
        #     ## If one of the previous or next nodes is not in the node set
        #     ## it means that the sub partial order is not closed.
        #     if not node_set.issuperset(prev_ids_set.union(next_id_set)):
        #         return False

        return True

    def init_partial_order(self):
        ## Initialize the frontier with all non-loop source nodes
        self.frontier = self.get_standard_source_nodes()
        ## Initialize the workset
        self.init_workset()
        logging.debug(f'Initialized workset')
        self.populate_to_be_resolved_dict([])
        logging.debug(f'To be resolved sets per node:')
        logging.debug(self.to_be_resolved)
        logging.info(f'Initialized the partial order!')
        self.log_partial_program_order_info()
        
        assert(self.valid())

    def init_workset(self):
        self.workset = self.get_all_non_committed_standard_nodes()

    ## Check if the partial order is done
    def is_completed(self) -> bool:
        return len(self.get_all_non_committed_standard_nodes()) == 0

    def get_workset(self) -> list:
        return self.workset
    
    def get_committed(self) -> set:
        return copy.deepcopy(self.committed)

    def get_committed_list(self) -> list:
        return sorted(list(self.committed))

    def is_committed(self, node_id: NodeId) -> bool:
        return node_id in self.committed

    def get_frontier(self) -> list:
        return sorted(list(self.frontier))

    def init_inverse_adjacency(self):
        self.inverse_adjacency = {i: [] for i in self.nodes.keys()}
        for from_id, to_ids in self.adjacency.items():
            for to_id in to_ids:
                self.inverse_adjacency[to_id].append(from_id)

    # ## TODO: (When there is time) Define a function that checks that the graph is valid
    ## TODO: Call valid and add assertiosn for loops here.
    def valid(self):
        logging.debug("Checking partial order validity...")
        self.log_partial_program_order_info()
        valid1 = self.loop_nodes_valid()
        ## TODO: Add a check that for x, y : NodeIds, x < y iff x is a predecessor to x
        ##       This is necessary due to the `hypothetical_before` method.

        ## TODO: Fix the checks below because they do not work currently
        ## TODO: Check that committed is prefix closed w.r.t partial order
        # self.all_frontier_nodes_after_committed_nodes()
        # self.frontier_and_committed_intersect()
        return valid1

    ## Checks if loop nodes are all valid, i.e., that there are no loop nodes handled like normal ones,
    ##   e.g., in workset, frontier etc
    ##
    ## Note that loop nodes can be in the committed set (after we are done executing all iterations of a loop)
    def loop_nodes_valid(self):
        forbidden_sets = self.get_frontier() + \
                         self.get_workset() + \
                         list(self.stopped) + \
                         list(self.commands_currently_executing.keys())
        loop_nodes_in_forbidden_sets = [node_id for node_id in forbidden_sets 
                                if self.is_loop_node(node_id)]
        return len(loop_nodes_in_forbidden_sets) == 0

    # Check if all frontier nodes are after committed nodes
    def all_frontier_nodes_after_committed_nodes(self):
        ## TODO: Make this check a proper predecessor check
        # return max(self.get_committed()) < min(self.frontier)
        return False

    # Checks if frontier and committed intersect
    def frontier_and_committed_intersect(self):
        return len(set.intersection(set(self.get_committed()), set(self.get_frontier()))) > 0

    def __len__(self):
        return len(self.nodes)

    def get_node(self, node_id:NodeId) -> Node:
        return self.nodes[node_id]

    def is_node_id(self, node_id:NodeId) -> bool:
        return node_id in self.nodes

    def get_node_loop_context(self, node_id: NodeId) -> LoopStack:
        return self.get_node(node_id).get_loop_context()

    def get_all_non_committed(self) -> "list[NodeId]":
        all_node_ids = self.nodes.keys()
        non_committed_node_ids = [node_id for node_id in all_node_ids
                                  if not self.is_committed(node_id)]  
        return non_committed_node_ids
    
    ## This adds a node to the committed set and saves important information
    def commit_node(self, node_id: NodeId):
        logging.trace(f" > Commiting node {node_id}")
        self.save_commit_state_of_cmd(node_id)
        self.committed.add(node_id)


    def is_loop_node(self, node_id:NodeId) -> bool:
        return self.get_node(node_id).in_loop()

    ## Only keeps standard (non-loop) nodes
    def filter_standard_nodes(self, node_ids: "list[NodeId]") -> "list[NodeId]":
        return [node_id for node_id in node_ids
                if not self.is_loop_node(node_id)]
    
    def filter_loop_nodes(self, node_ids: "list[NodeId]") -> "list[NodeId]":
        return [node_id for node_id in node_ids
                if self.is_loop_node(node_id)]

    ## This creates a new node_id and then creates a mapping from the node and iteration id to this node id
    ## TODO: Currently doesn't work with nested loops
    def create_node_id_with_one_less_loop_from_loop_node(self, node_id: NodeId, loop_id: int) -> NodeId:
        node = self.get_node(node_id)
        logging.debug(f' >>> Node: {node}')
        logging.debug(f' >>> its loops: {node.loop_context} --- {node.current_iters}')

        new_iter = node.get_next_iter(loop_id)
        ## Creates a new node id where we have appended the new iter
        new_node_id = node_id.generate_new_node_id_with_another_iter(new_iter)
        logging.debug(f' >>> new node_id with another iter: {new_node_id}')
        return new_node_id


    ## Returns all non committed non-loop nodes
    def get_all_non_committed_standard_nodes(self) -> "list[NodeId]":
        all_non_committed = self.get_all_non_committed()
        logging.debug(f"All non committed nodes: {all_non_committed}")
        return self.filter_standard_nodes(all_non_committed)

    def get_next(self, node_id:NodeId) -> "list[NodeId]":
        return self.adjacency[node_id][:]

    def get_prev(self, node_id:NodeId) -> "list[NodeId]":
        return self.inverse_adjacency[node_id][:]
        
    def add_edge(self, from_id: NodeId, to_id: NodeId):
        ## KK 2023-05-04 Is it a problem that we append? Maybe we should make that a set
        self.adjacency[from_id].append(to_id)
        self.inverse_adjacency[to_id].append(from_id)
        
    def remove_edge(self, from_id: NodeId, to_id: NodeId):
        self.adjacency[from_id].remove(to_id)
        self.inverse_adjacency[to_id].remove(from_id)        

    def get_transitive_closure(self, target_node_ids:"list[NodeId]") -> "list[NodeId]":
        all_next_transitive = set(target_node_ids)
        next_work = target_node_ids.copy()
        while len(next_work) > 0:
            node_id = next_work.pop()
            successors = set(self.get_next(node_id))
            new_next = successors - all_next_transitive
            all_next_transitive = all_next_transitive.union(successors)
            next_work.extend(new_next)
        return list(all_next_transitive)
    
    def get_inverse_transitive_closure(self, target_node_ids:"list[NodeId]") -> "list[NodeId]":
        all_prev_transitive = set(target_node_ids)
        next_work = target_node_ids.copy()
        while len(next_work) > 0:
            node_id = next_work.pop()
            predecessors = set(self.get_prev(node_id))
            new_prev = predecessors - all_prev_transitive
            all_prev_transitive = all_prev_transitive.union(predecessors)
            next_work.extend(new_prev)
        return list(all_prev_transitive)

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

    def is_frontier(self, node_id: NodeId) -> bool:
        return node_id in self.frontier
    
    def update_rw_set(self, node_id, rw_set):
        self.rw_sets[node_id] = rw_set

    def get_rw_set(self, node_id) -> RWSet:
        return self.rw_sets[node_id]
    
    def get_rw_sets(self) -> dict:
        return self.rw_sets

    def add_to_read_set(self, node_id: NodeId, item: str):
        self.rw_sets[node_id].add_to_read_set(item)

    def add_to_write_set(self, node_id: NodeId, item: str):
        self.rw_sets[node_id].add_to_write_set(item)

    def add_to_waiting_to_be_resolved(self, node_id: NodeId):
        self.waiting_to_be_resolved = self.waiting_to_be_resolved.union([node_id])

    # Check if the specific command can be resolved.
    # KK 2023-05-04 I am not even sure what this function does and why is it useful.
    def cmd_can_be_resolved(self, node_id: int) -> bool:
        logging.debug(f'Checking if node {node_id} can be resolved...')
        ## Get inverse_transitive_closure to find all nodes that are before this one
        inverse_tc_node_ids = self.get_inverse_transitive_closure([node_id])

        ## Out of those nodes, filter out the non-committed ones
        non_committed_nodes_in_inverse_tc = [node_id for node_id in inverse_tc_node_ids
                                                  if not self.is_committed(node_id)]
        logging.debug(f' > Non committed nodes that are predecessors to {node_id} are: {non_committed_nodes_in_inverse_tc}')

        currently_executing_ids = self.get_currently_executing()
        logging.debug(f' > Currently executing: {currently_executing_ids}')

        ## TODO: Make this check more efficient
        for other_node_id in non_committed_nodes_in_inverse_tc:
            ## If one of the non-committed nodes in the inverse_tc is currently executing then
            ## we can't resolve this command
            ## KK 2023-05-04 This is not sufficient. In the future (where we don't speculate everything at once)
            ##               there might be a case where nothing is executing but a command can still not be resolved.
            if other_node_id in currently_executing_ids:
                logging.debug(f' >> Cannot resolve {node_id}: Node {other_node_id} in non committed inverse tc is currently executing')
                return False

            ## If there exists a loop node that is not committed before the command then we cannot resolve.
            if self.is_loop_node(other_node_id):
                logging.debug(f' >> Cannot resolve {node_id}: Node {other_node_id} in non committed inverse tc is a loop node')
                return False

        ## Otherwise we can return
        logging.debug(f' >> Able to resolve {node_id}')
        return True

    def resolve_commands_that_can_be_resolved_and_step_forward(self):
        cmds_to_resolve = self.__pop_cmds_to_resolve_from_waiting_to_be_resolved()
        logging.debug(f"Commands to check for dependencies this round are: {sorted(cmds_to_resolve)}")
        logging.debug(f"Commands that cannot be resolved this round are: {sorted(self.waiting_to_be_resolved)}")
        
        ## Resolve dependencies for the commands that can actually be resolved
        to_commit = self.__resolve_dependencies_continuous_and_move_frontier(cmds_to_resolve)
        if len(to_commit) == 0:
            logging.debug(" > No nodes to be committed this round")
        else:
            logging.debug(f" > Nodes to be committed this round: {to_commit}")
            logging.trace(f"Commit|"+",".join(str(node_id) for node_id in to_commit))
            self.commit_cmd_workspaces(to_commit)
            # self.print_cmd_stderr(stderr)

    def __pop_cmds_to_resolve_from_waiting_to_be_resolved(self):
        cmd_ids_to_check = sorted(list(self.waiting_to_be_resolved))
        logging.debug(f" > Uncommitted commands done executing to be checked: {cmd_ids_to_check}")
        cmds_to_resolve = []
        for cmd_id in cmd_ids_to_check:
            # We check if we can resolve any possible dependencies
            # If we can't, we have to wait for another cycle
            if not self.cmd_can_be_resolved(cmd_id):
                if cmd_id not in self.waiting_to_be_resolved:
                    logging.debug(f" > Adding node {cmd_id} to waiting list")
                    logging.trace(f"WaitingAdd|{cmd_id}")
                    self.waiting_to_be_resolved.add(cmd_id)
                else:
                    logging.debug(f" > Keeping node {cmd_id} to waiting list")
            # If we are in this branch it means that we can resolve the dependencies of the current command
            else:
                cmds_to_resolve.append(cmd_id)
                # We remove the command from the waiting to be resolved set
                if cmd_id in self.waiting_to_be_resolved:
                    logging.debug(f" > Removing node {cmd_id} from waiting list")
                    logging.trace(f"WaitingRemove|{cmd_id}")
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
                    ## We only check for forward dependencies if the first node is not a loop (abstract) node
                    if self.is_loop_node(first_cmd_id):
                        logging.debug(f' > Skipping dependency check with node {first_cmd_id} because it is a loop node')
                        continue
                    if self.has_forward_dependency(first_cmd_id, second_cmd_id):
                        logging.debug(f' > Command {second_cmd_id} was added to the workset, due to a forward dependency with {first_cmd_id}')
                        new_workset.add(second_cmd_id)
        return new_workset

    ## Resolve all the forward dependencies and update the workset
    ## Forward dependency is when a command's output is the same
    ## as the input of a following command
    def __resolve_dependencies_continuous_and_move_frontier(self, cmds_to_resolve):
        self.log_partial_program_order_info()

        logging.debug(f"Commands to be checked for dependencies: {sorted(cmds_to_resolve)}")
        logging.debug(" --- Starting dependency resolution --- ")
        new_workset = self.resolve_dependencies(cmds_to_resolve)
        
        logging.debug(" > Modifying workset accordingly")
        # New workset contains previous unresolved commands and resolved commands with dependencies that have not been stopped
        workset_old = self.workset.copy()
        self.workset = [cmd_id for cmd_id in self.workset if cmd_id not in cmds_to_resolve and cmd_id not in self.stopped]
        self.workset.extend(list(new_workset))
        workset_diff = set(self.workset) - set(workset_old)
        logging.trace(f"WorksetAdd|{','.join(str(cmd_id) for cmd_id in workset_diff)}")

        # Keep the previous committed state
        old_committed = self.get_committed()

        # We want stopped commands to not enter the workset again yet
        assert(set(self.workset).isdisjoint(self.stopped))

        self.step_forward(old_committed)
        # self.log_partial_program_order_info()
        return set(self.get_committed()) - old_committed

    def rerun_stopped(self):
        new_stopped = self.stopped.copy()
        for cmd_id in self.stopped:
            if cmd_id in self.frontier:
                self.workset.append(cmd_id)
                logging.debug(f"Removing {cmd_id} from stopped")
                logging.trace(f"StoppedRemove|{cmd_id}")
                new_stopped.remove(cmd_id)
                # We remove any to-check-for-dependency nodes as the stopped node will execute in frontier
                self.to_be_resolved[cmd_id] = []
        self.stopped = new_stopped

    ## This method checks if nid1 would be before nid2 if nid2 was part of the PO.
    ##
    ## Therefore it does not just check edges, but rather computes if it would be before
    ##  based on ids and loop iterations.
    ##
    ## 1. Check if the loop ids of the two abstract parents of both nodes differ 
    ##     thus showing that one is before the other 
    ## 2. If all loop ids are the same, now we can actually compare iterations.
    ##     If a node is in the same loop ids but in a later iteration then it is later.
    ## 3. If all iterations are the same too, then we just compare node ids
    ##
    ## KK 2023-05-22 This is a complex procedure, I wonder if we can simplify it in some way
    def hypothetical_before(self, nid1: NodeId, nid2: NodeId):
        raw_id1 = nid1.get_non_iter_id()
        ## Get all loop ids that nid1 could be in
        loop_ids1 = self.get_node_loop_context(raw_id1)

        raw_id2 = nid1.get_non_iter_id()
        ## Get all loop ids that nid2 could be in
        loop_ids2 = self.get_node_loop_context(raw_id2)

        i = 0
        while i < len(loop_ids1) and i < len(loop_ids2):
            loop_id_1 = loop_ids1.get(len(loop_ids1) - 1 - i)
            loop_id_2 = loop_ids2.get(len(loop_ids2) - 1 - i)
            ## If the first node is in a previous loop than the second,
            ##  then we are done.
            if loop_id_1 < loop_id_2:
                return True
            elif loop_id_1 > loop_id_2:
                return False

            ## We need to keep going
            i += 1

        ## If we reach this, we know that both nodes are in the same loops up to i 
        ##  so we now compare iterations and node identifiers.

        iters1 = nid1.get_iters()
        iters2 = nid2.get_iters()

        i = 0
        while i < len(iters1) and i < len(iters2):
            iter1 = iters1.get(len(iters1) - 1 - i)
            iter2 = iters2.get(len(iters2) - 1 - i)
            ## If the first node is in a previous iteration than the second,
            ##  then we are done.
            if iter1 < iter2:
                return True
            elif iter1 > iter2:
                return False
            ## We need to keep going
            i += 1

        ## We now know that their common prefix of iterations is the same

        ## Check if the node could potentially generate other nodes that are bigger
        ##  i.e., if it is more abstract. If so, then it is not smaller.
        common_loop_depth = min(len(loop_ids1), len(loop_ids2))
        abstract_depth1 = max(common_loop_depth - len(iters1), 0)
        abstract_depth2 = max(common_loop_depth - len(iters2), 0)
        if abstract_depth1 < abstract_depth2:
            return True
        elif abstract_depth1 > abstract_depth2:
            return False

        return nid1.id < nid2.id


    def progress_po_due_to_wait(self, node_id: NodeId):
        logging.debug(f"Checking if we can progress the partial order after having received a wait for {node_id}")
        ## The node might not be part of the partial order if it corresponds to
        ##  a loop node iteration. In this case, we just need to make sure that
        ##  we commit the right previous loop nodes that are relevant to it.
        if not self.is_node_id(node_id):
            ## TODO: This check is not correct currently, it works for now, but when we move to full partial orders it wont anymore,
            ##        due to the check happening with < in hypothetical before
            logging.debug(f" > Node {node_id} is not part of the PO so we compute the nodes that would be before it...")
            all_non_committed = self.get_all_non_committed()
            all_non_committed_loop_nodes = self.filter_loop_nodes(all_non_committed)
            non_committed_loop_nodes_that_would_be_predecessors = [n_id for n_id in all_non_committed_loop_nodes
                                                                   if self.hypothetical_before(n_id, node_id)]
            
            new_committed_nodes = non_committed_loop_nodes_that_would_be_predecessors

        else:
            logging.debug(f" > Node {node_id} is part of the PO so we just check its predecessors following the inverse edges...")
            ## If the node is in the PO, then we can proceed normally and find its predecessors and commit them

            ## Get inverse_transitive_closure to find all nodes that are before this one
            inverse_tc_node_ids = self.get_inverse_transitive_closure([node_id])

            ## Out of those nodes, filter out the non-committed loop ones
            non_committed_loop_nodes_in_inverse_tc = [node_id for node_id in inverse_tc_node_ids
                                                    if not self.is_committed(node_id) and
                                                    self.is_loop_node(node_id)]
            logging.debug(f'Non committed loop nodes that are predecessors to {node_id} are: {non_committed_loop_nodes_in_inverse_tc}')
            
            new_committed_nodes = non_committed_loop_nodes_in_inverse_tc

        ## And "close them"
        ## TODO: This is a hack here, we need to have a proper method that commits
        ##       nodes and does whatever else is needed to do (e.g., add new nodes to frontier)
        logging.debug(f'Adding following loop nodes to committed: {new_committed_nodes}')
        for node_id in new_committed_nodes:
            self.commit_node(node_id)
        
        ## Since we committed some nodes, let's make sure that we also push the frontier
        ## TODO: Can we do this in a less hacky method? By using a well-defined commit_node_and_push_frontier method?
        if len(new_committed_nodes) > 0:
            new_nodes_sinks = self.get_sub_po_sink_nodes(new_committed_nodes)
            assert(len(new_nodes_sinks) == 1)
            new_nodes_sink = new_nodes_sinks[0]
            logging.debug(f'The sink of the newly committed loop nodes is {new_nodes_sink}')

            next_nodes = self.get_next(new_nodes_sink)
            next_standard_nodes = self.filter_standard_nodes(next_nodes)
            logging.trace(f"Adding its next nodes to the frontier|{','.join(str(node_id) for node_id in next_standard_nodes)}")
            self.frontier.extend(next_standard_nodes)



        ## TODO: Add some form of validity assertion after we are done with this.
        ##       Just to make sure that we haven't violated the continuity of the committed set.
        
        ## We check if something can be resolved and stepped forward here
        ## KK 2023-05-10 This seems to work for all tests (so it might be idempotent
        ##                since in many tests there is nothing new to resolve after a wait)
        self.resolve_commands_that_can_be_resolved_and_step_forward()

    ## When the frontend sends a wait for a node, it means that execution in the frontend has
    ## already surpassed all nodes prior to it. This is particularly important for loops, 
    ## since we can't always statically predict how many iterations they will do, so the only
    ## definitive way to know that they are done is to receive a wait for a node after them.
    def wait_received(self, node_id: NodeId):
        ## Whenever we receive a wait for a node, we always need to check and "commit" all prior loop nodes
        ##   since we know that they won't have any more iterations (the JIT frontend has already passed them).
        
        ## We first have to push and progress the PO due to the wait and then unroll
        ## KK 2023-05-22 Currently this checks whether a still nonexistent node is
        ##               would be a successor of existing nodes to commit some of 
        ##               them if needed. Unfortunately, to make this check for a non-existent
        ##               node is very complex and not elegant. 
        ## TODO: Could we swap unrolling and progressing so that we always 
        ##        check if a node can be progressed by checking edges?
        self.progress_po_due_to_wait(node_id)

        ## Unroll some nodes if needed.
        if node_id.has_iters():
            ## TODO: This unrolling can also happen and be moved to speculation.
            ##       For now we are being conservative and that is why it only happens here
            ## TODO: Move this to the scheduler.schedule_work() (if we have a loop node waiting for response and we are not unrolled, unroll to create work)
            self.maybe_unroll(node_id)


    def find_outer_loop_sub_partial_order(self, loop_id: int, nodes_subset: "list[NodeId]") -> "list[NodeId]":
        loop_node_ids = []
        for node_id in nodes_subset:
            loop_context = self.get_node_loop_context(node_id)
            ## Note: this only checks for the nodes that have this loop id as their outer loop
            if not loop_context.is_empty() and loop_id == loop_context.get_outer():
                loop_node_ids.append(node_id)
        ## TODO: Assert that this is closed w.r.t. partial order
        return loop_node_ids


    ## This function unrolls a single loop, by first finding all its nodes (they must be contiguous) and then creating new versions of them
    ## that are concretized. Its second argument describes which subset of all partial order nodes we want to look at.
    ## That is necessary because when unrolling nested loops, we might end up in a situation where we have unrolled the
    ## outer loop, but some of the newly created nodes might still be loop nodes (so we might have loop nodes for the same loop in multiple locations).
    def unroll_single_loop(self, loop_id: int, nodes_subset: "list[NodeId]"):
        logging.info(f'Unrolling loop with id: {loop_id}')
        all_loop_node_ids = self.find_outer_loop_sub_partial_order(loop_id, nodes_subset)
        
        ## We don't want to unroll already committed nodes
        loop_node_ids = [nid for nid in all_loop_node_ids
                         if not self.is_committed(nid)]

        logging.debug(f'Node ids for loop: {loop_id} are: {loop_node_ids}')
        
        ## Create the new nodes and remap adjacencies accordingly
        node_mappings = {}
        for node_id in loop_node_ids:
            node = self.get_node(node_id)
            new_loop_node_id = self.create_node_id_with_one_less_loop_from_loop_node(node_id, loop_id)
            node_mappings[node_id] = new_loop_node_id
            ## The new node has one less loop context than the previous one
            node_loop_contexts = node.get_loop_context()
            logging.debug(f'Node: {node_id} loop_contexts: {node_loop_contexts}')
            assert(node_loop_contexts.get_outer() == loop_id)
            new_node_loop_contexts = copy.deepcopy(node_loop_contexts)
            new_node_loop_contexts.pop_outer()

            ## Create the new node
            self.nodes[new_loop_node_id] = Node(new_loop_node_id, node.cmd, node.asts, new_node_loop_contexts)
            self.executions[new_loop_node_id] = 0
        logging.debug(f'New loop ids: {node_mappings}')

        ## Create the new adjacencies, by mapping adjacencies in the node set to the new node ids
        ## and leaving outside adjacencies as they are
        for _, new_node_id in node_mappings.items():
            self.adjacency[new_node_id] = []

        for node_id, new_node_id in node_mappings.items():
            old_prev_ids = self.get_prev(node_id)
            ## Modify all id to be in the new set except for the 
            new_prev_ids = PartialProgramOrder.map_using_mapping(old_prev_ids, node_mappings)
            self.inverse_adjacency[new_node_id] = new_prev_ids
            for new_prev_id in new_prev_ids:
                self.adjacency[new_prev_id].append(new_node_id)

        ## TODO: The rest of the code here makes assumptions about the shape of the partial order

        ## Modify the previous node of the loop nodes
        new_nodes_sinks = self.get_sub_po_sink_nodes(list(node_mappings.values()))
        assert(len(new_nodes_sinks) == 1)
        new_nodes_sink = new_nodes_sinks[0]
        logging.debug(f'The sink of the new iteration for loop: {loop_id} is {new_nodes_sink}')

        old_nodes_sources = self.get_sub_po_source_nodes(list(node_mappings.keys()))
        assert(len(old_nodes_sources) == 1)
        old_nodes_source = old_nodes_sources[0]

        old_next_node_ids = self.get_next(new_nodes_sink)
        assert(len(old_next_node_ids) <= 1)

        previous_ids = self.get_sub_po_prev_nodes(loop_node_ids)
        assert(len(previous_ids) <= 1)

        ## Add a new edge between the new_sink (concrete iter) and the old_source (loop po)
        self.add_edge(new_nodes_sink, old_nodes_source)

        ## Remove the old previous edge of the old_source if it exists
        if len(previous_ids) == 1:
            previous_id = previous_ids[0]
            logging.debug(f'Previous node id for loop: {loop_id} is {previous_id}')
            self.remove_edge(from_id=previous_id,
                             to_id=old_nodes_source)


        ## Return the new first node and all node mappings
        return node_mappings[old_nodes_source], node_mappings.values()

    ## Static method that just maps using a node mapping dictionary or leaves them as
    ## they are if not
    def map_using_mapping(node_ids: "list[NodeId]", mapping) -> "list[NodeId]":
        new_node_ids = []
        for node_id in node_ids:
            if node_id in mapping:
                new_id = copy.deepcopy(mapping[node_id])
            else:
                new_id = copy.deepcopy(node_id)
            new_node_ids.append(new_id)
        return new_node_ids

    ## This unrolls a sequence of loops by unrolling each loop outside-in
    def unroll_loops(self, loop_contexts: LoopStack) -> NodeId:
        logging.debug(f'Unrolling the following loops: {loop_contexts}')

        ## All new node_ids
        all_new_node_ids = set()
        relevant_node_ids = list(self.nodes.keys())
        for loop_ctx in loop_contexts.outer_to_inner():
            new_first_node_id, new_node_ids = self.unroll_single_loop(loop_ctx, relevant_node_ids)
            logging.debug(f'New node ids after unrolling: {new_node_ids}')
            ## Update all new nodes that we have added
            all_new_node_ids.update(new_node_ids)

            ## Re-set the relevant node ids to only the new nodes (if we unrolled a big loop once, 
            ##  we just want to look at those new unrolled nodes for the next unrolling).
            relevant_node_ids = new_node_ids

            logging.debug(f' >>> Edges after unrolling    : {self.adjacency}')
            logging.debug(f' >>> Inv Edges after unrolling: {self.inverse_adjacency}')

        ## Add all new standard nodes to the workset (since they have to be tracked)
        for new_node_id in all_new_node_ids:
            if not self.is_loop_node(new_node_id):
                self.workset.append(new_node_id) 

        ## KK 2023-05-22 Do we need to correctly populate the resolved set of next commands
        ##               after unrolling the loop.

        return new_first_node_id

    ## This unrolls a loop given a target concrete node id
    def unroll_loop_node(self, target_concrete_node_id: NodeId):
        raw_node_id = target_concrete_node_id.get_non_iter_id()
        assert(self.is_loop_node(raw_node_id))

        logging.debug(f'Edges: {self.adjacency}')

        ## Find the closest non-committed successor with this node id
        ## Note: This is necessary because we might need to unroll only a subset of the loops that a node is part of.
        ##       This is relevant when we have nested loops.
        all_non_committed = self.get_all_non_committed()
        all_non_committed_loop_nodes = self.filter_loop_nodes(all_non_committed)
        logging.debug(f'All non committed loop nodes: {all_non_committed_loop_nodes}')
        source_node_ids = self.get_min(all_non_committed_loop_nodes)
        ## Note: This assertion might not hold once we have actual partial orders
        assert(len(source_node_ids) == 1)
        node_id = source_node_ids[0]
        logging.debug(f'Closest non-committed loop node successor with raw_id {raw_node_id} is: {node_id}')
        loop_contexts = self.get_node_loop_context(node_id)


        ## Unroll all loops that this node is in
        new_first_node_id = self.unroll_loops(loop_contexts)

        ## TODO: This needs to change when we modify unrolling to happen speculatively too
        ## TODO: This needs to properly add the node to frontier and to resolve dictionary
        self.step_forward(self.get_committed())
        self.frontier.append(new_first_node_id)

        ## At the end of unrolling the target node must be part of the PO
        assert(self.is_node_id(target_concrete_node_id))


    def maybe_unroll(self, node_id: NodeId) -> NodeId:
        ## Only unrolls this node if it doesn't already exist in the PO
        if not self.is_node_id(node_id):
            self.unroll_loop_node(node_id)

        ## The node_id must be part of the PO after unrolling, otherwise we did something wrong
        assert(self.is_node_id(node_id))

    ## KK 2023-09-05 @Giorgo Do all of these steps need to be done at once, or are these methods
    ##               meaningful even if called one by one? In general, I would like there to
    ##               be a clear set of 1-3 methods that are supposed to be used whenever we
    ##               add some new nodes (or progress the PO in some way) that will step it properly,
    ##               while being idempotent (if they are called multiple times nothing goes wrong).
    ##
    ##               Internal functions on the other hand (ones that cannot be called on their own
    ##                since they might leave the PO in a partial state) should be prefixed with an
    ##               underscore.
    ##
    ##               All top-level functions should get minimal arguments (none if possible)
    ##               and should just get their relevant state from the fields of the PO.
    ## TODO: step_forward seems to be an internal function
    def step_forward(self, old_committed):
        self.frontier_commit_and_push()
        self.rerun_stopped()
        self.populate_to_be_resolved_dict(old_committed)

    ## Pushes the frontier forward as much as possible for all commands in it that can be committed
    def frontier_commit_and_push(self):
        logging.debug(" > Commiting and pushing frontier")
        logging.debug(f' > Frontier: {self.frontier}')
        changes_in_frontier = True
        while changes_in_frontier:
            new_frontier = []
            changes_in_frontier = False
            # Second condition below may be unecessary
            for frontier_node in self.frontier:
                ## If a node is not in the workset it means that it is actually done executing
                ## KK 2023-05-10 Do we need all these conditions in here? Some might be redundant?
                if frontier_node not in self.get_currently_executing() \
                    and frontier_node not in self.get_committed() \
                    and frontier_node not in self.stopped \
                    and frontier_node not in self.waiting_to_be_resolved \
                    and frontier_node not in self.workset\
                    and not self.is_loop_node(frontier_node):
                    ## Commit the node
                    self.commit_node(frontier_node)

                    ## Add its non-loop successors to the frontier
                    next_nodes = self.get_next(frontier_node)
                    next_standard_nodes = self.filter_standard_nodes(next_nodes)
                    logging.trace(f"FrontierAdd|{','.join(str(node_id) for node_id in next_standard_nodes)}")
                    new_frontier.extend(next_standard_nodes)

                    ## There are some changes in the frontier so we need to reenter the loop
                    changes_in_frontier = True
                # If node is still being executed, we cannot progress further
                else:
                    new_frontier.extend([frontier_node])
                    logging.trace(f" > Not commiting node {frontier_node}, readding to frontier")

            ## Update the frontier to the new frontier
            self.frontier = new_frontier
    

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
                    logging.debug(f' > File forward dependency found C1:({dir}) C2:({other_path})')
                    return True
        return False
    
    def is_subpath(self, dir, other_path):
        other_path.startswith(os.path.abspath(dir)+os.sep)

    def has_forward_dependency(self, first_id, second_id):
        first_write_set = set(self.rw_sets[first_id].get_write_set())
        second_read_set = set(self.rw_sets[second_id].get_read_set())
        logging.debug(f'Checking dependencies between {first_id} and {second_id}')
        if not first_write_set.isdisjoint(second_read_set):
            logging.debug(f' > Forward dependency found {first_write_set.intersection(second_read_set)}')
            return True

        elif self.has_dir_file_dependency(first_write_set, second_read_set):
            return True
        else:
            logging.debug(f' > No dependencies')
            return False

    ## TODO: Eventually, in the future, let's add here some form of limit
    def schedule_work(self, limit=0):
        # self.log_partial_program_order_info()
        logging.debug("Scheduling work...")
        ## KK 2023-05-04 Is it a problem if we do that here?
        # self.step_forward(copy.deepcopy(self.committed))

        ## TODO: Move loop unrolling here for speculation too

        self.run_all_frontier_cmds()
        self.schedule_all_workset_non_frontier_cmds()
        assert(self.valid())

    def schedule_all_workset_non_frontier_cmds(self):
        non_frontier_ids = [node_id for node_id in self.get_workset() 
                            if not self.is_frontier(node_id)]
        for cmd_id in non_frontier_ids:
            # We also need for a cmd to not be waiting to be resolved.
            if not cmd_id in self.commands_currently_executing and \
               not cmd_id in self.waiting_to_be_resolved:
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
                if cmd_id in self.stopped:
                    self.stopped.remove(cmd_id)
                    logging.trace(f"StoppedRemove|{cmd_id}")
                    # We remove any to-check-for-dependency nodes as the stopped node will execute in frontier
                    self.to_be_resolved[cmd_id] = []
                self.run_cmd_non_blocking(cmd_id)

    ## Run a command and add it to the dictionary of executing ones
    def run_cmd_non_blocking(self, node_id: NodeId):
        ## A command should only be run if it's in the frontier, otherwise it should be spec run
        assert(self.is_frontier(node_id))
        logging.trace(f'Running command: {node_id} {self.get_node(node_id)}')
        logging.trace(f"ExecutingAdd|{node_id}")
        self.execute_cmd_core(node_id, speculate=False)

    ## Run a command and add it to the dictionary of executing ones
    def speculate_cmd_non_blocking(self, node_id: NodeId):
        logging.debug(f'Speculating command: {node_id} {self.get_node(node_id)}')
        ## TODO: Since these (this and the function above)
        ##       are relevant for the report maker,
        ##       add them in some library (e.g., trace_for_report) 
        ##       so that we don't accidentally delete them.
        logging.trace(f"ExecutingSandboxAdd|{node_id}")
        self.execute_cmd_core(node_id, speculate=True)

    def execute_cmd_core(self, node_id: NodeId, speculate=False):
        node = self.get_node(node_id)
        ## TODO: Read and pass the actual variables in this
        variables = {}
        is_safe = analysis.safe_to_execute(node.asts, variables)
        if not is_safe:
            logging.debug(f'Command: "{node}" is not safe to execute, sending to the original shell to execute...')
            ## TODO: Implement the mechanism that runs the command in the original shell
        cmd = node.get_cmd()
        self.executions[node_id] += 1
        if speculate:
            execute_func = executor.async_run_and_trace_command_return_trace_in_sandbox
        else:
            execute_func = executor.async_run_and_trace_command_return_trace
        proc, trace_file, stdout, stderr, variable_file = execute_func(cmd, node_id)
        logging.debug(f'Read trace from: {trace_file}')
        self.commands_currently_executing[node_id] = (proc, trace_file, stdout, stderr, variable_file)

    def command_execution_completed(self, node_id: NodeId, riker_exit_code:int, sandbox_dir: str):
        logging.debug(f" --- Node {node_id}, just finished execution ---")
        self.sandbox_dirs[node_id] = sandbox_dir
        ## TODO: Store variable file somewhere so that we can return when wait
        _proc, trace_file, stdout, stderr, variable_file = self.commands_currently_executing.pop(node_id)
        logging.trace(f"ExecutingRemove|{node_id}")
        # Handle stopped by riker due to network access
        if int(riker_exit_code) == 159:
            logging.debug(f" > Adding {node_id} to stopped because it tried to access the network.")
            logging.trace(f"StoppedAdd|{node_id}:network")
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
            logging.trace(f"StoppedAdd|{node_id}:error")
            self.stopped.add(node_id)
        else:

            read_set, write_set = trace.parse_and_gather_cmd_rw_sets(trace_object)
            rw_set = RWSet(read_set, write_set)
            self.update_rw_set(node_id, rw_set)

        ## Now that command `node_id` is done executing, we can check which other commands
        ## can be resolved (that might have finished execution before but where waiting on `node_id`)
        logging.debug(f"Finding sets of commands that can be resolved after {node_id} finished executing")
        if node_id in self.stopped:
            logging.debug(f"Nothing new to be resolved since {node_id} exited with an error.")
            if node_id in self.workset:
                self.workset.remove(node_id)
                logging.trace(f"WorksetRemove|{node_id}")
            # If no commands can be resolved this round, 
            # do nothing and wait until a new command finishes executing
            logging.debug("No resolvable nodes were found in this round, nothing will change...")
            return

        assert(node_id not in self.stopped)
        ## Since the command properly finished executing, it now waits to be resolved
        self.add_to_waiting_to_be_resolved(node_id)
        ## We can now call the general resolution method that determines which commands
        ## can be resolved (all their dependencies are done executing), and resolves them.
        self.resolve_commands_that_can_be_resolved_and_step_forward()
        assert(self.valid())

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
        logging.debug(f"COMMITTED:      {self.get_committed_list()}")
        logging.debug(f"FRONTIER:       {self.get_frontier()}")
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
            if self.is_committed(node_id):
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
                relevant_committed = self.get_committed()
                if node_id not in relevant_committed:
                    to_add = self.get_prev(node_id).copy()
                    traversal = to_add.copy()
                    to_be_resolved_nodes_ids = to_add.copy()
                while len(traversal) > 0:
                    current_node_id = traversal.pop(0)
                    if current_node_id not in relevant_committed:
                        to_add = self.get_prev(current_node_id)
                        to_be_resolved_nodes_ids.extend(to_add)
                        traversal.extend(to_add)
                self.to_be_resolved[node_id] = to_be_resolved_nodes_ids.copy()
                self.to_be_resolved[node_id] = list(set(self.to_be_resolved[node_id]) - set(relevant_committed))
                logging.debug(f' |> New to be resolved set: {self.to_be_resolved[node_id]}')

    def get_currently_executing(self) -> list:
        return sorted(list(self.commands_currently_executing.keys()))
    
    ## KK 2023-05-02 What does this function do?
    def save_commit_state_of_cmd(self, cmd_id):
        self.committed_order.append(cmd_id)
        self.commit_state[cmd_id] = set(self.get_committed()) - set(self.to_be_resolved[cmd_id])

    def log_committed_cmd_state(self):
        logging.info("---------- Committed Order -----------")
        logging.info(" " + " -> ".join(map(str, self.committed_order)))
        logging.info("---------- Committed State -----------")
        for cmd in sorted(self.get_committed_list()):
            if len(self.commit_state[cmd]) == 0:
                logging.info(f" CMD {cmd} on\t\tSTART")
            else:
                logging.info(f" CMD {cmd} after:\t{', '.join(map(str, self.commit_state[cmd]))}")

    def log_executions(self):
        logging.debug("---------- (Re)executions ------------")
        for cmd in sorted(self.get_committed_list()):
            logging.debug(f" CMD {cmd} executed {self.executions[cmd]} times")
            logging.trace(f"Executions|{cmd}|{self.executions[cmd]}")
        logging.debug(f" Total (re)executions: {sum(list(self.executions.values()))}")
        logging.debug("--------------------------------------")


## TODO: Try to move those to PaSh and import them here
def parse_cmd_from_file(file_path: str) -> "tuple[str,list[AstNode]]":
    logging.debug(f'Parsing: {file_path}')
    with open(file_path) as f:
        cmd = f.read()
    asts = analysis.parse_shell_to_asts(file_path)
    return cmd, asts

def parse_edge_line(line: str) -> "tuple[int, int]":
    from_str, to_str = line.split(" -> ")
    return (int(from_str), int(to_str))

def parse_loop_context_line(line: str) -> "tuple[int, list[int]]":
    node_id, loop_contexts_raw = line.split("-loop_ctx-")
    if loop_contexts_raw != "":
        loop_contexts_str = loop_contexts_raw.split(",")
        loop_contexts = [int(loop_ctx) for loop_ctx in loop_contexts_str]
    else:
        loop_contexts = []
    return int(node_id), loop_contexts

def parse_loop_contexts(lines):
    loop_contexts = {}
    for line in lines:
        node_id, loop_ctx = parse_loop_context_line(line)
        loop_contexts[node_id] = loop_ctx

    return loop_contexts

def parse_partial_program_order_from_file(file_path: str) -> PartialProgramOrder:
    with open(file_path) as f:
        raw_lines = f.readlines()
    
    ## Filter comments and remove new lines
    lines = [line.rstrip() for line in raw_lines
             if not line.startswith("#")]

    ## The directory in which cmd_files are
    cmds_directory = str(lines[0])
    logging.debug(f'Cmds are stored in: {cmds_directory}')

    ## The number of nodes
    number_of_nodes = int(lines[1])
    logging.debug(f'Number of po cmds: {number_of_nodes}')

    ## The loop context for each node
    loop_context_start=2
    loop_context_end=number_of_nodes+2
    loop_context_lines = lines[loop_context_start:loop_context_end]
    loop_contexts = parse_loop_contexts(loop_context_lines)
    logging.debug(f'Loop contexts: {loop_contexts}')

    ## The rest of the lines are edge_lines
    edge_lines = lines[loop_context_end:]
    logging.debug(f'Edges: {edge_lines}')

    nodes = {}
    for i in range(number_of_nodes):
        file_path = f'{cmds_directory}/{i}'
        cmd, asts = parse_cmd_from_file(file_path)
        loop_ctx = loop_contexts[i]
        nodes[NodeId(i)] = Node(NodeId(i), cmd, 
                                asts=asts, 
                                loop_context=LoopStack(loop_ctx))

    edges = {NodeId(i) : [] for i in range(number_of_nodes)}
    for edge_line in edge_lines:
        from_id, to_id = parse_edge_line(edge_line)
        edges[NodeId(from_id)].append(NodeId(to_id))
    
    logging.trace(f"Nodes|{','.join([str(node) for node in nodes])}")
    logging.trace(f"Edges: {edges}")
    return PartialProgramOrder(nodes, edges)
