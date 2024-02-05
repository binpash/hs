from node import NodeId, Node, ConcreteNode, HSProg
import logging
from collections import deque

PROG_LOG = '[PROG_LOG] '
EVENT_LOG = '[EVENT_LOG] '

def event_log(s):
    logging.info(EVENT_LOG + s)

def progress_log(s):
    logging.info(PROG_LOG + s)

class PartialProgramOrder:
    frontier: set  # Set of nodes at the frontier
    # Di: I'm going to ignore this for now and implement the feature without a local data structure
    # Later we can add this back as a caching mechanism to avoid doing RWSet
    # intersections of files all the time
    # run_after: "dict[NodeId, list[Node]]"  # Nodes that should run after certain conditions
    to_be_resolved: "dict[NodeId, list[Node]]"  # Mapping of nodes to lists of uncommitted nodes
    concrete_nodes: "dict[NodeId, Node]"

    def __init__(self, abstract_nodes: "dict[NodeId, Node]", edges: "dict[NodeId, list[NodeId]]"):
        self.hsprog = HSProg(abstract_nodes, edges)
        self.concrete_nodes = {node_id: ConcreteNode(ab_node) for node_id, ab_node
                               in abstract_nodes.items()}
        self.frontier = set()
        # self.run_after = {}
        self.to_be_resolved = {}

    def init_partial_order(self):
        for node_id, node in self.concrete_nodes.items():
            if node.is_initialized():
                node.transition_from_init_to_ready()

        self.init_to_be_resolved_dict()
        logging.info(self.to_be_resolved)
        # Init frontier
        self.frontier = self.get_standard_source_nodes()
        # TODO: Implement the rest of the partial order initialization

    @property
    def abstract_nodes(self):
        return self.hsprog.abstract_nodes

    @property
    def adjacency(self):
        return self.hsprog.adjacency

    @property
    def inverse_adjacency(self):
        return self.hsprog.inverse_adjacency
        
    def commit_node(self, node):
        # Logic to handle committing a node
        node.transition_to_committed()
        # Maybe update dependencies here
        # etc.

    def get_node(self, node_id: NodeId) -> Node:
        return self.concrete_nodes[node_id]

    def get_all_nodes(self):
        return [node for node in self.concrete_nodes.values()]

    def get_committed_nodes(self):
        return [node for node in self.concrete_nodes.values() if node.is_committed()]

    def get_ready_nodes(self):
        return [node for node in self.concrete_nodes.values() if node.is_ready()]

    def get_executing_nodes(self):
        return [node for node in self.concrete_nodes.values() if node.is_executing()]

    def get_spec_executing_nodes(self):
        return [node for node in self.concrete_nodes.values() if node.is_spec_executing()]

    def get_executing_normal_and_spec_nodes(self):
        return [node for node in self.concrete_nodes.values() if node.is_executing() or node.is_spec_executing()]

    def get_speculated_nodes(self):
        return [node for node in self.concrete_nodes.values() if node.is_speculated()]

    def get_uncommitted_nodes(self):
        return [node for node in self.concrete_nodes.values() if not node.is_committed()]

    def get_frontier(self):
        return self.frontier

    def log_info(self):
        logging.info(f"Nodes: {self.concrete_nodes}")
        logging.info(f"Adjacency: {self.adjacency}")
        logging.info(f"Inverse adjacency: {self.inverse_adjacency}")
        self.log_state()

    def log_state(self):
        for node in self.concrete_nodes.values():
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
            current_node = self.concrete_nodes.get(current_node_id)

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
        return set([node for node in next if not self.concrete_nodes[node].is_committed()])

    def get_all_previous_uncommitted(self, node_id: NodeId) -> "set[NodeId]":
        previous = self.get_all_previous(node_id)
        return set([node for node in previous if not self.concrete_nodes[node].is_committed()])

    def adjust_to_be_resolved_dict_entry(self, node_id: NodeId):
        node = self.concrete_nodes.get(node_id)
        if node.is_committed():
            self.to_be_resolved[node_id] = []
        elif node.is_ready():
            self.to_be_resolved[node_id] = self.get_all_previous_uncommitted(node_id)

    def init_to_be_resolved_dict(self):
        for node_id in self.concrete_nodes:
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
        node_of_interest : Node = self.get_node(node_id)
        for nid in self.to_be_resolved[node_id]:
            node: Node = self.get_node(nid)
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
            logging.error(f'Error: Node {node_id} is in an invalid state: {node.state}')
            raise Exception(f'Error: Node {node_id} is in an invalid state: {node.state}')


        if node.is_ready():
            node.start_executing(env_file)
        elif node.is_stopped():
            if node in self.get_frontier():
                logging.info(f'Node {node_id} is stopped and in the frontier.')
                node.transition_from_stopped_to_executing(env_file)
            else:
                logging.info(f'Node {node_id} is stopped but not in the frontier.')
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
            logging.error(f'Error: Node {node_id} is in an invalid state: {node.state}')
            raise Exception(f'Error: Node {node_id} is in an invalid state: {node.state}')

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
