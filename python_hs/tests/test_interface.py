#!/usr/bin/env python

from __future__ import annotations

import logging
import subprocess
import time
import unittest
from pathlib import Path
from typing import TYPE_CHECKING, assert_never

from python_hs.constants import PASH_SPEC_TOP, PYTHON_SPEC_TOP

if TYPE_CHECKING:
    from typing import Literal, TypeAlias

    ShellType: TypeAlias = Literal["subprocess", "hs"]

INTERFACE_TESTS = (PYTHON_SPEC_TOP / "tests" / "interface_tests").rglob("*.py")

MIN_HS_TIME = 0.1

logger = logging.getLogger(__name__)

class TestInterface(unittest.TestCase):
    def run_script_with_shell(
        self, test_script_path: Path, shell_type: ShellType
    ) -> tuple[str, float]:
        """Run the test script with specified shell and return output and execution time."""
        # NOTE: We only test the subprocess.run no-capture path

        match shell_type:
            case "hs":
                args = [
                    PASH_SPEC_TOP / "pash-spec.sh",
                    "--python",
                    test_script_path,
                ]
            case "subprocess":
                args = ["python3", test_script_path]
            case _:
                assert_never(shell_type)

        start_time = time.time()

        res = subprocess.run(args, check=True, text=True, capture_output=True)

        end_time = time.time()

        execution_time = end_time - start_time
        stdout = res.stdout

        if res.stderr:
            logger.warning("Stderr of test is not empty:\n%s", res.stderr)

        print(f"{shell_type} execution time: {execution_time:.4f} seconds")

        return stdout, execution_time

    def test_performance_comparison(self) -> None:
        """Test that HS shell runs faster than bash with identical output for all test files."""
        for test_file in INTERFACE_TESTS:
            with self.subTest(test_file=test_file.name):
                print(f"Running performance comparison for {test_file.name}")

                sub_stdout, sub_time = self.run_script_with_shell(
                    test_file, "subprocess"
                )

                hs_stdout, hs_time = self.run_script_with_shell(test_file, "hs")
                self.assertEqual(
                    sub_stdout,
                    hs_stdout,
                    f"Output differs between subprocess and hS shell for {test_file.name}",
                )

                self.assertGreater(
                    hs_time,
                    MIN_HS_TIME,
                    f"HS ran in {hs_time:.4f}s < {MIN_HS_TIME}s, which is suspiscously short",
                )

                print(f"PASS: hS is {sub_time / hs_time:.3f}x the speed of bash")


if __name__ == "__main__":
    unittest.main()
