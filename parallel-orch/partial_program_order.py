from node import NodeId, Node
import logging
from collections import deque


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
        
    # def init_partial_order(self):
    #     self.init_workset()
    #     logging.debug(f'Initialized workset')
    #     self.populate_to_be_resolved_dict()
    #     if config.SPECULATE_IMMEDIATELY:
    #         self.init_latest_env_files()
    #     logging.debug(f'To be resolved sets per node:')
    #     logging.debug(self.to_be_resolved)
    #     logging.info(f'Initialized the partial order!')
    #     # self.log_partial_program_order_info()
    #     assert(self.valid())
    
    def init_partial_order(self):
        for node_id, node in self.nodes.items():
            if node.is_initialized():
                node.transition_from_init_to_ready()
                
        self.frontier = self.get_standard_source_nodes()
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
    
    def get_frontier(self):
        return self.frontier

    def log_info(self):
        logging.info(f"Nodes: {self.nodes}")
        logging.info(f"Adjacency: {self.adjacency}")
        logging.info(f"Inverse adjacency: {self.inverse_adjacency}")
        self.log_state()

    def log_state(self):
        for node in self.nodes.values():
            logging.info(f"Node {node.id}: {node.state}")

    def schedule_work(self):
        pass
    
    def get_source_nodes(self) -> list:
        sources = set()
        for to_id, from_ids in self.inverse_adjacency.items():
            if len(from_ids) == 0:
                sources.add(to_id)
        return list(sources)
    
    ## Returns the next non-committed normal node
    def progress_frontier(self) -> "list[NodeId]":
        return self.get_next_frontier_nodes(self.get_frontier())

    def get_next_nodes(self, node_id:NodeId) -> "list[NodeId]":
        return self.adjacency[node_id][:]

    def get_prev_nodes(self, node_id:NodeId) -> "list[NodeId]":
        return self.inverse_adjacency[node_id][:]
    
    def get_source_nodes(self) -> list:
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
        if visited is None:
            visited = set()
        visited.add(current_node_id)

        all_next_nodes = set([current_node_id])
        for neighbor in self.get_next_nodes(current_node_id):
            if neighbor not in visited:
                all_next_nodes.update(self.get_all_next(neighbor, visited))

        return all_next_nodes


    def get_all_previous(self, current_node_id: NodeId, visited=None) -> "set[NodeId]":
        if visited is None:
            visited = set()
        visited.add(current_node_id)

        all_previous_nodes = set([current_node_id])
        for neighbor in self.get_prev_nodes(current_node_id):
            if neighbor not in visited:
                all_previous_nodes.update(self.get_all_previous(neighbor, visited))

        return all_previous_nodes
    
    def get_all_previous_uncommitted(self, node_id: NodeId) -> "set[NodeId]":
        previous = self.get_all_previous(node_id)
        return set([node for node in previous if not self.nodes[node].is_committed()])
        
    
    def init_to_be_resolved_dict(self):
        for node_id in self.nodes.keys():
            self.to_be_resolved[node_id] = ...
        
    def init_to_be_resolved_dict(self):
        for node_id in self.nodes.keys():
            self.to_be_resolved[node_id] = ...
            
    
    def adjust_to_be_resolved_dict_entry(self, node_id: NodeId):
        
