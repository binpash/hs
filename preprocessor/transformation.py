"""
Transformation state for AST preprocessing.

This module provides the transformation state used during preprocessing
to track dataflow regions, loop contexts, and the control flow graph
for the speculative scheduler.
"""

from enum import Enum, auto
import os

from shasta.ast_node import AstNode
from shasta.json_to_ast import to_ast_node

from ast_util import string_to_argument, make_command
from parse import from_ast_objects_to_shell
import spec_util
from util import ptempfile


RUNTIME_EXECUTABLE = os.path.join(
    os.environ.get("PASH_SPEC_TOP", ""), "jit_runtime/jit.sh"
)


# === CFG classes for basic block tracking ===


class EdgeReason(Enum):
    """CFG edge types — names must match CFGEdgeType in parallel-orch/node.py"""
    IF_TAKEN = auto()
    ELSE_TAKEN = auto()
    LOOP_TAKEN = auto()
    LOOP_SKIP = auto()
    LOOP_BACK = auto()
    LOOP_BEGIN = auto()
    LOOP_END = auto()
    OTHER = auto()


class ShellBB:
    def __init__(self, num: int):
        self.num = num


class ShellLoopContext:
    def __init__(self, test_block, next_block):
        self.test_block = test_block
        self.next_block = next_block


class ShellIfContext:
    def __init__(self, test_block, next_block, has_else=False):
        self.test_block = test_block
        self.next_block = next_block
        self.has_else = has_else


class ShellProg:
    """Control flow graph for shell programs.

    Tracks basic blocks and edges during AST preprocessing,
    used by the speculative scheduler to understand program structure.
    """

    def __init__(self):
        self.bbs = [ShellBB(0)]
        self.current_bb = 0
        self.edges = {}  # {from_bb: {to_bb: (EdgeReason, aux_info)}}
        self.contexts = []

    def add_bb(self) -> int:
        next_bb = len(self.bbs)
        self.bbs.append(ShellBB(next_bb))
        return next_bb

    def add_edge(self, from_bb, to_bb, label, aux_info=""):
        if from_bb not in self.edges:
            self.edges[from_bb] = {}
        self.edges[from_bb][to_bb] = (label, aux_info)

    def enter_for(self, it_name=""):
        test_bb = self.add_bb()
        self.add_edge(self.current_bb, test_bb, EdgeReason.LOOP_BEGIN)
        next_bb = self.add_bb()
        self.add_edge(test_bb, next_bb, EdgeReason.LOOP_SKIP)
        body_bb = self.add_bb()
        self.add_edge(test_bb, body_bb, EdgeReason.LOOP_TAKEN, aux_info=it_name)
        self.contexts.append(ShellLoopContext(test_bb, next_bb))
        self.current_bb = body_bb

    def leave_for(self):
        ctx = self.contexts.pop()
        assert isinstance(ctx, ShellLoopContext)
        self.add_edge(self.current_bb, ctx.test_block, EdgeReason.LOOP_BACK)
        self.current_bb = ctx.next_block

    def enter_if(self):
        test_bb = self.current_bb
        next_bb = self.add_bb()
        body_bb = self.add_bb()
        self.add_edge(test_bb, body_bb, EdgeReason.IF_TAKEN)
        self.contexts.append(ShellIfContext(test_bb, next_bb))
        self.current_bb = body_bb

    def enter_else(self):
        ctx = self.contexts.pop()
        assert isinstance(ctx, ShellIfContext)
        self.add_edge(self.current_bb, ctx.next_block, EdgeReason.OTHER)
        else_bb = self.add_bb()
        self.add_edge(ctx.test_block, else_bb, EdgeReason.ELSE_TAKEN)
        self.contexts.append(ShellIfContext(ctx.test_block, ctx.next_block, has_else=True))
        self.current_bb = else_bb

    def leave_if(self):
        ctx = self.contexts.pop()
        assert isinstance(ctx, ShellIfContext)
        if not ctx.has_else:
            self.add_edge(ctx.test_block, ctx.next_block, EdgeReason.ELSE_TAKEN)
        self.add_edge(self.current_bb, ctx.next_block, EdgeReason.OTHER)
        self.current_bb = ctx.next_block

    def add_break(self):
        for ctx in reversed(self.contexts):
            if isinstance(ctx, ShellLoopContext):
                self.add_edge(self.current_bb, ctx.next_block, EdgeReason.LOOP_END)
                return
        assert False, "break outside loop"


class TransformationState:
    """Transformation state for speculative execution preprocessing."""

    def __init__(self, po_file: str):
        self._node_counter = 0
        self._loop_counter = 0
        self._loop_contexts = []
        self.partial_order_file = po_file
        self.partial_order_edges = []
        self.partial_order_node_loop_contexts = {}
        self.prog = ShellProg()
        self.var_assignment_nodes = set()

    # Node id related
    def get_next_id(self):
        new_id = self._node_counter
        self._node_counter += 1
        return new_id

    def get_current_id(self):
        return self._node_counter - 1

    def get_number_of_ids(self):
        return self._node_counter

    # Loop id related
    def get_next_loop_id(self):
        new_id = self._loop_counter
        self._loop_counter += 1
        return new_id

    def get_current_loop_context(self):
        return self._loop_contexts[:]

    def get_current_loop_id(self):
        if len(self._loop_contexts) == 0:
            return None
        else:
            return self._loop_contexts[0]

    def enter_loop(self, it_name=None):
        new_loop_id = self.get_next_loop_id()
        self._loop_contexts.insert(0, new_loop_id)
        self.prog.enter_for(it_name or "")
        return new_loop_id

    def exit_loop(self):
        self.prog.leave_for()
        self._loop_contexts.pop(0)

    def enter_if(self):
        self.prog.enter_if()

    def enter_else(self):
        self.prog.enter_else()

    def exit_if(self):
        self.prog.leave_if()

    def replace_df_region(
        self, asts, disable_parallel_pipelines=False, ast_text=None
    ) -> AstNode:
        text_to_output = get_shell_from_ast(asts, ast_text=ast_text)
        df_region_id = self.get_next_id()

        loop_id = self.get_current_loop_id()

        # Detect variable assignments (IFS modifications) for scheduler marking
        text_stripped = text_to_output.strip()
        if text_stripped.startswith('IFS=') or text_stripped.startswith('unset IFS'):
            self.mark_node_as_var_assignment(df_region_id)

        # Determine predecessors
        if df_region_id == 0:
            predecessors = []
        else:
            predecessors = [df_region_id - 1]

        spec_util.save_df_region(text_to_output, self, df_region_id, predecessors)
        replaced_node = self._make_call_to_runtime(df_region_id, loop_id)
        return to_ast_node(replaced_node)

    def get_partial_order_file(self):
        return self.partial_order_file

    def add_edge(self, from_id: int, to_id: int):
        self.partial_order_edges.append((from_id, to_id))

    def get_all_edges(self):
        return self.partial_order_edges

    def add_node_loop_context(self, node_id: int, loop_contexts):
        self.partial_order_node_loop_contexts[node_id] = loop_contexts

    def get_all_loop_contexts(self):
        return self.partial_order_node_loop_contexts

    def mark_node_as_var_assignment(self, node_id: int):
        self.var_assignment_nodes.add(node_id)

    def get_var_nodes(self):
        return self.var_assignment_nodes

    def get_number_of_var_assignments(self):
        return len(self.var_assignment_nodes)

    @staticmethod
    def _make_call_to_runtime(command_id: int, loop_id) -> AstNode:
        """Make a call to the speculative runtime."""
        assignments = [["pash_spec_command_id", string_to_argument(str(command_id))]]
        if loop_id is None:
            loop_id_str = ""
        else:
            loop_id_str = str(loop_id)

        assignments.append(["pash_spec_loop_id", string_to_argument(loop_id_str)])

        arguments = [
            string_to_argument("source"),
            string_to_argument(RUNTIME_EXECUTABLE),
        ]
        runtime_node = make_command(arguments, assignments=assignments)
        return runtime_node


def get_shell_from_ast(asts, ast_text=None) -> str:
    """Get shell text from AST, using original text if available."""
    if ast_text is None:
        text_to_output = from_ast_objects_to_shell(asts)
    else:
        text_to_output = ast_text
    return text_to_output
