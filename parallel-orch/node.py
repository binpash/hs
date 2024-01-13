import logging
import executor
from dataclasses import dataclass
from subprocess import Popen
from typing import Tuple
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
    
    def __init__(self, id_: int):
        self.id_ = id_

    def get_non_iter_id(self):
        return NodeId(self.id_)

    def __repr__(self):
        ## TODO: Represent it using n.
        output = f'{self.id_}'
        return output

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        # return self.loop_iters == other.loop_iters and self.id == other.id
        return self.id_ == other.id_

    def __ne__(self, other):
        return not(self == other)

    def __lt__(self, obj):
        return (str(self) < str(obj))

    def __gt__(self, obj):
        return (str(self) > str(obj))

    @staticmethod
    def parse_node_id(node_id_str: str):
        return NodeId(int(node_id_str))

@dataclass
class ExecCtxt:
    process: Popen
    trace_file: str
    stdout: str
    stderr: str
    pre_env_file: str
    post_env_file: str
    sandbox_dir: str

@dataclass
class ExecResult:
    exit_code: int
    proc_id: int
    
    
class Node:
    id_: NodeId
    cmd: str
    asts: "list[AstNode]"
    state: NodeState
    # Nodes to check for fs dependencies before this node can be committed
    # for this particular execution of the main sandbox.
    # No need to do the same for the background sandbox since it will always get committed.
    to_be_resolved_snapshot: "set[NodeId]"
    # Read and write sets for this node
    rwset: RWSet
    # The wait trace file for this node
    wait_env_file: str
    # This can only be set while in the frontier and the background node execution is enabled
    # TODO: For now ignore this. Maybe there is a better way to do this.
    # background_sandbox: Sandbox
    exec_ctxt: ExecCtxt
    exec_result: ExecResult
    
    def __init__(self, node_id: NodeId, cmd: str, asts: "list[AstNode]"):
        self.id_ = node_id
        self.cmd = cmd
        self.asts = asts
        self.state = NodeState.INIT
        self.tracefile = None
        self.rwset = None
        self.wait_env_file = None
        self.to_be_resolved_snapshot = None
        self.exec_ctxt = None

    def __str__(self):
        return f'Node(id:{self.id_}, cmd:{self.cmd}, state:{self.state}, rwset:{self.rwset}, to_be_resolved_snapshot:{self.to_be_resolved_snapshot}, wait_env_file:{self.wait_env_file}, exec_ctxt:{self.exec_ctxt})'
    
    def __repr__(self):
        return str(self)

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

    def start_command(self, env_file: str, speculate=False):
        # TODO: implement speculate
        # TODO: built-in commands
        cmd = self.cmd
        execute_func = executor.async_run_and_trace_command_return_trace
        self.exec_ctxt = ExecCtxt(*execute_func(cmd, self.id_, env_file))

    def execution_outcome(self) -> Tuple[int, str, str]:
        assert self.exec_result is not None
        return self.exec_result.exit_code, self.exec_ctxt.post_env_file, self.exec_ctxt.stdout
        
    ##                                      ##
    ##          Transition Functions        ##
    ##                                      ##
    
    def transition_from_init_to_ready(self):
        assert self.state == NodeState.INIT
        self.state = NodeState.READY
        # Initialize data structures here

        # Also, probably unroll here?

    def start_executing(self, env_file):
        assert self.state == NodeState.READY
        self.start_command(env_file)
        self.state = NodeState.EXECUTING

    def commit_frontier_execution(self):
        assert self.state in [NodeState.EXECUTING, NodeState.SPEC_EXECUTING]
        self.state = NodeState.COMMITTED
        self.exec_result = ExecResult(self.exec_ctxt.process.pid, self.exec_ctxt.process.returncode)
        executor.commit_workspace(self.exec_ctxt.sandbox_dir)
        

    def _attempt_start_command(self, env_file, speculate=False):
        if self.wait_env_file is not None:
            self.start_command(env_file=self.wait_env_file, speculate=speculate)
        elif env_file is not None:
            self.start_command(env_file=env_file, speculate=speculate)
        else:
            logging.error(f'Error: No valid execution env for Node {self.id_}')

    def transition_from_ready_to_executing(self, env_file=None):
        assert self.state == NodeState.READY
        self.state = NodeState.EXECUTING
        self._attempt_start_command(env_file)

    def transition_from_ready_to_spec_executing(self, env_file=None):
        assert self.state == NodeState.READY
        self.state = NodeState.SPEC_EXECUTING
        self._attempt_start_command(env_file, speculate=True)

    def transition_from_stopped_to_executing(self, env_file=None):
        assert self.state == NodeState.READY
        self.state = NodeState.EXECUTING
        self._attempt_start_command(env_file)

    def transition_to_committed(self):
        assert self.state in NodeState.SPECULATED
        self.state = NodeState.COMMITTED
        # TODO

    def transition_from_spec_executing_to_speculated(self):
        pass

    def set_wait_env_file(self, env_file: str):
        assert self.state in [NodeState.READY, NodeState.EXECUTING, NodeState.SPEC_EXECUTING, NodeState.STOP, NodeState.SPECULATED]
        self.post_env_file = env_file
    