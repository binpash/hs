from __future__ import annotations

import os
import sys
from importlib.resources import files
from pathlib import Path


def runtime_root() -> Path:
    root = files("binpash_hs").joinpath("runtime")
    return Path(os.fspath(root))


def runtime_env() -> dict[str, str]:
    runtime = runtime_root()
    env = os.environ.copy()
    env["PASH_SPEC_TOP"] = str(runtime)
    env["PASH_TOP"] = str(runtime)
    env["ORCH_TOP"] = str(runtime)
    env["PASH_PYTHON"] = sys.executable
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    try_utils = runtime / "deps" / "try" / "utils"
    env["PATH"] = f"{try_utils}{os.pathsep}{env.get('PATH', '')}"
    return env
