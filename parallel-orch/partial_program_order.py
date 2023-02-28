from collections import defaultdict


class Node:
    def __init__(self, id, cmd):
        self.cmd = cmd
        self.id = id
        # maybe redundant
        self.committed = False
        self.in_frontier = False
        self.executed_successfully = False
        self.read_set = set()
        self.write_set = set()

    def __str__(self):
        # return f"ID: {self.id}\nCMD: {self.cmd}\nR: {self.read_set}\nW: {self.write_set}"
        return self.cmd

    def update_read_set(self, read_set):
        self.read_set = set(read_set)

    def add_to_read_set(self, ref):
        self.read_set.add(ref)

    def update_write_set(self, write_set):
        self.write_set = set(write_set)
    
    def add_to_write_set(self, ref):
        self.write_set.add(ref)

    def __eq__(self, other):
        if isinstance(other, Node):
            if self.id == other.id:
                return True
            else:
                return False
            
    def log_simplified(self):
        logging.debug(f"ID:{self.id}")
        logging.debug(f"CMD:{self.cmd}")
        logging.debug(f"R:{[ref_name for ref_name in self.read_set]}")
        logging.debug(f"W:{[ref_name for ref_name in self.write_set]}")
        logging.debug(f"C:{self.commited}\n")



class PartialProgramOrder:

    def __init__(self, nodes:dict, edges:dict):
        self.nodes = nodes
        # TODO: consider changing values to sets instead of lists
        self.adjacency = edges
        self.init_inverse_adjacency()
        ## self.committed is an add-only set, we never remove
        self.committed = []
        ## Nodes that are in the frontier can only move to committed
        self.frontier = self.get_source_nodes()
        self.speculated = []
    
    def __str__(self):
        return f"Nodes: {len(self.nodes.keys())}\nEdges: {self.adjacency}"

    def get_source_nodes(self):
        sources = set()
        for to_id, from_ids in self.inverse_adjacency.items():
            if len(from_ids) == 0:
                sources.add(to_id)
        return list(sources)
    
    def init_inverse_adjacency(self):
        self.inverse_adjacency = {i: [] for i in self.nodes.keys()}
        for from_id, to_ids in self.adjacency.items():
            for to_id in to_ids:
                self.inverse_adjacency[to_id].append(from_id)

    ## TODO: (When there is time) Define a function that checks that the graph is valid
    def valid(self):
        ## TODO: Check that committed is prefix closed w.r.t partial order
        ## TODO: Check that frontier and committed do not intersect
        ## TODO: Check that all frontier nodes are after committed nodes
        ## TODO: Check that speculated have no intersection with committed and frontier
        return True

    def __len__(self):
        return len(self.nodes)

    def get_node(self, node_id:int) -> Node:
        return self.nodes[node_id]

    def get_all_non_committed(self):
        return self.get_transitive_closure(self.frontier)

    def get_next(self, node_id:int) -> list:
        return self.adjacency[node_id]
    
    def get_transitive_closure(self, target_node_ids:list) -> list:
        all_next_transitive = set(target_node_ids)
        workset = target_node_ids.copy()
        while len(workset) > 0:
            node_id = workset.pop()
            next = self.get_next(node_id)
            new_next = all_next_transitive.intersection(next)
            all_next_transitive = all_next_transitive.union(next)
            workset.extend(new_next)
        return list(all_next_transitive)

    
    ## Old ones below

    # def get_all_current(self):
    #     return self.frontier
    # # Moves the frontier one step forward (breadth-first traversal)
    # # and commits previous frontier nodes
    # def move_frontier_forward(self):
    #     new_frontier = set()
    #     for frontier_node in self.frontier:
    #         frontier_node.committed = True
    #         node_to_add = self.get_next_adjacent_of_node(frontier_node)
    #         if not node_to_add.in_forntier:
    #             node_to_add.in_forntier = True
    #             new_frontier.add(node_to_add)
    #     self.frontier = new_frontier
    #     return new_frontier
    
    # # Fetches the next nodes (the future frontier but without committing it)
    # def get_all_next(self, node):
    #     next_nodes = set()
    #     for frontier_node in self.frontier:
    #         next_node = self.get_next_adjacent_of_node(frontier_node)
    #         if not next_node.in_forntier:
    #             next_nodes.add(next_node)
    #     return next_nodes
    
    # def get_rest(self):
    #     rest_nodes = []
    #     for node in self.nodes:
    #         if not node.committed and not node.in_frontier:
    #             rest_nodes = []
    #     return rest_nodes

    # def get_next_adjacent_of_node(self, node):
    #     for adjacent_node in self.adjacency(node):
    #         if not adjacent_node.committed:
    #             return node

    # def get_all_enumerate(self):
    #     return enumerate(self.nodes)

    # # ## Needs to be called after get_all_enumerate
    # # def get_suffix(self, i):
    # #     return self.list_of_cmds[i+1:]

    # def get_all_next_to_execute(self, node):
    #     next_nodes = set()
    #     for frontier_node in self.frontier:
    #         next_node = self.get_next_adjacent_of_node(frontier_node)
    #         if not next_node.in_forntier:
    #             next_nodes.add(next_node)
    #     return next_nodes
    

