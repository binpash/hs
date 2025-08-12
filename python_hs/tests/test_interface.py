#!/usr/bin/env python

from __future__ import annotations

import contextlib
import os
import runpy
import time
import unittest
from io import StringIO
from pathlib import Path

from python_hs import hs

pash_spec_top = Path(__file__).parent.parent.parent

MIN_HS_TIME: float = 0.1  # seconds


class TestInterface(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
        cls.interface_tests_dir = Path(__file__).parent / "interface_tests"
        cls.test_files = list(cls.interface_tests_dir.glob("*.py"))
        hs.PARAMS.debug = True
        hs.PARAMS.min_commit_time = 0
        hs.PARAMS.shell_type = None

    def run_script_with_shell(
        self, test_script_path: Path, shell_type: hs.ShellType
    ) -> tuple[str, str, hs.CommitResults, float]:
        """Run the test script with specified shell and return output and execution time."""
        hs.PARAMS.shell_type = shell_type

        captured_stdout = StringIO()
        captured_stderr = StringIO()

        before_commit_log_len = len(hs.commit_log)

        with (
            contextlib.redirect_stdout(captured_stdout),
            contextlib.redirect_stderr(captured_stderr),
        ):
            start_time = time.time()
            runpy.run_path(str(test_script_path), run_name="__main__")
            hs.commit()

        end_time = time.time()

        execution_time = end_time - start_time
        stdout = captured_stdout.getvalue()
        stderr = captured_stderr.getvalue()

        self.assertTrue(
            len(hs.commit_log) == before_commit_log_len + 1,
            f"{len(hs.commit_log)} != ({before_commit_log_len} + 1): One commit should have occured",
        )
        last_commit = hs.commit_log[-1]

        self.assertEqual(
            last_commit.shell_type,
            shell_type,
            f"Shell type in commit log should match {shell_type}",
        )

        self.assertFalse(stderr, f"{shell_type} error:\n\n{stderr}")
        print(f"{shell_type} execution time: {execution_time:.4f} seconds")

        hs.PARAMS.shell_type = None

        return stdout, stderr, last_commit, execution_time

    def test_performance_comparison(self) -> None:
        """Test that HS shell runs faster than bash with identical output for all test files."""
        for test_file in self.test_files:
            with self.subTest(test_file=test_file.name):
                print(f"Running performance comparison for {test_file.name}")

                sub_stdout, sub_stderr, last_sub_commit, sub_time = (
                    self.run_script_with_shell(test_file, "subprocess")
                )

                bash_stdout, bash_stderr, last_bash_commit, bash_time = (
                    self.run_script_with_shell(test_file, "bash")
                )

                self.assertEqual(
                    sub_stdout,
                    bash_stdout,
                    f"Output differs between subprocess and bash shell for {test_file.name}",
                )

                hs_stdout, hs_stderr, last_hs_commit, hs_time = (
                    self.run_script_with_shell(test_file, "hs")
                )

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

                self.assertTrue(
                    last_hs_commit.same_speculated(),
                    f"Speculation mismatch for {test_file.name}: "
                    f"expected={last_hs_commit.expect_speculated}, "
                    f"actual={last_hs_commit.actual_speculated}. ",
                )

                print(f"PASS: hS is {bash_time / hs_time:.2f}x the speed of bash")


if __name__ == "__main__":
    unittest.main()
