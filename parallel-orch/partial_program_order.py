import trace

class Node:
    def __init__(self, id, cmd):
        self.cmd = cmd
        self.id = id
        self.cmd_no_redir = trace.remove_command_redir(self.cmd)

    def __str__(self):
        # return f"ID: {self.id}\nCMD: {self.cmd}\nR: {self.read_set}\nW: {self.write_set}"
        return self.cmd


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

    def get_cmd(self):
        return self.cmd

    def get_cmd_no_redir(self):
        return self.cmd_no_redir


class RWSet:

    def __init__(self, read_set: set, write_set: set):
        self.read_set = read_set
        self.write_set = write_set

    def add_to_read_set(self, item):
        self.read_set.add(item)

    def add_to_write_set(self, item):
        self.write_set.add(item)

    def get_read_set(self):
        return self.read_set

    def get_write_set(self):
        return self.write_set


class PartialProgramOrder:

    def __init__(self, nodes:dict, edges:dict):
        self.nodes = nodes
        # TODO: consider changing values to sets instead of lists
        self.adjacency = edges
        self.init_inverse_adjacency()
        ## self.committed is an add-only set, we never remove
        self.committed = set()
        ## Nodes that are in the frontier can only move to committed
        self.frontier = self.get_source_nodes()
        self.speculated = set()
        self.rw_sets = {node_id: RWSet([], []) for node_id in self.nodes.keys()}
        self.workset = []
    
    def __str__(self):
        return f"Nodes: {len(self.nodes.keys())}\nEdges: {self.adjacency}"

    def get_source_nodes(self):
        sources = set()
        for to_id, from_ids in self.inverse_adjacency.items():
            if len(from_ids) == 0:
                sources.add(to_id)
        return list(sources)

    def init_workset(self):
        self.workset = self.get_all_non_committed()
    
    def get_workset(self) -> list:
        return self.workset

    def init_inverse_adjacency(self):
        self.inverse_adjacency = {i: [] for i in self.nodes.keys()}
        for from_id, to_ids in self.adjacency.items():
            for to_id in to_ids:
                self.inverse_adjacency[to_id].append(from_id)

    # ## TODO: (When there is time) Define a function that checks that the graph is valid
    # def valid(self):
    #     ## TODO: Check that committed is prefix closed w.r.t partial order
        
    #     ## TODO: Check that all frontier nodes are after committed nodes

    #     ## TODO: Check that speculated have no intersection with committed and frontier
    #     ## TODO: Check that frontier and committed do not intersect
    #     assert(not self.sets_intersect())
    #     return True

    # def sets_intersect(self):
    #     return len(set.intersection(set(self.committed), set(self.frontier), set(self.speculated))) > 0

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
        workset = target_node_ids.copy()
        while len(workset) > 0:
            node_id = workset.pop()
            next = self.get_next(node_id)
            new_next = all_next_transitive.intersection(next)
            all_next_transitive = all_next_transitive.union(next)
            workset.extend(new_next)
        return list(all_next_transitive)

    def is_frontier(self, node_id: int) -> bool:
        return node_id in self.frontier
    
    def update_rw_set(self, node_id, rw_set):
        self.rw_sets[node_id] = rw_set

    def get_rw_set(self, node_id):
        return self.rw_sets[node_id]
    
    def get_rw_sets(self):
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

    ## Resolve all the forward dependencies and update the workset
    ## Forward dependency is when a command's output is the same
    ## as the input of a following command
    def resolve_dependencies(self):
        for first_cmd_id in self.get_workset():
            # We don't want the first cmd, so we remove it from the transitive closure.
            transitive_closure = self.get_transitive_closure([first_cmd_id])
            transitive_closure.remove(first_cmd_id)
            # We look at the transitive closure instead of workset because we want to also check the speculated cmds that are not in the workset
            for second_cmd_id in transitive_closure:
                # If no anti-dependencies exist, we proceed to check for dependencies
                if not (self.has_backward_dependency(first_cmd_id, second_cmd_id)
                        or self.has_write_dependency(first_cmd_id, second_cmd_id)):
                    if self.has_forward_dependency(first_cmd_id, second_cmd_id):
                        # When a forward dependency exists
                        # the first command can be speculated but we need to rerun the second one
                        self.speculated.add(first_cmd_id)
                    else:
                        # No dependency exist so both commands are speculated successfully
                        self.speculated.add(first_cmd_id)
                        self.speculated.add(second_cmd_id)

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

    # We want to commit the current frontier node(s),
    # move the frontier one step forward
    # and then generate the new workset,
    # ignoring the speculated cmds
    def step_forward(self):
        self.commit_frontier()
        self.move_frontier_forward()
        self.create_new_workset()

    # Add frontier commands to committed set
    def commit_frontier(self):
        self.committed.update(self.frontier)

    # Returns all the uncommitted, non-speculated nodes
    # directly or indirectly adjacent to the given node
    def get_next_non_speculated(self, node_id):
        next_node_ids = self.adjacency[node_id]
        next_non_speculated_node_ids = []
        for next_node_id in next_node_ids:
            # If node already committed, do nothing
            if next_node_id in self.committed:
                continue
            # We want to commit the speculated node right away
            # and then move another step forward
            if next_node_id in self.speculated:
                self.speculated.remove(next_node_id)
                self.committed.add(next_node_id)
                next_non_speculated_node_ids.extend(self.get_next_non_speculated(next_node_id))
            else:
                next_non_speculated_node_ids.append(next_node_id)
        return next_non_speculated_node_ids

    def move_frontier_forward(self):
        new_frontier = []
        for node_id in self.frontier:
            if not node_id in new_frontier:
                new_frontier.extend(self.get_next_non_speculated(node_id))

    def create_new_workset(self):
        self.workset = [node_id for node_id in self.get_all_non_committed() if node_id not in self.speculated]
        print(">>>",self.workset)
        print(">>>",self.frontier)
