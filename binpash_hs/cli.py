from __future__ import annotations

import os
import shlex
import shutil
import sys

from binpash_hs._runtime import runtime_env, runtime_root


def _is_help_request(argv: list[str]) -> bool:
    return any(arg in {"-h", "--help"} for arg in argv)


def _require_root_for_execution(argv: list[str]) -> None:
    if os.geteuid() == 0 or _is_help_request(argv):
        return

    executable = shutil.which("hs") or sys.argv[0]
    command = " ".join([shlex.quote(executable), *map(shlex.quote, argv)])
    print(
        "hs requires root privileges for sandboxed execution.\n"
        f"Run this command as: sudo {command}\n"
        "If `sudo hs` is not found, use `sudo $(command -v hs) ...` "
        "or install a root-visible wrapper in /usr/local/bin.",
        file=sys.stderr,
    )
    raise SystemExit(2)


def main() -> None:
    _require_root_for_execution(sys.argv[1:])
    hs_script = runtime_root() / "hs"
    argv = ["bash", str(hs_script), *sys.argv[1:]]
    os.execvpe("bash", argv, runtime_env())
