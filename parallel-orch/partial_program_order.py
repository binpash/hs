import copy
from node import LoopStack, NodeId, ConcreteNode, AbstractNode
import logging
from collections import deque

PROG_LOG = '[PROG_LOG] '
EVENT_LOG = '[EVENT_LOG] '
DEBUG_LOG = '[DEBUG_LOG] '

def event_log(s):
    logging.info(EVENT_LOG + s)

def progress_log(s):
    logging.info(PROG_LOG + s)

def debug_log(s):
    logging.debug(DEBUG_LOG + s)
    
class PartialProgramOrder:
    frontier: set  # Set of nodes at the frontier
    # Di: I'm going to ignore this for now and implement the feature without a local data structure
    # Later we can add this back as a caching mechanism to avoid doing RWSet
    # intersections of files all the time
    # run_after: "dict[NodeId, list[ConcreteNode]]"  # Nodes that should run after certain conditions
    to_be_resolved: "dict[NodeId, list[ConcreteNode]]"  # Mapping of nodes to lists of uncommitted nodes
    nodes: "dict[NodeId, ConcreteNode]"
    adjacency: "dict[NodeId, list[NodeId]]"
    abstract_adjacency: "dict[NodeId, list[NodeId]]"
    inverse_adjacency: "dict[NodeId, list[NodeId]]"
    
    def __init__(self, nodes: "dict[NodeId, ConcreteNode]", edges: "dict[NodeId, list[NodeId]]"):
        self.abstract_nodes = nodes
        self.abstract_adjacency = edges
        self.abstract_inverse_adjacency = self.init_abstract_inverse_adjacency()
        self.nodes = {}
        self.adjacency = {}
        self.inverse_adjacency = {}
        self.frontier = set()
        # self.run_after = {}
        self.to_be_resolved = {}

    def init_partial_order(self):
        
        self.concretize_abstract_plain_nodes_until_loops()
        for node_id, node in self.nodes.items():
            if node.is_initialized():
                node.transition_from_init_to_ready()

        self.init_to_be_resolved_dict()
        logging.info(self.to_be_resolved)
        # Init frontier
        self.frontier = self.get_standard_source_nodes()
        # TODO: Implement the rest of the partial order initialization



    def commit_node(self, node):
        # Logic to handle committing a node
        node.transition_to_committed()
        # Maybe update dependencies here 
        # etc.

    def init_abstract_inverse_adjacency(self):
        abstract_inverse_adjacency = {i: [] for i in self.abstract_nodes.keys()}
        for from_id, to_ids in self.abstract_adjacency.items():
            for to_id in to_ids:
                abstract_inverse_adjacency[to_id].append(from_id)
        return abstract_inverse_adjacency
    
    def get_node(self, node_id: NodeId) -> ConcreteNode:
        return self.nodes[node_id]

    def get_all_nodes(self):
        return [node for node in self.nodes.values()]
    
    def get_committed_nodes(self):
        return [node for node in self.nodes.values() if node.is_committed()]
    
    def get_ready_nodes(self):
        return [node for node in self.nodes.values() if node.is_ready()]
    
    def get_executing_nodes(self):
        return [node for node in self.nodes.values() if node.is_executing()]
    
    def get_spec_executing_nodes(self):
        return [node for node in self.nodes.values() if node.is_spec_executing()]
    
    def get_executing_normal_and_spec_nodes(self):
        return [node for node in self.nodes.values() if node.is_executing() or node.is_spec_executing()]
    
    def get_speculated_nodes(self):
        return [node for node in self.nodes.values() if node.is_speculated()]
    
    def get_uncommitted_nodes(self):
        return [node for node in self.nodes.values() if not node.is_committed()]
    
    def get_frontier(self):
        return self.frontier
    
    def log_info(self):
        logging.info(f"Nodes: {self.nodes}")
        logging.info(f"Adjacency: {self.adjacency}")
        logging.info(f"Inverse adjacency: {self.inverse_adjacency}")
        self.log_state()

    def log_state(self):
        for node in self.nodes.values():
            progress_log(node.pretty_state_repr())
        progress_log('')

    def get_schedulable_nodes(self) -> list[NodeId]:
        return [node.id_ for node in self.get_ready_nodes()]
            
    ## Returns the next non-committed normal node
    def progress_frontier(self) -> "list[NodeId]":
        return self.get_next_frontier_nodes(self.get_frontier())

    def get_next_nodes(self, node_id:NodeId) -> "list[NodeId]":
        return self.adjacency[node_id][:]

    def get_prev_nodes(self, node_id:NodeId) -> "list[NodeId]":
        return self.inverse_adjacency[node_id][:]
    
    def get_source_nodes(self) -> "list[NodeId]":
        sources = set()
        for to_id, from_ids in self.inverse_adjacency.items():
            if len(from_ids) == 0:
                sources.add(to_id)
        return list(sources)
    
    def get_standard_source_nodes(self) -> list:
        source_nodes = self.get_source_nodes()
        # TODO: Filter out loop nodes
        # return self.filter_standard_nodes(source_nodes)
        return source_nodes    

    def get_next_frontier_nodes(self, start_nodes: "list[NodeId]") -> "set[int]":
        # TODO: filter non-loop nodes
        visited = set()
        to_visit = [(node_id, 0) for node_id in start_nodes]  # Pair each start node with depth 0
        non_committed_nodes = set()
        first_non_committed_depth = None

        while to_visit:
            current_node_id, depth = to_visit.pop()
            if current_node_id in visited:
                continue

            visited.add(current_node_id)
            current_node = self.nodes.get(current_node_id)

            if not current_node.is_committed():
                if first_non_committed_depth is None:
                    first_non_committed_depth = depth
                elif depth > first_non_committed_depth:
                    # Do not consider nodes deeper than the first non-committed depth
                    continue

                non_committed_nodes.add(current_node_id)

            if first_non_committed_depth is None or depth < first_non_committed_depth:
                next_nodes = self.get_next_nodes(current_node_id)  # Use the provided method to get next nodes
                for neighbor in next_nodes:
                    if neighbor not in visited:
                        to_visit.append((neighbor, depth + 1))  # Increase depth for neighbors

        return non_committed_nodes
    
    def get_all_next(self, current_node_id: NodeId, visited=None) -> "set[NodeId]":
        all_next = set()
        def reachable_rec(cur, reachable):
            if cur in reachable:
                return
            reachable.add(cur)
            for n in self.get_next_nodes(cur):
                reachable_rec(n, reachable)
        for n in self.get_next_nodes(current_node_id):
            reachable_rec(n, all_next)
        return all_next


    def get_all_previous(self, current_node_id: NodeId, visited=None) -> "set[NodeId]":
        all_prev = set()
        def reachable_rec(cur, reachable):
            if cur in reachable:
                return
            reachable.add(cur)
            for n in self.get_prev_nodes(cur):
                reachable_rec(n, reachable)
        for n in self.get_prev_nodes(current_node_id):
            reachable_rec(n, all_prev)
        return all_prev
    
    def get_all_next_uncommitted(self, node_id: NodeId) -> "set[NodeId]":
        next = self.get_all_next(node_id)
        return set([node for node in next if not self.nodes[node].is_committed()])
    
    def get_all_previous_uncommitted(self, node_id: NodeId) -> "set[NodeId]":
        previous = self.get_all_previous(node_id)
        return set([node for node in previous if not self.nodes[node].is_committed()])

    def adjust_to_be_resolved_dict_entry(self, node_id: NodeId):
        node = self.nodes.get(node_id)
        if node.is_committed():
            self.to_be_resolved[node_id] = []
        elif node.is_ready():
            self.to_be_resolved[node_id] = self.get_all_previous_uncommitted(node_id)

    def init_to_be_resolved_dict(self):
        for node_id in self.nodes:
            self.adjust_to_be_resolved_dict_entry(node_id)

    def adjust_to_be_resolved_dict(self):
        # TODO: this design seems to require the function to be called
        # each time before a node entering EXECUTING or SPEC_EXECUTING
        # to be optimal (that is, it might keep more things in the list).
        # It's safe as is so I'm not touching it.
        for node_id in self.to_be_resolved.keys():
            self.adjust_to_be_resolved_dict_entry(node_id)

    #TODO: Add partial order invariant checks
    def valid(self):
        return True

    def fetch_fs_actions(self):
        for node in self.get_executing_normal_and_spec_nodes():
            node.gather_fs_actions()
            
    def _has_fs_deps(self, node_id: NodeId):
        node_of_interest : ConcreteNode = self.get_node(node_id)
        for nid in self.to_be_resolved[node_id]:
            node: ConcreteNode = self.get_node(nid)
            if node.get_rw_set().has_conflict(node_of_interest.get_rw_set()):
                return True
        return False

    # TODO: It's currently designed this way to avoid reading trace file all the time
    # When we have complex caching code for this we can make this go away
    def has_fs_deps(self, node_id:NodeId):
        self.fetch_fs_actions()
        self._has_fs_deps(node_id)
    
    ### external handler events ###
    
    def schedule_work(self, node_id: NodeId, env_file: str):
        event_log("schedule_work")
        self.get_node(node_id).start_executing(env_file)

    def schedule_spec_work(self, node_id: NodeId, env_file: str):
        event_log("schedule_spec")
        self.adjust_to_be_resolved_dict_entry(node_id)
        self.get_node(node_id).start_spec_executing(env_file)
    
    def handle_complete(self, node_id: NodeId, has_pending_wait: bool,
                        current_env: str):
        event_log(f"handle_complete {node_id}")
        node = self.get_node(node_id)
        # TODO: complete the state matching
        if node.is_executing():
            node.commit_frontier_execution()
            self.adjust_to_be_resolved_dict()
        elif node.is_spec_executing():
            if self.has_fs_deps(node_id):
                node.reset_to_ready()
                # otherwise it stays in ready state and waits to be scheduled by the scheduler
                if has_pending_wait:
                    node.start_executing(current_env)
            else:
                node.finish_spec_execution()
                if has_pending_wait:
                    node.commit_speculated()
                    self.adjust_to_be_resolved_dict()
        else:
            assert False

    def reset_succeeding_nodes(self, node_id: NodeId, env_file: str):
        for uncommitted_node_id in self.get_all_next(node_id):
            uncommitted_node = self.get_node(uncommitted_node_id)
            if uncommitted_node.is_spec_executing():
                uncommitted_node.reset_to_ready()
            # uncommitted_node.start_spec_executing(env_file)

    def handle_wait(self, node_id: NodeId, env_file: str):
        event_log(f"handle_wait {node_id}")
        node = self.get_node(node_id)

        # Invalid state check
        if node.is_committed() or node.is_unsafe() or node.is_initialized():
            logging.error(f'Error: ConcreteNode {node_id} is in an invalid state: {node.state}')
            raise Exception(f'Error: ConcreteNode {node_id} is in an invalid state: {node.state}')
        

        if node.is_ready():
            node.start_executing(env_file)
        elif node.is_stopped():
            if node in self.get_frontier():
                logging.info(f'ConcreteNode {node_id} is stopped and in the frontier.')
                node.transition_from_stopped_to_executing(env_file)
            else:
                logging.info(f'ConcreteNode {node_id} is stopped but not in the frontier.')
        elif node.is_speculated():
            # Check if env conflicts exist
            if node.has_env_conflict_with(env_file):
                node.reset_to_ready()
                node.start_executing(env_file)
                self.reset_succeeding_nodes(node_id, env_file)
            # Optimization: It would make sense to perform the checks independently,
            # and if fs conflict, then update the run after dict.
            elif self.has_fs_deps(node_id):
                node.reset_to_ready()
                node.start_executing(env_file)
            else:
                node.commit_speculated()
                self.adjust_to_be_resolved_dict()
        elif node.is_executing():
            if node.has_env_conflict_with(env_file):
                self.reset_succeeding_nodes(node_id, env_file)
        elif node.is_spec_executing():
            if node.has_env_conflict_with(env_file):
                self.reset_succeeding_nodes(node_id, env_file)
        else:
            logging.error(f'Error: ConcreteNode {node_id} is in an invalid state: {node.state}')
            raise Exception(f'Error: ConcreteNode {node_id} is in an invalid state: {node.state}')
        
    def eager_fs_killing(self):
        event_log("try to eagerly kill conflicted speculation")
        to_be_killed = []
        self.fetch_fs_actions()
        for node in self.get_all_nodes():
            if ((node.is_speculated() or node.is_spec_executing())
                and self._has_fs_deps(node.id_)):
                to_be_killed.append(node)
        for node in to_be_killed:
            node.reset_to_ready()
            
    def exists_as_concrete_node(self, node_id) -> bool:
        return node_id in self.nodes
    
    def is_abstract_loop_node(self, node_id: NodeId):
        return self.abstract_nodes.get(node_id).is_loop()
    
    def filter_abstract_loop_nodes(self, node_ids: "list[NodeId]") -> "list[NodeId]":
        return [node_id for node_id in node_ids
                if self.is_abstract_loop_node(node_id)]


    def concretize_abstract_plain_nodes_until_loops(self):
        for abstract_node_id, abstract_node in self.abstract_nodes.items():
            # TODO: add extra condition when we add if branches
            if self.is_abstract_loop_node(abstract_node_id):
                # TODO: Here we want to check whether the abstract node has been committed
                # If committed, we don't have to stop here but move on
                # TODO: Would it make sense to add a committed/uncommitted state 
                # just for abstract nodes?
                return

            if not self.exists_as_concrete_node(abstract_node_id):
                abstract_node = self.abstract_nodes.get(abstract_node_id)
                self.nodes[abstract_node_id] = ConcreteNode(abstract_node.id_, 
                                                            abstract_node.cmd, 
                                                            abstract_node.asts, 
                                                            abstract_node.loop_contexts)
                # FIXME: This might not be correct. 
                # When stopping adding nodes in the PO due to loop nodes,
                # we might want to make the last inserted adjacency empty
                # and fix it once we add the future nodes.
                self.init_concrete_adjacency_entry(abstract_node_id)
                self.init_concrete_inverse_adjacency_entry(abstract_node_id)

    # Adds adjacency entry but completely ignores loop nodes
    # Might not make sense since we already ignore loop nodes earlier
    # in concretize_abstract_plain_nodes_until_loops()
    def init_concrete_adjacency_entry(self, node_id: NodeId):
        new_adjacency = self._get_concrete_adjacency(node_id, self.abstract_adjacency)
        self.adjacency[node_id] = new_adjacency
        
    def init_concrete_inverse_adjacency_entry(self, node_id: NodeId):
        new_inverse_adjacency = self._get_concrete_adjacency(node_id, self.abstract_inverse_adjacency)
        self.inverse_adjacency[node_id] = new_inverse_adjacency

    def _get_concrete_adjacency(self, node_id: NodeId, adjacency):
        to_check = adjacency[node_id].copy()
        new_adjacency = []
        visited = set()
        while to_check:
            current_node = to_check.pop()
            if current_node in visited:
                continue
            
            visited.add(current_node)
            if self.is_abstract_loop_node(current_node):
                for neighbor in adjacency[current_node]:
                    to_check.append(neighbor)
            else:
                new_adjacency.append(current_node)
        return new_adjacency

    def maybe_unroll_loop_node(self, node_id: NodeId) -> NodeId:
        ## Only unrolls this node if it doesn't already exist in the PO
        if not node_id in self.nodes:
            self.unroll_loop_node(node_id)
        ## The node_id must be part of the PO after unrolling, otherwise we did something wrong
        assert(node_id in self.nodes)
        
    def is_concrete_loop_node(self, node_id: NodeId):
        return self.nodes[node_id].is_loop()
        
    def filter_concrete_loop_nodes(self, node_ids: "list[NodeId]") -> "list[NodeId]":
        return [node_id for node_id in node_ids if self.is_abstract_loop_node(node_id)]

    def get_abstract_node_loop_context(self, node_id: NodeId):
        return self.abstract_nodes[node_id].loop_contexts

    ## This unrolls a loop given a target concrete node id
    def unroll_loop_node(self, target_concrete_node_id: NodeId):
        raw_node_id = target_concrete_node_id.get_non_iter_id()
        assert(self.is_abstract_loop_node(raw_node_id))
        loop_contexts = self.get_abstract_node_loop_context(raw_node_id)
        logging.debug(f'Closest non-committed loop node to unroll with raw_id {raw_node_id} is: {target_concrete_node_id}, and loop contexts: {loop_contexts}')
        ## Unroll all loops that this node is in
        new_first_node_id = self.unroll_loops(loop_contexts)

        ## At the end of unrolling the target node must be part of the PO
        assert(self.is_node_id(target_concrete_node_id))

    ## This unrolls a sequence of loops by unrolling each loop outside-in
    def unroll_loops(self, loop_contexts: LoopStack) -> NodeId:
        logging.debug(f'Unrolling the following loops: {loop_contexts}')

        ## All new node_ids
        all_new_node_ids = set()
        relevant_node_ids = list(self.abstract_nodes.keys())
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
                ## GL: 08-24-2023: This might not the best way to treat this as we need
                ## to update the env half way through the loop. 
                ## For now, we just copy the env from the parent loop node
                non_iter_id = new_node_id.get_non_iter_id()
                logging.debug(f"Copying latest env from loop context to loop node: {non_iter_id} -> {new_node_id}")
                self.latest_envs[new_node_id] = self.latest_envs[non_iter_id]

        ## KK 2023-05-22 Do we need to correctly populate the resolved set of next commands
        ##               after unrolling the loop.

        return new_first_node_id

    def find_outer_loop_sub_partial_order(self, loop_id: int, nodes_subset: "list[NodeId]") -> "list[NodeId]":
        loop_node_ids = []
        for node_id in nodes_subset:
            loop_context = self.get_abstract_node_loop_context(node_id)
            ## Note: this only checks for the nodes that have this loop id as their outer loop
            if not loop_context.is_empty() and loop_id == loop_context.get_outer():
                loop_node_ids.append(node_id)
        ## TODO: Assert that this is closed w.r.t. partial order
        return loop_node_ids

    ## This creates a new node_id and then creates a mapping from the node and iteration id to this node id
    ## TODO: Currently doesn't work with nested loops
    def create_node_id_with_one_less_loop_from_loop_node(self, node_id: NodeId, loop_id: int) -> NodeId:
        node: AbstractNode = self.abstract_nodes.get(node_id)
        logging.debug(f' >>> Node: {node}')
        logging.debug(f' >>> its loops: {node.loop_context} --- {node.current_iters}')

        new_iter = node.get_next_iter(loop_id)
        ## Creates a new node id where we have appended the new iter
        new_node_id = node_id.generate_new_node_id_with_another_iter(new_iter)
        logging.debug(f' >>> new node_id with another iter: {new_node_id}')
        return new_node_id

    ## This function unrolls a single loop, by first finding all its nodes (they must be contiguous) and then creating new versions of them
    ## that are concretized. Its second argument describes which subset of all partial order nodes we want to look at.
    ## That is necessary because when unrolling nested loops, we might end up in a situation where we have unrolled the
    ## outer loop, but some of the newly created nodes might still be loop nodes (so we might have loop nodes for the same loop in multiple locations).
    def unroll_single_loop(self, loop_id: int, nodes_subset: "list[NodeId]"):
        logging.info(f'Unrolling loop with id: {loop_id}')
        loop_node_ids = self.find_outer_loop_sub_partial_order(loop_id, nodes_subset)
        
        logging.debug(f'Node ids for loop: {loop_id} are: {loop_node_ids}')
        
        ## GL: OK UP TO HERE
        
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
