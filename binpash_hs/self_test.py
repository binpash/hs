from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile

from binpash_hs._runtime import runtime_env, runtime_root


def main() -> int:
    runtime = runtime_root()
    with tempfile.TemporaryDirectory(prefix="binpash-hs-test-") as tmpdir:
        work_runtime = os.path.join(tmpdir, "runtime")
        shutil.copytree(runtime, work_runtime)

        env = runtime_env()
        env["ORCH_TOP"] = work_runtime
        env["PASH_SPEC_TOP"] = work_runtime
        env["PASH_TOP"] = work_runtime
        env["DEBUG"] = "0"
        env["PATH"] = os.pathsep.join(
            [os.path.join(work_runtime, "deps", "try", "utils"), env.get("PATH", "")]
        )

        test_script = os.path.join(work_runtime, "test", "test_orch.sh")
        completed = subprocess.run(["bash", test_script], cwd=work_runtime, env=env)
        return completed.returncode


if __name__ == "__main__":
    sys.exit(main())
