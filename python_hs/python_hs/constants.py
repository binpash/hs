import os
from pathlib import Path


def _get_path(env_var: str) -> Path | None:
    try:
        return Path(os.environ[env_var])
    except KeyError:
        return None


PASH_SPEC_TOP = Path(__file__).parent.parent.parent
assert PASH_SPEC_TOP.name == "hs"

PASH_TOP = PASH_SPEC_TOP / "deps" / "pash"
PYTHON_SPEC_TOP = PASH_SPEC_TOP / "python_hs"

RUNTIME_DIR = PASH_TOP / "compiler" / "orchestrator_runtime"

# TODO: Fix wrt tmp dir

PASH_SPEC_SCHEDULER_SOCKET = _get_path("PASH_SPEC_SCHEDULER_SOCKET")
PASH_SPEC_TMP_PREFIX = _get_path("PASH_SPEC_TMP_PREFIX")
