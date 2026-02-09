"""
AST to AST transformation using CommandVisitor.

The preprocessing pass replaces all _candidate_ dataflow regions with
calls to PaSh's runtime to let it establish if they are actually dataflow
regions. The pass serializes all candidate dataflow regions:
- A list of ASTs if at the top level or
- an AST subtree if at a lower level

The PaSh runtime then deserializes them, compiles them (if safe) and optimizes them.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any

from shasta.ast_node import (
    AstNode,
    PipeNode,
    CommandNode,
    BackgroundNode,
    RedirNode,
    SubshellNode,
    SemiNode,
    AndNode,
    OrNode,
    NotNode,
    IfNode,
    ForNode,
    WhileNode,
    CaseNode,
    DefunNode,
    ArithNode,
    CondNode,
    SelectNode,
    ArithForNode,
    CoprocNode,
    TimeNode,
    GroupNode,
)
from shasta.ast_walker import CommandVisitor

from ast_util import PreprocessedAST, UnparsedScript, unzip
from loop_tracking import for_node_with_loop_tracking


@dataclass
class PreprocessContext:
    """Context threaded through preprocessing traversal."""

    trans_options: Any  # TransformationState
    last_object: bool = False


@dataclass
class NodeResult:
    """Result from processing a single node."""

    ast: AstNode
    replace_whole: bool = False
    non_maximal: bool = False
    something_replaced: bool = False

    def to_preprocessed_ast(self, last_ast: bool) -> PreprocessedAST:
        """Convert to PreprocessedAST for API compatibility."""
        return PreprocessedAST(
            ast=self.ast,
            replace_whole=self.replace_whole,
            non_maximal=self.non_maximal,
            something_replaced=self.something_replaced,
            last_ast=last_ast,
        )


class PreprocessVisitor(CommandVisitor):
    """
    Preprocessing visitor that identifies candidate dataflow regions.

    Subclasses CommandVisitor from shasta.ast_walker, adding close-node
    semantics for control flow children that cannot be part of the
    parent's dataflow region.
    """

    def __init__(self, ctx: PreprocessContext):
        self.ctx = ctx

    def walk(self, node: AstNode) -> PreprocessedAST:
        """Walk and preprocess an AST node, returning PreprocessedAST."""
        result = self._dispatch(node)
        return result.to_preprocessed_ast(self.ctx.last_object)

    def walk_close(self, node: AstNode) -> tuple[AstNode, bool]:
        """
        Walk a node with "close" semantics.

        Used for children that cannot be part of the parent's dataflow
        region (e.g., children of control flow constructs).
        """
        preprocessed = self.walk(node)

        if preprocessed.should_replace_whole_ast():
            final_ast = self.ctx.trans_options.replace_df_region(
                asts=[preprocessed.ast],
                disable_parallel_pipelines=self.ctx.last_object,
            )
            return final_ast, True
        else:
            return preprocessed.ast, preprocessed.will_anything_be_replaced()

    def _dispatch(self, node: AstNode) -> NodeResult:
        """Dispatch to the appropriate visit method."""
        method_name = f"visit_{type(node).NodeName.lower()}"
        method = getattr(self, method_name, None)
        if method is not None:
            return method(node)
        raise ValueError(f"Unknown node type: {type(node).NodeName}")

    # === Leaf replacement nodes ===

    def visit_pipe(self, node: PipeNode) -> NodeResult:
        return NodeResult(
            ast=node,
            replace_whole=True,
            non_maximal=node.is_background,
            something_replaced=True,
        )

    def visit_command(self, node: CommandNode) -> NodeResult:
        if len(node.arguments) == 0:
            # Assignment-only command — always treat as replaceable
            return NodeResult(ast=node, replace_whole=True, something_replaced=True)
        return NodeResult(ast=node, replace_whole=True, something_replaced=True)

    def visit_background(self, node: BackgroundNode) -> NodeResult:
        return NodeResult(
            ast=node,
            replace_whole=True,
            non_maximal=True,
            something_replaced=True,
        )

    # === Binary operators with close-node semantics ===

    def visit_semi(self, node: SemiNode) -> NodeResult:
        return self._walk_binary_close(node, "left_operand", "right_operand")

    def visit_and(self, node: AndNode) -> NodeResult:
        return self._walk_binary_close(node, "left_operand", "right_operand")

    def visit_or(self, node: OrNode) -> NodeResult:
        return self._walk_binary_close(node, "left_operand", "right_operand")

    # === Single-child close nodes ===

    def visit_redir(self, node: RedirNode) -> NodeResult:
        return self._walk_single_close(node, "node")

    def visit_subshell(self, node: SubshellNode) -> NodeResult:
        return self._walk_single_close(node, "body")

    def visit_not(self, node: NotNode) -> NodeResult:
        return self._walk_single_close(node, "body")

    def visit_group(self, node: GroupNode) -> NodeResult:
        return self._walk_single_close(node, "body")

    def visit_coproc(self, node: CoprocNode) -> NodeResult:
        return self._walk_single_close(node, "body")

    def visit_time(self, node: TimeNode) -> NodeResult:
        return self._walk_single_close(node, "command")

    def visit_select(self, node: SelectNode) -> NodeResult:
        return self._walk_single_close(node, "body")

    def visit_arithfor(self, node: ArithForNode) -> NodeResult:
        return self._walk_single_close(node, "action")

    # === Control flow with multiple children ===

    def visit_while(self, node: WhileNode) -> NodeResult:
        self.ctx.trans_options.enter_loop()

        new_test, test_replaced = self.walk_close(node.test)
        new_body, body_replaced = self.walk_close(node.body)

        node.test = new_test
        node.body = new_body

        self.ctx.trans_options.exit_loop()

        return NodeResult(
            ast=node, something_replaced=test_replaced or body_replaced
        )

    def visit_for(self, node: ForNode) -> NodeResult:
        return for_node_with_loop_tracking(node, self.ctx, self)

    def visit_if(self, node: IfNode) -> NodeResult:
        new_cond, cond_replaced = self.walk_close(node.cond)

        self.ctx.trans_options.enter_if()
        new_then, then_replaced = self.walk_close(node.then_b)

        if node.else_b is not None:
            self.ctx.trans_options.enter_else()
            new_else, else_replaced = self.walk_close(node.else_b)
        else:
            new_else, else_replaced = None, False

        self.ctx.trans_options.exit_if()

        node.cond = new_cond
        node.then_b = new_then
        node.else_b = new_else

        return NodeResult(
            ast=node,
            something_replaced=cond_replaced or then_replaced or else_replaced,
        )

    def visit_case(self, node: CaseNode) -> NodeResult:
        any_replaced = False
        new_cases = []

        for case in node.cases:
            if case.get("cbody") is not None:
                new_body, replaced = self.walk_close(case["cbody"])
                case["cbody"] = new_body
                any_replaced = any_replaced or replaced
            new_cases.append(case)

        node.cases = new_cases
        return NodeResult(ast=node, something_replaced=any_replaced)

    def visit_cond(self, node: CondNode) -> NodeResult:
        replaced_left = False
        replaced_right = False

        if node.left is not None:
            node.left, replaced_left = self.walk_close(node.left)
        if node.right is not None:
            node.right, replaced_right = self.walk_close(node.right)

        return NodeResult(
            ast=node, something_replaced=replaced_left or replaced_right
        )

    # === No-op nodes ===

    def visit_defun(self, node: DefunNode) -> NodeResult:
        return NodeResult(ast=node, something_replaced=False)

    def visit_arith(self, node: ArithNode) -> NodeResult:
        return NodeResult(ast=node, something_replaced=False)

    # === Helper methods ===

    def _walk_single_close(self, node: AstNode, child_attr: str) -> NodeResult:
        """Walk a node with a single child using close-node semantics."""
        child = getattr(node, child_attr)
        new_child, replaced = self.walk_close(child)
        setattr(node, child_attr, new_child)
        return NodeResult(ast=node, something_replaced=replaced)

    def _walk_binary_close(
        self, node: AstNode, left_attr: str, right_attr: str
    ) -> NodeResult:
        """Walk a binary node with close-node semantics on both children."""
        left = getattr(node, left_attr)
        right = getattr(node, right_attr)

        new_left, replaced_left = self.walk_close(left)
        new_right, replaced_right = self.walk_close(right)

        setattr(node, left_attr, new_left)
        setattr(node, right_attr, new_right)

        return NodeResult(
            ast=node, something_replaced=replaced_left or replaced_right
        )


# === Public API ===


def preprocess_node(
    ast_node: AstNode,
    trans_options,
    last_object: bool,
) -> PreprocessedAST:
    """
    Preprocesses an AstNode by dispatching to the appropriate visitor method.

    This is the main entry point for preprocessing a single node.
    """
    ctx = PreprocessContext(trans_options=trans_options, last_object=last_object)
    visitor = PreprocessVisitor(ctx)
    return visitor.walk(ast_node)


def replace_ast_regions(ast_objects, trans_options):
    """
    Replace candidate dataflow AST regions with calls to PaSh's runtime.
    """
    preprocessed_asts = []
    candidate_dataflow_region = []
    last_object = False
    for i, ast_object in enumerate(ast_objects):
        if i == len(ast_objects) - 1:
            last_object = True

        ast, original_text, _linno_before, _linno_after = ast_object
        assert isinstance(ast, AstNode)

        preprocessed_ast_object = preprocess_node(
            ast, trans_options, last_object=last_object
        )
        assert (
            not preprocessed_ast_object.is_non_maximal()
            or preprocessed_ast_object.should_replace_whole_ast()
        )
        assert (
            not preprocessed_ast_object.should_replace_whole_ast()
            or preprocessed_ast_object.will_anything_be_replaced()
        )

        if preprocessed_ast_object.is_non_maximal():
            candidate_dataflow_region.append(
                (preprocessed_ast_object.ast, original_text)
            )
        else:
            if len(candidate_dataflow_region) > 0:
                candidate_dataflow_region.append(
                    (preprocessed_ast_object.ast, original_text)
                )
                dataflow_region_asts, dataflow_region_lines = unzip(
                    candidate_dataflow_region
                )
                dataflow_region_text = _join_original_text_lines(dataflow_region_lines)
                replaced_ast = trans_options.replace_df_region(
                    dataflow_region_asts,
                    ast_text=dataflow_region_text,
                    disable_parallel_pipelines=last_object,
                )
                candidate_dataflow_region = []
                preprocessed_asts.append(replaced_ast)
            else:
                if preprocessed_ast_object.should_replace_whole_ast():
                    replaced_ast = trans_options.replace_df_region(
                        [preprocessed_ast_object.ast],
                        ast_text=original_text,
                        disable_parallel_pipelines=last_object,
                    )
                    preprocessed_asts.append(replaced_ast)
                else:
                    if (
                        preprocessed_ast_object.will_anything_be_replaced()
                        or original_text is None
                    ):
                        preprocessed_asts.append(preprocessed_ast_object.ast)
                    else:
                        preprocessed_asts.append(UnparsedScript(original_text))

    # Close the final dataflow region
    if len(candidate_dataflow_region) > 0:
        dataflow_region_asts, dataflow_region_lines = unzip(candidate_dataflow_region)
        dataflow_region_text = _join_original_text_lines(dataflow_region_lines)
        replaced_ast = trans_options.replace_df_region(
            dataflow_region_asts,
            ast_text=dataflow_region_text,
            disable_parallel_pipelines=True,
        )
        preprocessed_asts.append(replaced_ast)

    return preprocessed_asts


def _join_original_text_lines(shell_source_lines_or_none):
    """Join original unparsed shell source, handling None values."""
    if any(text is None for text in shell_source_lines_or_none):
        return None
    else:
        return "\n".join(shell_source_lines_or_none)
