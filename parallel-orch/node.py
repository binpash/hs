from itertools import chain
from enum import Enum, auto
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
import analysis

class NodeState(Enum):
    INIT = auto()
    READY = auto()
    COMMITTED = auto()
    STOP = auto()
    SPECULATED = auto()
    EXECUTING = auto()
    SPEC_EXECUTING = auto()
    UNSAFE = auto()

def state_pstr(state: NodeState):
    same_length_state_str = {
        NodeState.INIT:           '  INIT',
        NodeState.READY:          ' READY',
        NodeState.COMMITTED:      'COMMIT',
        NodeState.STOP:           '  STOP',
        NodeState.SPECULATED:     'SPEC_F',
        NodeState.EXECUTING:      '   EXE',
        NodeState.SPEC_EXECUTING: 'SPEC_E',
        NodeState.UNSAFE:         'UNSAFE'
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


class NodeId:
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

class LoopStack:
    def __init__(self, loop_contexts_or_iters=None):
        if loop_contexts_or_iters is None:
            self.loops = []
        else:
            self.loops = loop_contexts_or_iters

    def __repr__(self):
        ## TODO: Represent it using 'it', 'it0', 'it1', etc
        ##       or -(iters)- in front of it.
        output = "-".join([str(it) for it in self.loops])
        return output
    def __eq__(self, other):
        return self.loops == other.loops

@dataclass
class Node:
    id_: NodeId
    cmd: str
    asts: "list[AstNode]"
    basic_block_id: int

    def __init__(self, id_, cmd, asts, basic_block_id):
        self.id_ = id_
        self.cmd = cmd
        self.asts = asts
        self.basic_block_id = basic_block_id

class ConcreteNodeId:
    def __init__(self, node_id: NodeId, loop_iters = list()):
        self.node_id = node_id
        self.loop_iters = tuple(loop_iters)

    def __repr__(self):
        return f'cnid({self.node_id.id_})'

    def __hash__(self):
        return hash((self.node_id, self.loop_iters))

    def __eq__(self, other):
        return self.node_id == other.node_id and self.loop_iters == other.loop_iters

    def __str__(self):
        return f'{self.node_id}@' + ''.join(['-' + str(n) for n in self.loop_iters])

    def do_action(self, next_abstract_id: NodeId, edge_type: 'CFGEdgeType'):
        loop_iters_list = list(self.loop_iters)
        if edge_type == CFGEdgeType.LOOP_BACK:
            loop_iters_list[0] += 1
        elif edge_type == CFGEdgeType.LOOP_SKIP:
            loop_iters_list.pop(0)
        elif edge_type == CFGEdgeType.LOOP_BEGIN:
            loop_iters_list.insert(0, 1)
        elif edge_type == CFGEdgeType.LOOP_END:
            loop_iters_list.pop(0)
        return ConcreteNodeId(next_abstract_id, loop_iters_list)

    @staticmethod
    def parse(input_str):
        node_id_str, loop_iters_str = input_str.split('@')
        return ConcreteNodeId(NodeId(int(node_id_str)), [int(cnt) for cnt in loop_iters_str.split('-')[1:]])

class ConcreteNode:
    cnid: ConcreteNodeId
    abstract_node: Node
    state: NodeState
    # Used for identifying the most recent valid execution
    exec_id: int
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

    def __init__(self, cnid: ConcreteNodeId, node: Node):
        self.cnid = cnid
        self.abstract_node = node
        self.state = NodeState.INIT
        self.tracefile = None
        self.rwset = None
        self.wait_env_file = None
        self.to_be_resolved_snapshot = None
        self.exec_ctxt = None
        self.exec_id = None

    def __str__(self):
        return f'Node(id:{self.id_}, cmd:{self.cmd}, state:{self.state}, rwset:{self.rwset}, to_be_resolved_snapshot:{self.to_be_resolved_snapshot}, wait_env_file:{self.wait_env_file}, exec_ctxt:{self.exec_ctxt})'

    def __repr__(self):
        return str(self)

    @property
    def id_(self):
        return self.abstract_node.id_

    @property
    def cmd(self):
        return self.abstract_node.cmd

    @property
    def asts(self):
        return self.abstract_node.asts

    def pretty_state_repr(self):
        return f'{state_pstr(self.state)} {self.cmd} --- {self.cnid}'

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
        # Set the execution id
        self.exec_id = util.generate_id()
        self.exec_ctxt = ExecCtxt(*execute_func(cmd, self.cnid, self.exec_id, env_file))

    def execution_outcome(self) -> Tuple[int, str, str]:
        assert self.exec_result is not None
        return self.exec_result.exit_code, self.exec_ctxt.post_env_file, self.exec_ctxt.stdout

    def command_unsafe(self):
        return not analysis.safe_to_execute(self.asts, {})


    ##                                      ##
    ##          Transition Functions        ##
    ##                                      ##

    def transition_from_init_to_ready(self):
        assert self.state == NodeState.INIT
        self.state = NodeState.READY
        self.rwset = RWSet(set(), set())
        # Also, probably unroll here?

    def transition_from_ready_to_unsafe(self):
        assert self.state == NodeState.READY
        self.state = NodeState.UNSAFE

    def kill(self):
        assert self.state in [NodeState.EXECUTING, NodeState.SPEC_EXECUTING]
        self.exec_ctxt.process.kill()

    def try_reset_to_ready(self):
        if self.state in [NodeState.READY, NodeState.UNSAFE]:
            return
        else:
            self.reset_to_ready()
        
    def reset_to_ready(self):
        assert self.state in [NodeState.EXECUTING, NodeState.SPEC_EXECUTING,
                              NodeState.SPECULATED]

        logging.info(f"Resetting node {self.id_} to ready {self.exec_id}")
        # We reset the exec id so if we receive a message
        # due to a race condition, we will ignore it.
        self.exec_id = None

        # TODO: make this more sophisticated
        if self.state in [NodeState.EXECUTING, NodeState.SPEC_EXECUTING]:
            self.kill()

        # Probably delete them from tmpfs too
        process = self.exec_ctxt.process
        if process.poll() is None:
            # Exceptions will be handled inside the call so we don't have to worry
            util.kill_process_tree(process.pid, sig=signal.SIGKILL)

        self.exec_ctxt = None
        self.exec_result = None
        self.state = NodeState.READY


    def start_executing(self, env_file):
        assert self.state == NodeState.READY
        self.start_command(env_file)
        self.state = NodeState.EXECUTING

    def start_spec_executing(self, env_file):
        assert self.state == NodeState.READY
        self.start_command(env_file, speculate=True)
        self.state = NodeState.SPEC_EXECUTING

    def commit_frontier_execution(self):
        assert self.state == NodeState.EXECUTING
        self.exec_result = ExecResult(self.exec_ctxt.process.pid, self.exec_ctxt.process.returncode)
        self.gather_fs_actions()
        executor.commit_workspace(self.exec_ctxt.sandbox_dir)
        self.state = NodeState.COMMITTED

    def finish_spec_execution(self):
        assert self.state == NodeState.SPEC_EXECUTING
        self.exec_result = ExecResult(self.exec_ctxt.process.pid, self.exec_ctxt.process.returncode)
        self.gather_fs_actions()
        self.state = NodeState.SPECULATED


    def commit_speculated(self):
        assert self.state == NodeState.SPECULATED
        executor.commit_workspace(self.exec_ctxt.sandbox_dir)
        self.state = NodeState.COMMITTED

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

    def commit_unsafe_node(self):
        assert self.state == NodeState.UNSAFE
        self.state = NodeState.COMMITTED

    def update_rw_set(self, rw_set):
        self.rwset = rw_set

    def gather_fs_actions(self) -> RWSet:
        assert self.state in [NodeState.EXECUTING, NodeState.SPEC_EXECUTING]
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
        # if self.state in [NodeState.EXECUTING, NodeState.SPEC_EXECUTING]:
        #     self.gather_fs_actions()
        return self.rwset

    def has_env_conflict_with(self, other_env) -> bool:
        # Early return if paths are the same
        if self.exec_ctxt.pre_env_file == other_env:
            return False

        ignore_vars = set([
            "_", 'RANDOM', "msg", "pash_runtime_final_status", "pash_previous_set_status",
            "pash_runtime_shell_variables_file", "from_set", "output_variable_file",
            "pash_loop_iter_counters", "daemon_response", "vars_file",
            "pash_speculative_command_id", "prev_env", "PREVIOUS_SET_STATUS",
            "BASH_LINENO", "response_args", "stdout_file", "pash_spec_command_id",
            "cmd_exit_code", "pash_set_to_add", "POST_EXEC_ENV",
            "HISTCMD", "EXEC_MODE", "TRACE_FILE", "CMD_STRING",
            "CMD_ID", "STDOUT_FILE", "DIRSTACK", "SECONDS", "TMPDIR",
            "UPDATED_DIRS_AND_MOUNTS", "EPOCHSECONDS", "LATEST_ENV_FILE",
            "TRY_COMMAND", "SRANDOM", "speculate_flag", "EXECUTION_ID",
            "EPOCHREALTIME", "OLDPWD"
        ])
        

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

        logging.debug(f"Comparing env files {self.exec_ctxt.pre_env_file} and {other_env}")
        
        conflict_exists = False
        for key in set(node_env_vars.keys()).union(other_env_vars.keys()):
            if key not in node_env_vars:
                logging.debug(f"Variable {key} missing in node environment")
                conflict_exists = True
            elif key not in other_env_vars:
                logging.debug(f"Variable {key} missing in other environment")
                conflict_exists = True
            elif node_env_vars[key] != other_env_vars[key]:
                logging.debug(f"Variable {key} differs: node environment has {node_env_vars[key]}, other has {other_env_vars[key]}")
                conflict_exists = True

        return conflict_exists


class CFGEdgeType(Enum):
    IF_TAKEN = auto()
    ELSE_TAKEN = auto()
    LOOP_TAKEN = auto()
    LOOP_SKIP = auto()
    LOOP_BACK = auto()
    LOOP_BEGIN = auto()
    LOOP_END = auto()
    OTHER = auto()

class HSBasicBlock:
    def __init__(self, bb_id: int, nodes: list[Node]):
        self.bb_id = bb_id
        self.nodes = nodes

    def __str__(self):
        return ''.join([node.cmd.strip() + '\n' for node in self.nodes])

    @property
    def loop_context(self):
        return self.nodes[0].loop_context

    @property
    def node_ids(self):
        return [node.id_ for node in self.nodes]

    def get_node(self, node_id: NodeId) -> Node:
        nodes = [node for node in self.nodes if node.id_ == node_id]
        assert len(nodes) == 1
        return nodes[0]

class HSProg:
    basic_blocks: list[HSBasicBlock] = []
    block_adjacency: "dict[int, dict[int, CFGEdgeType]]"

    def __init__(self, basic_blocks: list, block_edges: list[tuple]):
        self.basic_blocks = [HSBasicBlock(i, []) for i, bb in enumerate(basic_blocks)]
        self.block_adjacency = {}
        for bb_id in range(len(basic_blocks)):
            self.block_adjacency[bb_id] = {}

        for from_bb, to_bb, edge_type in block_edges:
            self.block_adjacency[from_bb][to_bb] = CFGEdgeType[edge_type]

    def is_start_of_block(self, node_id: NodeId):
        for bb in self.basic_blocks:
            bb : HSBasicBlock
            if len(bb.nodes) and bb.nodes[0].id_ == node_id:
                return True
        return False

    def append_node_to(self, bb_id, node: Node):
        self.basic_blocks[bb_id].nodes.append(node)

    def find_basic_block(self, node_id: NodeId):
        for bb in self.basic_blocks:
            bb : HSBasicBlock
            for node in bb.nodes:
                if node.id_ == node_id:
                    return bb
        raise ValueError('no such node_id')

    def is_last_block(self, bb: HSBasicBlock):
        bb_id = self.basic_blocks.index(bb)
        if len(self.block_adjacency[bb_id]) == 0:
            return True
        else:
            return False

    def guess_next_block(self, bb: HSBasicBlock):
        bb_id = self.basic_blocks.index(bb)
        pick_dict = {}
        for next_bb_id, edge_type in self.block_adjacency[bb_id].items():
            pick_dict[edge_type] = next_bb_id
        for edge_type in [CFGEdgeType.LOOP_END, CFGEdgeType.LOOP_TAKEN, CFGEdgeType.LOOP_SKIP,
                          CFGEdgeType.LOOP_BACK, CFGEdgeType.LOOP_BEGIN,
                          CFGEdgeType.IF_TAKEN, CFGEdgeType.ELSE_TAKEN,
                          CFGEdgeType.OTHER]:
            if edge_type in pick_dict:
                return edge_type, self.basic_blocks[pick_dict[edge_type]]
        assert False

    def find_node(self, node_id):
        for bb in self.basic_blocks:
            for node in bb.nodes:
                if node.id_ == node_id:
                    return node
        raise ValueError('no such node_id')

    def __str__(self):
        return 'prog:\n' + '\n'.join(
            [f'block {i}:\n' + str(bb) + f'goto block {self.block_adjacency[i]}\n' for i, bb in enumerate(self.basic_blocks)])
