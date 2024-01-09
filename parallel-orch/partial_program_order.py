from node import NodeId, Node
import logging


class PartialProgramOrder:
    frontier: set  # Set of nodes at the frontier
    run_after: set  # Nodes that should run after certain conditions
    window: int  # Integer representing the window
    to_be_resolved: "dict[NodeId, list[Node]]"  # Mapping of nodes to lists of uncommitted nodes
    nodes: "dict[NodeId, Node]"
    adjacency: "dict[NodeId, list[NodeId]]"
    inverse_adjacency: "dict[NodeId, list[NodeId]]"
    
    def __init__(self, nodes: "dict[NodeId, Node]", edges: "dict[NodeId, list[NodeId]]"):
        self.nodes = nodes
        self.adjacency = edges
        self.inverse_adjacency = self.init_inverse_adjacency()
        self.frontier = set()
        self.run_after = set()
        self.window = 0
        self.to_be_resolved = {} 
        
    def init_partial_order(self):
        for node_id, node in self.nodes.items():
            node.transition_to_ready()
        # TODO: Implement the rest of the partial order initialization

    def commit_node(self, node):
        # Logic to handle committing a node
        node.transition_to_committed()
        # Maybe update dependencies here 
        # etc.

    def init_inverse_adjacency(self):
        inverse_adjacency = {i: [] for i in self.nodes.keys()}
        for from_id, to_ids in self.adjacency.items():
            for to_id in to_ids:
                inverse_adjacency[to_id].append(from_id)
        return inverse_adjacency
    
    def get_node(self, node_id: NodeId) -> Node:
        return self.nodes[node_id]
    
    def get_committed_nodes(self):
        return [node for node in self.nodes.values() if node.is_committed()]
    
    def get_ready_nodes(self):
        return [node for node in self.nodes.values() if node.is_ready()]
    
    def get_executing_nodes(self):
        return [node for node in self.nodes.values() if node.is_executing()]
    
    def get_spec_executing_nodes(self):
        return [node for node in self.nodes.values() if node.is_spec_executing()]
    
    def get_executing_normal_and_speculated_nodes(self):
        return [node for node in self.nodes.values() if node.is_executing() or node.is_spec_executing()]
    
    def get_speculated_nodes(self):
        return [node for node in self.nodes.values() if node.is_speculated()]
    
    def get_uncommitted_nodes(self):
        return [node for node in self.nodes.values() if not node.is_committed()]

    def log_state(self):
        for node in self.nodes.values():
            logging.info(f"Node {node.id}: {node.state}")

    def schedule_work(self):
        pass
