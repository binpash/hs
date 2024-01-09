from enum import Enum, auto

class NodeState(Enum):
    INIT = auto()
    READY = auto()
    COMMITTED = auto()
    STOP = auto()
    SPECULATED = auto()
    EXECUTING = auto()
    SPEC_EXECUTING = auto()
    UNSAFE = auto()

class Sandbox:
    def __init__(self, trace_file, exit_code, post_execution_env_file, stdout_file, sandbox_dir):
        # These get predetermined prior to the execution
        self.trace_file = trace_file
        self.post_execution_env_file = post_execution_env_file
        self.stdout_file = stdout_file
        self.sandbox_dir = sandbox_dir
        # These get set after execution is done
        self.exit_code = None
        self.proc_id = None
        
    def set_exit_code(self, exit_code):
        self.exit_code = exit_code
        
    def set_proc_id(self, proc_id):
        self.proc_id = proc_id

    def get_exit_code(self):
        return self.exit_code

    def get_post_execution_env_file(self):
        return self.post_execution_env_file

    def get_stdout_file(self):
        return self.stdout_file

    def get_sandbox_dir(self):
        return self.sandbox_dir

    def get_trace_file(self):
        return self.trace_file

    def __str__(self):
        return f'Sandbox(trace:{self.get_trace_file}, ec:{self.get_exit_code()}, env:{self.get_post_execution_env_file()}, stdout:{self.get_stdout_file()}, sandbox:{self.get_sandbox_dir()})'

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


class NodeId:
    
    #TODO: Implement iteration support
    
    def __init__(self, id: int):
        self.id = id

    def get_non_iter_id(self):
        return NodeId(self.id)

    def __repr__(self):
        ## TODO: Represent it using n.
        output = f'{self.id}'
        return output

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        # return self.loop_iters == other.loop_iters and self.id == other.id
        return self.id == other.id

    def __ne__(self, other):
        return not(self == other)

    def __lt__(self, obj):
        return (str(self) < str(obj))

    def __gt__(self, obj):
        return (str(self) > str(obj))

    @staticmethod
    def parse_node_id(node_id_str: str):
        return NodeId(int(node_id_str))


class Node:
    id: NodeId
    cmd: str
    asts: "list[AstNode]"
    state: NodeState
    # Nodes to check for fs dependencies before this node can be committed
    # for this particular execution of the main sandbox.
    # No need to do the same for the background sandbox since it will always get committed.
    to_be_resolved_snapshot: "set[NodeId]"
    # Read and write sets for this node
    rwset: RWSet
    # This contains the sandbox and execution info for a spec-executing node 
    # (or plain executing node if frontier background node execution is not enabled)
    main_sandbox: Sandbox
    # This can only be set while in the frontier and the background node execution is enabled
    background_sandbox: Sandbox
    
    
    def __init__(self, node_id: NodeId, cmd: str, asts: "list[AstNode]"):
        self.id = node_id
        self.cmd = cmd
        self.asts = asts
        # The node's state
        self.state = NodeState.INIT
        self.tracefile = None
        self.rwset = None
        # The 
        self.to_be_resolved_snapshot = None
        
        self.main_sandbox = None
        
        self.background_sandbox = None


    def is_initialized(self):
        return self.state == NodeState.INIT
    
    def is_ready(self):
        return self.state == NodeState.READY
    
    def is_committed(self):
        return self.state == NodeState.COMMITTED
    
    def is_stopped(self):
        return self.state == NodeState.STOP
    
    def is_speculated(self):
        return self.state == NodeState.SPECULATED

    def is_executing(self):
        return self.state == NodeState.EXECUTING
    
    def is_spec_executing(self):
        return self.state == NodeState.SPEC_EXECUTING
    
    def is_unsafe(self):
        return self.state == NodeState.UNSAFE
    
    def get_main_sandbox(self):
        return self.main_sandbox
    
    
    ##                                      ##
    ##          Transition Functions        ##
    ##                                      ##
    
    def transition_to_ready(self):
        assert self.state == NodeState.INIT
        self.state = NodeState.READY
        # Initialize data structures here

    def transition_to_executing(self):
        assert self.state == NodeState.READY
        self.state = NodeState.EXECUTING
        # TODO

    def transition_to_spec_executing(self):
        assert self.state == NodeState.READY
        self.state = NodeState.SPEC_EXECUTING
        # TODO

    def transition_to_committed(self):
        assert self.state in [NodeState.EXECUTING, NodeState.SPECULATED]
        self.state = NodeState.COMMITTED
        # TODO

    # TODO: other transition functions


    # Do we need this here of should we handle everything on scheduler server and ppo?
    def handle_event(self, event_msg):
        pass # TODO
