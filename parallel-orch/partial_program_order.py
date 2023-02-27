from collections import defaultdict

class PartialProgramOrder:

    def __init__(self):
        self.nodes = []
        self.adjacency = defaultdict(lambda: [])
        self.inverse_adjacency = defaultdict(lambda: [])
        self.id_counter = 0
        self.frontier = set()

    def init_frontier(self):
        self.frontier.add(self.nodes[0])
        self.nodes[0].in_frontier = True

    def add_node(self, cmd):
        node = Node(cmd, self.id_counter)
        self.nodes.append(node)
        self.id_counter += 1

    def add_edge(self, node_from, node_to):
        if node_to not in self.adjacency[node_from]:
            self.adjacency[node_from].append[node_to]
        # else:
        #     raise Exception("Edge already exists")

    def __len__(self):
        return len(self.nodes)

    def get_all_current(self):
        return self.frontier

    # Moves the frontier one step forward (breadth-first traversal)
    # and commits previous frontier nodes
    def move_frontier_forward(self):
        new_frontier = set()
        for frontier_node in self.frontier:
            frontier_node.committed = True
            node_to_add = self.get_next_adjacent_of_node(frontier_node)
            if not node_to_add.in_forntier:
                node_to_add.in_forntier = True
                new_frontier.add(node_to_add)
        self.frontier = new_frontier
        return new_frontier
    
    # Fetches the next nodes (the future frontier but without committing it)
    def get_all_next(self, node):
        next_nodes = set()
        for frontier_node in self.frontier:
            next_node = self.get_next_adjacent_of_node(frontier_node)
            if not next_node.in_forntier:
                next_nodes.add(next_node)
        return next_nodes
    
    def get_rest(self):
        rest_nodes = []
        for node in self.nodes:
            if not node.committed and not node.in_frontier:
                rest_nodes = []
        return rest_nodes

    def get_next_adjacent_of_node(self, node):
        for adjacent_node in self.adjacency(node):
            if not adjacent_node.committed:
                return node

    def get_all_enumerate(self):
        return enumerate(self.nodes)

    ## Needs to be called after get_all_enumerate
    def get_suffix(self, i):
        return self.list_of_cmds[i+1:]

class Node:
    def __init__(self, cmd, id):
        self.cmd = cmd
        self.id = id
        self.committed = False
        self.in_frontier = False

    def __eq__(self, other):
        if isinstance(other, Node):
            if self.id == other.id:
                return True
            else:
                return False