import copy
import logging
import re
import executor
import trace_v2
import util
import signal
from dataclasses import dataclass
from subprocess import Popen
from typing import Tuple
from enum import Enum, auto
import util

class ConcreteNodeState(Enum):
    INIT = auto()
    READY = auto()
    COMMITTED = auto()
    STOP = auto()
    SPECULATED = auto()
    EXECUTING = auto()
    SPEC_EXECUTING = auto()
    UNSAFE = auto()

def state_pstr(state: ConcreteNodeState):
    same_length_state_str = {
        ConcreteNodeState.INIT:           '  INIT',
        ConcreteNodeState.READY:          ' READY',
        ConcreteNodeState.COMMITTED:      'COMMIT',
        ConcreteNodeState.STOP:           '  STOP',
        ConcreteNodeState.SPECULATED:     'SPEC_F',
        ConcreteNodeState.EXECUTING:      '   EXE',
        ConcreteNodeState.SPEC_EXECUTING: 'SPEC_E',
        ConcreteNodeState.UNSAFE:         'UNSAFE'
    }
    return same_length_state_str[state]

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

    def has_conflict(self, other: 'RWSet') -> bool:
        if (self.write_set.intersection(other.read_set) or
            self.read_set.intersection(other.write_set) or
            self.write_set.intersection(other.write_set)):
            return True
        else:
            return False

    def get_conflict(self, other: 'RWSet') -> set:
        return self.write_set.intersection(other.read_set).union(
            self.read_set.intersection(other.write_set)).union(
                self.write_set.intersection(other.write_set))
        
    def __str__(self):
        return f"RW(R:{self.get_read_set()}, W:{self.get_write_set()})"

## This class is used for both loop contexts and loop iters
## The indices go from inner to outer
class LoopStack:
    def __init__(self, loop_contexts_or_iters=None):
        if loop_contexts_or_iters is None:
            self.loops = []
        else:
            self.loops = loop_contexts_or_iters

    def is_empty(self):
        return len(self.loops) == 0

    def __len__(self):
        return len(self.loops)

    ## Generates a new loop stack with the same length but 0s as values
    def new_zeroed_loop_stack(self):
        return [0 for i in self.loops]

    def get_outer(self):
        return self.loops[-1]

    def pop_outer(self):
        return self.loops.pop()
    
    def add_inner(self, loop_iter_id: int):
        self.loops.insert(0, loop_iter_id)

    def outer_to_inner(self):
        return self.loops[::-1]

    def index(self, loop_iter_id: int) -> int:
        return self.loops.index(loop_iter_id)

    def get(self, index: int):
        return self.loops[index]

    def __repr__(self):
        ## TODO: Represent it using 'it', 'it0', 'it1', etc
        ##       or -(iters)- in front of it.
        output = "-".join([str(it) for it in self.loops])
        return output

    def __eq__(self, other):
        if not len(self.loops) == len(other.loops):
            return False
        for i in range(len(self.loops)):
            if not self.loops[i] == other.loops[i]:
                return False
        return True

class NodeId:
    
    def __init__(self, id: int, loop_iters=None):
        self.id = id
        
        if loop_iters is None:
            self.loop_iters = LoopStack()
        else:
            assert(isinstance(loop_iters, LoopStack))
            self.loop_iters = loop_iters

    def has_iters(self):
        return not self.loop_iters.is_empty()
    
    def get_iters(self):
        return copy.deepcopy(self.loop_iters)

    def get_non_iter_id(self):
        return NodeId(self.id)

    ## Returns a new NodeId
    def generate_new_node_id_with_another_iter(self, new_iter: int):
        ## This node already contains iterations for the outer loops potentially
        ##  so we just need to add another inner iteration
        new_iters = copy.deepcopy(self.loop_iters)
        new_iters.add_inner(new_iter)
        
        new_node_id = NodeId(self.id, new_iters)
        return new_node_id

    def __repr__(self):
        ## TODO: Represent it using n.
        output = f'{self.id}'
        if not self.loop_iters.is_empty():
            output += f'+{self.loop_iters}'
        return output

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return self.loop_iters == other.loop_iters and self.id == other.id

    def __ne__(self, other):
        # Not strictly necessary, but to avoid having both x==y and x!=y
        # True at the same time
        return not(self == other)
    
    ## TODO: Define this correctly if it is to be used for something other than dictionary indexing
    def __lt__(self, obj):
        return (str(self) < str(obj))
  
    def __gt__(self, obj):
        return (str(self) > str(obj))

    @staticmethod
    def parse_node_id(node_id_str: str):
        if "+" in node_id_str:
            node_id_int, iters_str = node_id_str.split("+")
            iters = [int(it) for it in iters_str.split("-")]
            return NodeId(int(node_id_int), LoopStack(iters))
        else:
            return NodeId(int(node_id_str), LoopStack())


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
    # The wait trace file for this node
    wait_env_file: str
    
    def __init__(self, node_id: NodeId, cmd: str, asts: "list[AstNode]"):
        self.id_ = node_id
        self.cmd = cmd
        self.asts = asts
        self.wait_env_file = None
    
# Extends parent node
class ConcreteNode(Node):
    state: ConcreteNodeState
    # Used for identifying the most recent valid execution
    exec_id: int
    # Nodes to check for fs dependencies before this node can be committed
    # for this particular execution of the main sandbox.
    # No need to do the same for the background sandbox since it will always get committed.
    to_be_resolved_snapshot: "set[NodeId]"
    # Read and write sets for this node
    rwset: RWSet
    # This can only be set while in the frontier and the background node execution is enabled
    # TODO: For now ignore this. Maybe there is a better way to do this.
    # background_sandbox: Sandbox
    exec_ctxt: ExecCtxt
    exec_result: ExecResult
    loop_contexts: LoopStack
    
    def __init__(self, node_id: NodeId, cmd: str, asts: "list[AstNode]", loop_context=None):
        super().__init__(node_id, cmd, asts)
        self.state = ConcreteNodeState.INIT
        self.exec_id = None
        self.to_be_resolved_snapshot = set()
        self.rwset = RWSet(set(), set())
        self.exec_ctxt = None
        self.exec_result = None
        self.loop_context = loop_context

    def __str__(self):
        return f'ConcreteNode(id:{self.id_}, cmd:{self.cmd}, state:{self.state}, rwset:{self.rwset}, to_be_resolved_snapshot:{self.to_be_resolved_snapshot}, wait_env_file:{self.wait_env_file}, exec_ctxt:{self.exec_ctxt})'
    
    def __repr__(self):
        return str(self)

    def pretty_state_repr(self):
        return f'{state_pstr(self.state)} {self.cmd}'
    
    def is_initialized(self):
        return self.state == ConcreteNodeState.INIT
    
    def is_ready(self):
        return self.state == ConcreteNodeState.READY
    
    def is_committed(self):
        return self.state == ConcreteNodeState.COMMITTED
    
    def is_stopped(self):
        return self.state == ConcreteNodeState.STOP
    
    def is_speculated(self):
        return self.state == ConcreteNodeState.SPECULATED

    def is_executing(self):
        return self.state == ConcreteNodeState.EXECUTING
    
    def is_spec_executing(self):
        return self.state == ConcreteNodeState.SPEC_EXECUTING
    
    def is_unsafe(self):
        return self.state == ConcreteNodeState.UNSAFE

    def start_command(self, env_file: str, speculate=False):
        # TODO: implement speculate
        # TODO: built-in commands
        cmd = self.cmd
        execute_func = executor.async_run_and_trace_command_return_trace
        # Set the execution id
        self.exec_id = util.generate_id()
        self.exec_ctxt = ExecCtxt(*execute_func(cmd, self.id_, self.exec_id, env_file))

    def execution_outcome(self) -> Tuple[int, str, str]:
        assert self.exec_result is not None
        return self.exec_result.exit_code, self.exec_ctxt.post_env_file, self.exec_ctxt.stdout


    ##                                      ##
    ##          Transition Functions        ##
    ##                                      ##
    
    def transition_from_init_to_ready(self):
        assert self.state == ConcreteNodeState.INIT
        self.state = ConcreteNodeState.READY
        # Also, probably unroll here?

    def kill(self):
        assert self.state in [ConcreteNodeState.EXECUTING, ConcreteNodeState.SPEC_EXECUTING]
        self.exec_ctxt.process.kill()

    def reset_to_ready(self):
        assert self.state in [ConcreteNodeState.EXECUTING, ConcreteNodeState.SPEC_EXECUTING,
                              ConcreteNodeState.SPECULATED]
        
        logging.info(f"Resetting node {self.id_} to ready {self.exec_id}")
        # We reset the exec id so if we receive a message 
        # due to a race condition, we will ignore it.
        self.exec_id = None
        
        # TODO: make this more sophisticated
        if self.state in [ConcreteNodeState.EXECUTING, ConcreteNodeState.SPEC_EXECUTING]:
            self.kill()
        
        # Probably delete them from tmpfs too
        process = self.exec_ctxt.process
        if process.poll() is None:
            # Exceptions will be handled inside the call so we don't have to worry
            util.kill_process_tree(process.pid, sig=signal.SIGKILL)

        self.exec_ctxt = None
        self.exec_result = None
        self.state = ConcreteNodeState.READY


    def start_executing(self, env_file):
        assert self.state == ConcreteNodeState.READY
        self.start_command(env_file)
        self.state = ConcreteNodeState.EXECUTING

    def start_spec_executing(self, env_file):
        assert self.state == ConcreteNodeState.READY
        self.start_command(env_file, speculate=True)
        self.state = ConcreteNodeState.SPEC_EXECUTING
        
    def commit_frontier_execution(self):
        assert self.state == ConcreteNodeState.EXECUTING
        self.exec_result = ExecResult(self.exec_ctxt.process.pid, self.exec_ctxt.process.returncode)
        self.gather_fs_actions()
        executor.commit_workspace(self.exec_ctxt.sandbox_dir)
        self.state = ConcreteNodeState.COMMITTED

    def finish_spec_execution(self):
        assert self.state == ConcreteNodeState.SPEC_EXECUTING
        self.exec_result = ExecResult(self.exec_ctxt.process.pid, self.exec_ctxt.process.returncode)
        self.gather_fs_actions()
        self.state = ConcreteNodeState.SPECULATED


    def commit_speculated(self):
        assert self.state == ConcreteNodeState.SPECULATED
        executor.commit_workspace(self.exec_ctxt.sandbox_dir)
        self.state = ConcreteNodeState.COMMITTED

    def transition_from_stopped_to_executing(self, env_file=None):
        assert self.state == ConcreteNodeState.READY
        self.state = ConcreteNodeState.EXECUTING
        self._attempt_start_command(env_file)

    def transition_to_committed(self):
        assert self.state in ConcreteNodeState.SPECULATED
        self.state = ConcreteNodeState.COMMITTED
        # TODO

    def transition_from_spec_executing_to_speculated(self):
        pass


    def update_rw_set(self, rw_set):
        self.rwset = rw_set

    def gather_fs_actions(self) -> RWSet:
        assert self.state in [ConcreteNodeState.EXECUTING, ConcreteNodeState.SPEC_EXECUTING]
        sandbox_dir = self.exec_ctxt.sandbox_dir
        trace_file = self.exec_ctxt.trace_file
        try:
            trace_object = executor.read_trace(sandbox_dir, trace_file)
        except FileNotFoundError:
            self.update_rw_set(RWSet(set(), set()))
            return
        read_set, write_set = trace_v2.parse_and_gather_cmd_rw_sets(trace_object)
        rw_set = RWSet(read_set, write_set)
        self.update_rw_set(rw_set)

    def get_rw_set(self):
        # if self.state in [ConcreteNodeState.EXECUTING, ConcreteNodeState.SPEC_EXECUTING]:
        #     self.gather_fs_actions()
        return self.rwset

    def has_env_conflict_with(self, other_env) -> bool:
        # Early return if paths are the same
        if self.exec_ctxt.pre_env_file == other_env:
            return False

        ignore_vars = set(['RANDOM'])  
        
        re_scalar_string = re.compile(r'declare (?:-x|--)? (\w+)="([^"]*)"')
        re_scalar_int = re.compile(r'declare -i (\w+)="(\d+)"')
        re_array = re.compile(r'declare -a (\w+)=(\([^)]+\))')

        def parse_env(content):
            env_vars = {}
            for line in content.splitlines():
                if line.startswith('#') or not line.strip():
                    continue
                for regex in [re_scalar_string, re_scalar_int, re_array]:
                    match = regex.match(line)
                    if match:
                        key, value = match.groups()
                        if key not in ignore_vars:
                            env_vars[key] = value
            return env_vars

        with open(self.exec_ctxt.pre_env_file, 'r') as file:
            node_env_vars = parse_env(file.read())

        with open(other_env, 'r') as file:
            other_env_vars = parse_env(file.read())
        return node_env_vars != other_env_vars
