from enum import Enum
from node import NodeId, Node, ConcreteNodeId, ConcreteNode, HSProg, HSBasicBlock
import logging
import util
from collections import deque

PROG_LOG = '[PROG_LOG] '
EVENT_LOG = '[EVENT_LOG] '

def event_log(s):
    logging.info(EVENT_LOG + s)

def progress_log(s):
    logging.info(PROG_LOG + s)


class ConcreteTree:
    def __init__(self):
        self.nodes = set()
        self.edges = {}
        self.reverse_edges = {}

    def add_node(self, node):
        self.nodes.add(node)

    def add_edge(self, from_node, to_node):
        assert from_node in self.nodes and to_node in self.nodes
        if label is None:
            label = CFGEdgeType.OTHER
        if not from_node in self.edges:
            self.edges[from_node] = set()
        if not to_node in self.reverse_edges:
            self.reverse_edges[to_node] = set()
        self.edges[from_node].add(to_node)
        self.reverse_edges[from_node].add(to_node)

    def has_node(self, node):
        return node in self.nodes

    def has_edge(self, from_node, to_node):
        return self.has_node(from_node) and to_node in self.edges[from_node]

class PartialProgramOrder:
    frontier: set  # Set of nodes at the frontier
    # Di: I'm going to ignore this for now and implement the feature without a local data structure
    # Later we can add this back as a caching mechanism to avoid doing RWSet
    # intersections of files all the time
    # run_after: "dict[NodeId, list[Node]]"  # Nodes that should run after certain conditions

    # Mapping of concrete nodes to lists of uncommitted concrete nodes the precedes them.
    # It is the snapshot of the reachable uncommited concrete nodes from prev_concrete_node graph
    # at the time the concrete node enters execution. So if there is fs conflict in them,
    # it needs to be rerun
    to_be_resolved: "dict[NodeId, list[Node]]"
    concrete_nodes: "dict[NodeId, Node]"

    def __init__(self, abstract_nodes: "dict[NodeId, Node]", edges: "dict[NodeId, list[NodeId]]",
                 hs_prog: HSProg):
        self.hsprog = hs_prog
        self.concrete_nodes: dict[ConcreteNodeId, ConcreteNode] = {}
        self.frontier = set()
        # self.run_after = {}
        # self.exec_order = ConcreteTree()
        # Nodes that we have received "wait" for
        self.canon_exec_order: list[ConcreteNodeId] = list()
        # Nodes that we think should happen, and haven't received "wait" for
        self.spec_exec_order: list[ConcreteNodeId] = list()
        self.to_be_resolved: dict[ConcreteNodeId, list[ConcreteNodeId]] = {}

    def commit_node(self, node):
        # Logic to handle committing a node
        node.transition_to_committed()
        # Maybe update dependencies here
        # etc.

    def get_concrete_node(self, concrete_node_id: ConcreteNodeId) -> ConcreteNode:
        return self.concrete_nodes[concrete_node_id]

    def get_all_nodes(self):
        return [node for node in self.concrete_nodes.values()]

    def get_committed_nodes(self):
        return [node for node in self.concrete_nodes.values() if node.is_committed()]

    # def get_ready_nodes(self):
    #     return [(cnid, n) for cnid, n in self.concrete_nodes.items() if n.is_ready()]

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
        # logging.info(f"Adjacency: {self.adjacency}")
        # logging.info(f"Inverse adjacency: {self.inverse_adjacency}")
        self.log_state()

    def log_state(self):
        for node in self.concrete_nodes.values():
            progress_log(node.pretty_state_repr())
        progress_log('')
        progress_log('canon: ' + ' '.join([str(cnid) for cnid in self.canon_exec_order]))
        progress_log('spec:  ' + ' '.join([str(cnid) for cnid in self.spec_exec_order]))
        

    def make_new_spec_node(self, prev_node: ConcreteNodeId):
        bb = self.hsprog.find_basic_block(prev_node.node_id)
        next_concrete_id = None
        if bb.node_ids[-1] != prev_node.node_id:
            i = bb.node_ids.index(prev_node.node_id)
            next_node_id = bb.node_ids[i+1]
            next_node = bb.get_node(next_node_id)
            next_concrete_id = ConcreteNodeId(next_node_id, prev_node.loop_iters)
        else:
            walked_edges = []
            seen_block_ids = set()
            while True:
                if self.hsprog.is_last_block(bb) or bb.bb_id in seen_block_ids:
                    return None
                seen_block_ids.add(bb.bb_id)
                edge_type, next_bb = self.hsprog.guess_next_block(bb)
                walked_edges.append(edge_type)
                if len(next_bb.nodes) > 0:
                    break
                bb = next_bb
            next_node = next_bb.nodes[0]
            next_node_id = next_node.id_
            for edge in walked_edges:
                next_concrete_id = prev_node.do_action(next_node_id, edge)
                prev_node = next_concrete_id
        if (next_concrete_id in self.concrete_nodes and
            not self.concrete_nodes[next_concrete_id].is_ready()):
            self.concrete_nodes[next_concrete_id].reset_to_ready()
        else:
            new_concrete_node = ConcreteNode(next_concrete_id, next_node)
            self.concrete_nodes[next_concrete_id] = new_concrete_node
            new_concrete_node.transition_from_init_to_ready()
            if new_concrete_node.command_unsafe():
                new_concrete_node.transition_from_ready_to_unsafe()
        return next_concrete_id
        
    def get_schedulable_nodes(self, window=2) -> list[ConcreteNodeId]:
        assert len(self.canon_exec_order) > 0
        if len(self.spec_exec_order) == 0:
            prev_node = self.canon_exec_order[-1]
        else:
            prev_node = self.spec_exec_order[-1]
        while len(self.spec_exec_order) < window:
            next_concrete_id = self.make_new_spec_node(prev_node)
            if next_concrete_id is None:
                window = len(self.spec_exec_order)
            else:
                self.spec_exec_order.append(next_concrete_id)
                prev_node = self.spec_exec_order[-1]
        self.log_state()
        return [cnid for cnid in self.spec_exec_order[:window]
                if self.concrete_nodes[cnid].is_ready()]
    
    # def get_prev_nodes(self, concrete_node_id: ConcreteNodeId) -> "list[ConcreteNodeId]":
    #     return self.exec_order[concrete_node_id][:]

    # def get_all_next(self, current_node_id: ConcreteNodeId, visited=None) -> "set[NodeId]":
    #     all_next = set()
    #     def reachable_rec(cur, reachable):
    #         if cur in reachable:
    #             return
    #         reachable.add(cur)
    #         for n in self.get_next_nodes(cur):
    #             reachable_rec(n, reachable)
    #     for n in self.get_next_nodes(current_node_id):
    #         reachable_rec(n, all_next)
    #     return all_next


    # def get_all_previous(self, current_node_id: ConcreteNodeId, visited=None) -> "set[NodeId]":
    #     all_prev = set()
    #     def reachable_rec(cur, reachable):
    #         if cur in reachable:
    #             return
    #         reachable.add(cur)
    #         for n in self.get_prev_nodes(cur):
    #             reachable_rec(n, reachable)
    #     for n in self.get_prev_nodes(current_node_id):
    #         reachable_rec(n, all_prev)
    #     return all_prev

    def get_all_previous(self, current_node_id: ConcreteNodeId):
        if current_node_id in self.canon_exec_order:
            i = self.canon_exec_order.index(current_node_id)
            return self.canon_exec_order[:i]
        elif current_node_id in self.spec_exec_order:
            i = self.spec_exec_order.index(current_node_id)
            return self.canon_exec_order[:] + self.spec_exec_order[:i]
        else:
            assert False

    # TODO: fixme
    # def get_all_next_uncommitted(self, node_id: NodeId) -> "set[NodeId]":
    #     next = self.get_all_next(node_id)
    #     return set([node for node in next if not self.concrete_nodes[node].is_committed()])

    def get_all_previous_uncommitted(self, concrete_node_id: ConcreteNodeId) -> "set[ConcreteNodeId]":
        previous = self.get_all_previous(concrete_node_id)
        return set([cnid for cnid in previous if not self.concrete_nodes[cnid].is_committed()])

    def adjust_to_be_resolved_dict_entry(self, concrete_node_id: ConcreteNodeId):
        node = self.concrete_nodes.get(concrete_node_id)
        if node.is_committed():
            self.to_be_resolved[concrete_node_id] = []
        elif node.is_ready() and (concrete_node_id in self.spec_exec_order or
                                  concrete_node_id in self.canon_exec_order):
            self.to_be_resolved[concrete_node_id] = self.get_all_previous_uncommitted(concrete_node_id)

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

    def _has_fs_deps(self, concrete_node_id: ConcreteNodeId):
        node_of_interest : ConcreteNode = self.get_concrete_node(concrete_node_id)
        for nid in self.to_be_resolved[concrete_node_id]:
            node: ConcreteNode = self.get_concrete_node(nid)
            if node.get_rw_set().has_conflict(node_of_interest.get_rw_set()):
                return True
        return False

    # TODO: It's currently designed this way to avoid reading trace file all the time
    # When we have complex caching code for this we can make this go away
    def has_fs_deps(self, concrete_node_id: ConcreteNodeId):
        self.fetch_fs_actions()
        self._has_fs_deps(concrete_node_id)

    ### external handler events ###

    def schedule_work(self, concrete_node_id: ConcreteNodeId, env_file: str):
        event_log("schedule_work")
        self.get_concrete_node(concrete_node_id).start_executing(env_file)

    def schedule_spec_work(self, concrete_node_id: ConcreteNodeId, env_file: str):
        event_log("schedule_spec")
        util.debug_log(f"concrete_node_id: {concrete_node_id}")
        self.adjust_to_be_resolved_dict_entry(concrete_node_id)
        self.get_concrete_node(concrete_node_id).start_spec_executing(env_file)

    def handle_complete(self, concrete_node_id: ConcreteNodeId, has_pending_wait: bool,
                        current_env: str):
        event_log(f"handle_complete {concrete_node_id}")
        node = self.get_concrete_node(concrete_node_id)
        # TODO: complete the state matching
        if node.is_executing():
            node.commit_frontier_execution()
            self.adjust_to_be_resolved_dict()
        elif node.is_spec_executing():
            if self.has_fs_deps(concrete_node_id):
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
        # TODO: fixme
        pass
        # for uncommitted_node_id in self.get_all_next(node_id):
        #     uncommitted_node = self.get_concrete_node(uncommitted_node_id)
        #     if uncommitted_node.is_spec_executing():
        #         uncommitted_node.reset_to_ready()
        #     # uncommitted_node.start_spec_executing(env_file)

    # def adding_new_basic_block(self, concrete_node_id: ConcreteNodeId):
    #     basic_block = self.hsprog.find_basic_block(concrete_node_id.node_id)
    #     if len(self.concrete_nodes) != 0:
    #         prev_concrete_node_id = next(reversed(self.concrete_nodes))
    #     else:
    #         prev_concrete_node_id = None
    #     loop_iters = concrete_node_id.loop_iters
    #     for abstract_node_id in basic_block.node_ids:
    #         new_concrete_node_id = ConcreteNodeId(abstract_node_id, loop_iters)
    #         new_concrete_node = ConcreteNode(new_concrete_node_id,
    #                                          basic_block.get_node(abstract_node_id))
    #         new_concrete_node.transition_from_init_to_ready()
    #         if new_concrete_node.command_unsafe():
    #             new_concrete_node.transition_from_ready_to_unsafe()
    #         self.concrete_nodes[new_concrete_node_id] = new_concrete_node
    #         if prev_concrete_node_id is not None:
    #             self.exec_order[new_concrete_node_id] = [prev_concrete_node_id]
    #         else:
    #             self.exec_order[new_concrete_node_id] = []
    #         prev_concrete_node_id = new_concrete_node_id
    #     assert concrete_node_id in self.concrete_nodes

    def finish_wait_unsafe(self, concrete_node_id: ConcreteNodeId):
        node = self.concrete_nodes[concrete_node_id]
        node.commit_unsafe_node()

    def handle_wait(self, concrete_node_id: ConcreteNodeId, env_file: str):
        event_log(f"handle_wait {concrete_node_id}")

        if len(self.spec_exec_order) and concrete_node_id == self.spec_exec_order[0]:
            self.spec_exec_order.pop(0)
        else:
            for cnid in self.spec_exec_order:
                self.concrete_nodes[cnid].reset_to_ready()
            self.spec_exec_order = []

        if not concrete_node_id in self.concrete_nodes:
            abstract_node = self.hsprog.find_node(concrete_node_id.node_id)
            new_concrete_node = ConcreteNode(concrete_node_id, abstract_node)
            new_concrete_node.transition_from_init_to_ready()
            if new_concrete_node.command_unsafe():
                new_concrete_node.transition_from_ready_to_unsafe()            
            self.concrete_nodes[concrete_node_id] = new_concrete_node

        self.canon_exec_order.append(concrete_node_id)
        
        node = self.get_concrete_node(concrete_node_id)
        # Invalid state check
        if node.is_committed() or node.is_initialized():
            logging.error(f'Error: Node {concrete_node_id} is in an invalid state: {node.state}')
            raise Exception(f'Error: Node {concrete_node_id} is in an invalid state: {node.state}')

        if node.is_ready():
            node.start_executing(env_file)
        elif node.is_unsafe():
            pass
        elif node.is_stopped():
            if node in self.get_frontier():
                logging.info(f'Node {concrete_node_id} is stopped and in the frontier.')
                node.transition_from_stopped_to_executing(env_file)
            else:
                logging.info(f'Node {concrete_node_id} is stopped but not in the frontier.')
        elif node.is_speculated():
            # Check if env conflicts exist
            if node.has_env_conflict_with(env_file):
                util.debug_log(f'prev_env: {node.exec_ctxt.pre_env_file}, real: {env_file}')
                node.reset_to_ready()
                node.start_executing(env_file)
                self.reset_succeeding_nodes(concrete_node_id, env_file)
            # Optimization: It would make sense to perform the checks independently,
            # and if fs conflict, then update the run after dict.
            elif self.has_fs_deps(concrete_node_id):
                node.reset_to_ready()
                node.start_executing(env_file)
            else:
                node.commit_speculated()
                self.adjust_to_be_resolved_dict()
        elif node.is_executing():
            if node.has_env_conflict_with(env_file):
                node.reset_to_ready()
                node.start_executing(env_file)
        elif node.is_spec_executing():
            # if node.has_env_conflict_with(env_file):
                node.reset_to_ready()
                node.start_executing(env_file)
        else:
            logging.error(f'Error: Node {concrete_node_id} is in an invalid state: {node.state}')
            raise Exception(f'Error: Node {concrete_node_id} is in an invalid state: {node.state}')

    def eager_fs_killing(self):
        event_log("try to eagerly kill conflicted speculation")
        to_be_killed = []
        self.fetch_fs_actions()
        for node in self.get_all_nodes():
            if ((node.is_speculated() or node.is_spec_executing())
                and self._has_fs_deps(node.cnid)):
                to_be_killed.append(node)
        for node in to_be_killed:
            node.reset_to_ready()
