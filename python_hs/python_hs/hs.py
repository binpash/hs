from __future__ import annotations

import atexit
import builtins
import dataclasses
import functools
import os
import re
import subprocess
import tempfile
import threading
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from typing import Any, Literal, ParamSpec, TypeAlias, TypeVar

    ShellType: TypeAlias = Literal["hs", "bash", "subprocess"]
    P = ParamSpec("P")
    R = TypeVar("R")

    # could be more complex
    ExpectedSpeculated: TypeAlias = Literal["yes", "no", "any"]

FUNCTIONS_TO_PATCH: set[str] = {"open", "print"}


@dataclasses.dataclass(slots=True, kw_only=True)
class Params:
    shell_type: ShellType | None
    debug: bool
    min_commit_time: float  # seconds -- 0 = never

    def shell(self) -> Path | str:
        if self.shell_type == "hs":
            if self.debug:
                return python_hs_top / "hs_debug_entrypoint.sh"
            else:
                return python_hs_top / "hs_entrypoint.sh"
        elif self.shell_type == "bash":
            return "bash"
        elif self.shell_type == "subprocess":
            raise ValueError(
                "shell() should not be called when shell_type='subprocess'"
            )
        elif self.shell_type is None:
            raise ValueError("Please set shell_type")
        else:
            assert False, "should never happen"


PARAMS = Params(shell_type="hs", debug=True, min_commit_time=0.1)


@dataclasses.dataclass(slots=True)
class CommandBuffer:
    command_buffer: list[str | Sequence[str]] = dataclasses.field(default_factory=list)
    excluded_inds: set[int] = dataclasses.field(default_factory=set)
    expected_speculation: list[ExpectedSpeculated] = dataclasses.field(
        default_factory=list
    )

    def merge(self) -> tuple[str, list[ExpectedSpeculated]]:
        commands = (
            v if isinstance(v, str) else " ".join(v) for v in self.command_buffer
        )
        script = "\n".join(f"( {c} )" for c in commands)
        self.command_buffer.clear()
        old_expected_spec = self.expected_speculation
        self.expected_speculation = []
        return script, old_expected_spec

    def append(
        self,
        v: str | Sequence[str],
        *,
        expected_speculated: ExpectedSpeculated | bool,
    ) -> None:
        if isinstance(expected_speculated, bool):
            expected_speculated = "yes" if expected_speculated else "no"

        self.command_buffer.append(v)
        self.expected_speculation.append(expected_speculated)


command_buffer = CommandBuffer()

commit_log: list[CommitResults] = []

python_hs_top = Path(__file__).parent
_commit_timer: threading.Timer | None = None

python_hs_tmp_dir = tempfile.mkdtemp(prefix="python_hs")

if PARAMS.debug:
    hs_logfile = tempfile.NamedTemporaryFile(  # noqa: SIM115
        delete=False, mode="r", dir=python_hs_tmp_dir, prefix="logfile"
    )

    os.environ["PYTHON_HS_LOGFILE"] = hs_logfile.name


@dataclasses.dataclass(frozen=True, slots=True)
class CommitResults:
    shell_type: ShellType
    expect_speculated: Sequence[ExpectedSpeculated]
    actual_speculated: Sequence[bool]

    def same_speculated(self) -> bool:
        for actual, expected in zip(
            self.actual_speculated, self.expect_speculated, strict=True
        ):
            if expected != "any" and actual != (expected == "yes"):
                return False

        return True


good_log_regex = re.compile(r"\[GOOD_LOG\] (?P<spec_id>\d+)@? speculation committed")
debug_log_regex = re.compile(r"\[DEBUG_LOG\] Node \d+@? executing")


def parse_good_log_output(output: Sequence[str]) -> list[bool]:
    """Parse hS log output to determine which commands were speculated."""
    actual_speculated: list[bool] = []
    for line in output:
        if re.search(debug_log_regex, line):
            actual_speculated.append(False)
        elif spec_match := re.search(good_log_regex, line):
            spec_id = int(spec_match.group("spec_id"))
            actual_speculated[spec_id] = True

    return actual_speculated


def run(argv: str | Sequence[str], *, _speculated: bool = True, **kwargs: Any) -> None:
    global _commit_timer

    command_buffer.append(
        argv, expected_speculated=PARAMS.shell_type == "hs" and _speculated
    )

    if PARAMS.shell_type == "subprocess":
        filtered_kwargs = {k: v for k, v in kwargs.items() if not k.startswith("_")}
        filtered_kwargs.setdefault("shell", True)
        filtered_kwargs.setdefault("text", True)
        subprocess.run(argv, **filtered_kwargs)

    if PARAMS.min_commit_time:
        if _commit_timer is not None:
            _commit_timer.cancel()
        _commit_timer = threading.Timer(PARAMS.min_commit_time, commit)
        _commit_timer.start()


@atexit.register
def commit() -> None:
    if _commit_timer is not None:
        if _commit_timer.is_alive():
            return
        _commit_timer.cancel()

    command_string, expect_speculated = command_buffer.merge()

    if command_string:
        if PARAMS.shell_type != "subprocess":
            subprocess.run(
                command_string,
                shell=True,
                executable=PARAMS.shell(),
                text=True,
                check=PARAMS.debug,
            )

        if PARAMS.debug:
            hs_log = hs_logfile.readlines()
            hs_logfile.seek(0)
            actual_speculated = (
                parse_good_log_output(hs_log)
                if PARAMS.shell_type == "hs"
                else [False] * len(expect_speculated)
            )
            actual_speculated = [
                v
                for i, v in enumerate(actual_speculated)
                if i not in command_buffer.excluded_inds
            ]

            assert PARAMS.shell_type is not None
            commit_result: CommitResults = CommitResults(
                PARAMS.shell_type,
                expect_speculated,
                actual_speculated,
            )
            commit_log.append(commit_result)


def unsafe(func: Callable[P, R]) -> Callable[P, R]:
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        commit()
        return func(*args, **kwargs)

    return wrapper


def monkeypatch_unsafe() -> None:
    for f in FUNCTIONS_TO_PATCH:
        setattr(builtins, f, unsafe(getattr(builtins, f)))
