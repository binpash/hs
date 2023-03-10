import trace

class Node:
    def __init__(self, id, cmd):
        self.cmd = cmd
        self.id = id
        self.cmd_no_redir = trace.remove_command_redir(self.cmd)

    def __str__(self):
        # return f"ID: {self.id}\nCMD: {self.cmd}\nR: {self.read_set}\nW: {self.write_set}"
        return self.cmd

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
        self.rw_sets = {node_id: RWSet([], []) for node_id in self.nodes.keys()}
        self.workset = []
    
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
            successors = set(self.get_next(node_id))
            new_next = successors - all_next_transitive
            all_next_transitive = all_next_transitive.union(successors)
            workset.extend(new_next)
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

    ## Resolve all the forward dependencies and update the workset
    ## Forward dependency is when a command's output is the same
    ## as the input of a following command
    def resolve_dependencies(self):
        new_workset = []
        for first_cmd_id in self.get_workset():
            # We don't want the first cmd, so we remove it from the transitive closure.
            transitive_closure = self.get_transitive_closure([first_cmd_id])
            transitive_closure.remove(first_cmd_id)
            # We look at the transitive closure instead of workset because we want to also check the speculated cmds that are not in the workset
            for second_cmd_id in transitive_closure:
                # If no anti-dependencies exist, we proceed to check for dependencies
                if second_cmd_id not in new_workset and (self.has_backward_dependency(first_cmd_id, second_cmd_id) or self.has_write_dependency(first_cmd_id, second_cmd_id) or self.has_forward_dependency(first_cmd_id, second_cmd_id)):
                    new_workset.append(second_cmd_id)
                else:
                    pass
        # Set the new speculated set
        
        old_speculated = self.speculated.copy()
        self.speculated = {cmd_id for cmd_id in self.workset if cmd_id not in new_workset and cmd_id not in self.frontier}
        # Set the new workset
        self.workset = new_workset
        self.step_forward(old_speculated)

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
    def step_forward(self, old_speculated: set):
        self.commit_frontier()
        self.move_frontier_forward(old_speculated)

    # Add frontier commands to committed set
    def commit_frontier(self):
        self.committed.update(self.frontier)

    def move_frontier_forward(self, old_speculated: set):
        new_frontier = []
        for node in self.frontier:
            new_frontier.extend(self.get_next_non_speculated(node, old_speculated))
        self.frontier = new_frontier

    def get_next_non_speculated(self, start, old_speculated: set):
        workset = self.get_next(start)
        next_non_speculated = []
        while len(workset) > 0:
            node_id = workset.pop()
            if node_id in old_speculated.union(self.speculated):
                self.speculated.discard(node_id)
                self.committed.add(node_id)
                workset.extend(self.get_next(node_id))
            else:
                next_non_speculated.append(node_id)
        return next_non_speculated

    def log_rw_sets(self, logging):
        logging.debug("====== |RW Sets| ======")
        for node_id, rw_set in self.rw_sets.items():
            logging.debug(f"ID: {node_id}")
            logging.debug(f"Read: {rw_set.get_read_set()}")
            logging.debug(f"Write: {rw_set.get_write_set()}")

    def log_partial_program_order_info(self):
        print(f"=" * 60)
        print(f"WORKSET:{self.get_workset()}")
        print(f"COMMITTED:{self.get_committed()}")
        print(f"FRONTIER:{self.get_frontier()}")
        print(f"SPECULATED:{self.get_speculated()}")
        print(f"=" * 60)