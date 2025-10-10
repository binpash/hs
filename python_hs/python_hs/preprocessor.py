#!/usr/bin/env python3

from __future__ import annotations

import ast
import builtins
import copy
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, assert_never

from python_hs.logging_ import setup_logger
from python_hs.runtime import get_vars

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from typing import Any, Literal

logger = setup_logger(__name__)

SAFE_STDLIB = {"range", "len", "str", "int", "hex", "min", "max", "abs", "ord", "chr"}


def eval_expr(node: ast.expr, *args: Any) -> Any:
    # note: using eval for subprocess argument evaluation - unsafe but fine for prototype
    # we should use simple_eval for this
    return eval(compile(ast.Expression(node), "", "eval"), *args)


@dataclass
class PreprocessedCommand:
    args: list[str]
    stdout: Literal["capture", "output", "pipe"]
    stdin: PreprocessedCommand | None

    def _get_all_commands(self) -> Iterator[PreprocessedCommand]:
        # reverse iterate over linked list
        if self.stdin is not None:
            yield from self.stdin._get_all_commands()

        yield self

    def _get_args_str(self) -> str:
        return f"{' '.join(shlex.quote(a) for a in self.args)}"

    def create_command(self) -> tuple[str, Path | None]:
        """Write command to file and return shell command with stdout temp file path."""

        stdout_path: Path | None = None
        pipes = self._get_all_commands()
        command = " | ".join(cmd._get_args_str() for cmd in pipes)

        match self.stdout:
            case "capture" | "output":
                pass
            case "pipe":
                assert False, "pipe should not be ending a command"
            case _:
                assert_never(self.stdout)

        return command, stdout_path


@dataclass
class PreprocessState:
    specs: list[PreprocessedCommand]

    def __init__(self) -> None:
        self.specs = []

    def create_partial_order_directory(self, hs_runtime: Path) -> None:
        """Save all commands in specs to hs_runtime/partial_order."""
        partial_order_path = hs_runtime / "partial_order"
        partial_order_path.mkdir(exist_ok=True)

        for i, spec in enumerate(self.specs):
            # TODO: Use.
            command, _stdout_path = spec.create_command()
            command_file = partial_order_path / str(i)
            command_file.write_text(command + "\n")

    def create_partial_order_file(self, hs_runtime: Path) -> None:
        """Save all commands in specs to hs_runtime/partial_order_file."""

        # /tmp/pash_Ye4T3Qw//speculative/partial_order/
        # /tmp/pash_Ye4T3Qw/tmpvk6xpy6g
        # 3
        # Basic blocks:
        # Basic block edges:
        # Loop context:
        # 0-loop_ctx-0
        # 1-loop_ctx-0
        # 2-loop_ctx-0
        # 0
        # 0 -> 1
        # 1 -> 2
        partial_order_path = hs_runtime / "partial_order"

        partial_order_contents = [
            partial_order_path,
            get_vars(),
            len(self.specs),
            "Basic blocks:",
            "Basic block edges:",
            "Loop context:",
            *[f"{i}-loop_ctx-0" for i in range(len(self.specs))],
            "0",
            *[f"{i - 1} -> {i}" for i in range(1, len(self.specs))],
        ]
        partial_order_text = "\n".join(map(str, partial_order_contents))
        (hs_runtime / "partial_order_file").write_text(partial_order_text)

    def add(
        self,
        args: list[str],
        stdout: Literal["capture", "output", "pipe"],
        stdin: int | None,
    ) -> int:
        """Add a command to specs and return its index."""
        cmd = PreprocessedCommand(
            args, stdout, self.specs[stdin] if stdin is not None else None
        )

        if stdin is not None:
            self.specs[stdin] = cmd
            return stdin

        self.specs.append(cmd)
        return len(self.specs) - 1


def _get_stdin_ind(node: ast.expr, preprocessed_command_vars: dict[str, int]) -> int:
    if (
        not isinstance(node, ast.Attribute)
        or not isinstance(node.value, ast.Name)
        or node.attr != "stdout"
        or node.value.id not in preprocessed_command_vars
    ):
        raise ValueError("Bad node", node)

    return preprocessed_command_vars[node.value.id]


class PreprocessorTransformer(ast.NodeTransformer):
    def __init__(self) -> None:
        self.state: PreprocessState = PreprocessState()
        self.loop_id: int | None = None
        self.preprocessed_command_vars: dict[str, int] = {}
        self.name: str | None = None
        self.eval_context: dict[str, Any] = {"os": os}
        for func in SAFE_STDLIB:
            self.eval_context[func] = getattr(builtins, func)
        # lineno to transformer function (takes the loop id)
        self.transform_cache: dict[int, Callable[[], ast.expr]] = {}

    @staticmethod
    def _is_subprocess_val(node: ast.expr, *names: str) -> bool:
        assert names
        # TODO Fix.
        return (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "subprocess"
            and (node.attr in names)
        )

    @staticmethod
    def _has_break_continue(body: list[ast.stmt]) -> bool:
        """Check if the loop body contains break or continue statements."""
        for stmt in body:
            if isinstance(stmt, ast.Break | ast.Continue):
                return True
            if isinstance(
                stmt,
                ast.For
                | ast.While
                | ast.If
                | ast.With
                | ast.Try
                | ast.FunctionDef
                | ast.ClassDef
                | ast.AsyncFor
                | ast.AsyncWith
                | ast.AsyncFunctionDef,
            ) and PreprocessorTransformer._has_break_continue(stmt.body):
                return True
            if isinstance(
                stmt, ast.For | ast.While | ast.If | ast.Try
            ) and PreprocessorTransformer._has_break_continue(stmt.orelse):
                return True
        return False

    def _can_safely_attempt_unroll(self, node: ast.For) -> bool:
        """Check if a for loop can be unrolled."""
        return not self._has_break_continue(node.body) and isinstance(
            node.target, ast.Name
        )

    def _unroll_loop(self, node: ast.For) -> list[ast.stmt]:
        """Unroll a for loop into individual statements."""

        assert isinstance(node.target, ast.Name)
        loop_var = node.target.id

        try:
            iterator_values = eval_expr(node.iter, self.eval_context)
        except Exception as e:
            raise ValueError(f"Cannot evaluate loop iterator: {e}") from e

        unrolled_statements = []

        if self.loop_id is None:
            self.loop_id = 0
            top_loop = True
        else:
            top_loop = False

        for value in iterator_values:
            self.eval_context[loop_var] = value
            # Won't work for "complex" iterators probably
            unrolled_statements.append(
                ast.Assign([node.target], ast.Constant(value), lineno=-1)
            )

            for stmt in node.body:
                stmt_copy = copy.deepcopy(stmt)
                transformed_stmt = self.visit(stmt_copy)
                unrolled_statements.append(transformed_stmt)

        if top_loop:
            self.loop_id = None
        return unrolled_statements

    def visit_Assign(self, node: ast.Assign) -> ast.AST:
        if len(node.targets) != 1 or not isinstance(
            target := node.targets[0], ast.Name
        ):
            return self.generic_visit(node)

        name = target.id
        if isinstance(target.ctx, ast.Store):
            try:
                self.eval_context[name] = eval_expr(node.value, self.eval_context)
            except Exception:
                pass
            else:
                return self.generic_visit(node)

        old_name = self.name
        if isinstance(node.value, ast.Call) and self._is_subprocess_val(
            node.value.func, "Popen"
        ):
            self.name = name

        visited = self.generic_visit(node)
        self.name = old_name

        return visited

    def visit_Call(self, node: ast.Call) -> ast.AST:
        if self._is_subprocess_val(node.func, "run", "Popen"):
            return self._transform_subprocess_call(node)

        return self.generic_visit(node)

    def visit_For(self, node: ast.For) -> ast.AST | list[ast.stmt]:
        if self._can_safely_attempt_unroll(node):
            return self._unroll_loop(node)
        return node

    def _transform_subprocess_call(self, node: ast.Call) -> ast.expr:
        """Transform subprocess.run/Popen call to hs_run call."""

        if cached_transform := self.transform_cache.get(node.lineno):
            return cached_transform()

        if not node.args:
            raise ValueError("subprocess.run requires at least one argument")

        cmd_ast = node.args[0]

        kw_args = {kw.arg: kw.value for kw in node.keywords}

        try:
            stdin = kw_args.pop("stdin")
        except KeyError:
            source = None
        else:
            source = _get_stdin_ind(stdin, self.preprocessed_command_vars)

        if self._is_subprocess_val(node.func, "Popen"):
            try:
                pipe_node = kw_args.pop("stdout")
            except KeyError as e:
                raise ValueError("Popen without stdout to subprocess.PIPE") from e

            if not self._is_subprocess_val(pipe_node, "PIPE"):
                raise ValueError("Popen without PIPE for stdout, instead kw.value")

            if self.name is None:
                raise ValueError("Unnamed Popen")

            dest = "pipe"
            return_none = True
        elif self._is_subprocess_val(node.func, "run"):
            try:
                val = kw_args.pop("capture_output")
            except KeyError:
                capture_output = False
            else:
                capture_output = ast.literal_eval(val)

            dest = "capture" if capture_output else "output"
            return_none = False
        else:
            raise NotImplementedError(node)

        if kw_args:
            raise ValueError(f"Extra kws {kw_args}")

        def transformer() -> ast.expr:
            evaluated_cmd = eval_expr(
                cmd_ast, self.eval_context | {"subprocess": subprocess}
            )
            if isinstance(evaluated_cmd, str | Path):
                args = [str(evaluated_cmd)]
            else:
                args = [str(arg) for arg in evaluated_cmd]

            cmd_id = self.state.add(args, dest, source)
            if self.name is not None:
                self.preprocessed_command_vars[self.name] = cmd_id

            if return_none:
                return ast.Constant(value=None)

            ret = ast.Call(
                func=ast.Name(id="hs_run", ctx=ast.Load()),
                args=[
                    ast.Constant(value=cmd_id),
                    ast.Constant(value=self.loop_id),
                    ast.Constant(value=dest),
                ],
                keywords=[],
            )
            if self.loop_id is not None:
                self.loop_id += 1
            return ret

        self.transform_cache[node.lineno] = transformer
        return transformer()


def not_none_statement(v: ast.stmt) -> bool:
    return not (
        isinstance(v, ast.Expr)
        and isinstance(v.value, ast.Constant)
        and v.value.value is None
    )


def preprocess(code: str) -> tuple[str, PreprocessState]:
    """Preprocess Python code to extract constants and transform subprocess.run calls."""
    tree = ast.parse(code)
    transformer = PreprocessorTransformer()

    logger.info("Original Code:\n" + code)

    new_tree = transformer.visit(tree)

    if not isinstance(new_tree, ast.Module):
        new_tree = ast.Module(
            body=new_tree if isinstance(new_tree, list) else [new_tree], type_ignores=[]
        )

    new_statements: list[ast.stmt] = [
        ast.ImportFrom("python_hs", [ast.alias("hs_run")], 0)
    ]

    new_statements.extend(filter(not_none_statement, new_tree.body))

    result_tree = ast.Module(body=new_statements, type_ignores=[])

    result = ast.unparse(result_tree) + "\n"
    logger.info("Preprocessed Code:\n" + result)
    return result, transformer.state


def preprocess_file(spec_runtime: Path | str, path: Path) -> Path:
    """Preprocess a Python file and return path to preprocessed temporary file."""
    logger.info(f"Preprocessing file: {path}")

    spec_runtime = Path(spec_runtime)

    source_code = path.read_text()

    preprocessed_code, state = preprocess(source_code)

    with tempfile.NamedTemporaryFile(
        dir=spec_runtime,
        prefix=f"python_hs_preprocessed_{path.stem}_",
        suffix=".py",
        delete=False,
        mode="w",
    ) as temp_file:
        temp_file.write(preprocessed_code)

    if shutil.which("ruff"):
        subprocess.run(
            ["ruff", "format", temp_file.name], check=True, capture_output=True
        )

    logger.info(f"Preprocessed file: {temp_file.name}")
    state.create_partial_order_directory(spec_runtime)
    state.create_partial_order_file(spec_runtime)

    return Path(temp_file.name)


if __name__ == "__main__":
    with open(sys.argv[1]) as f:
        print(preprocess(f.read())[0])
