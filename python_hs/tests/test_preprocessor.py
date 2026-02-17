#!/usr/bin/env python
from __future__ import annotations

import unittest

from python_hs.preprocessor import (
    PreprocessState,
    preprocess,
)


class TestPreprocessState(unittest.TestCase):
    def test_add_command(self) -> None:
        state = PreprocessState()

        # The add method requires stdout parameter
        cmd_id = state.add(["echo", "test"], stdout="output", stdin=None)
        self.assertEqual(cmd_id, 0)
        self.assertEqual(len(state.specs), 1)
        self.assertEqual(state.specs[0].args, ["echo", "test"])
        self.assertEqual(state.specs[0].stdout, "output")
        self.assertIsNone(state.specs[0].stdin)

    def test_add_command_with_pipe(self) -> None:
        state = PreprocessState()

        # First command outputs to pipe
        cmd_id1 = state.add(["echo", "test"], stdout="pipe", stdin=None)
        # Second command takes input from first
        cmd_id2 = state.add(["grep", "test"], stdout="output", stdin=cmd_id1)

        self.assertEqual(cmd_id1, 0)
        self.assertEqual(cmd_id2, 0)
        self.assertEqual(state.specs[0].args, ["grep", "test"])
        self.assertEqual(state.specs[0].stdin.args, ["echo", "test"])  # type: ignore

    def test_add_multiple_commands(self) -> None:
        state = PreprocessState()

        cmd_id1 = state.add(["echo", "hello"], stdout="output", stdin=None)
        cmd_id2 = state.add(["echo", "world"], stdout="output", stdin=None)

        self.assertEqual(cmd_id1, 0)
        self.assertEqual(cmd_id2, 1)
        self.assertEqual(len(state.specs), 2)


class TestPreprocessor(unittest.TestCase):
    def test_subprocess_replacement(self) -> None:
        code = """
import subprocess
subprocess.run(['echo', 'hello'])
subprocess.run(['echo', 'world'])
"""
        result, _ = preprocess(code)

        self.assertIn("hs_run(0, None, 'output', False, False)", result)
        self.assertIn("hs_run(1, None, 'output', False, False)", result)
        self.assertNotIn("subprocess.run", result)

    def test_subprocess_with_capture_output(self) -> None:
        code = """
import subprocess
result = subprocess.run(['echo', 'hello'], capture_output=True)
"""
        result, _ = preprocess(code)

        self.assertIn("hs_run(0, None, 'capture', False, False)", result)
        self.assertNotIn("subprocess.run", result)

    def test_popen_transformation(self) -> None:
        code = """
import subprocess
p1 = subprocess.Popen(['echo', 'hello'], stdout=subprocess.PIPE)
p2 = subprocess.run(['grep', 'h'], stdin=p1.stdout)
"""
        result, _ = preprocess(code)

        # Should transform Popen calls to hs_run
        self.assertIn("hs_run(", result)
        self.assertNotIn("subprocess.Popen", result)
        # The second command should use stdin from first

    def test_loop_transformation(self) -> None:
        code = """
for i in range(3):
    subprocess.run(['echo', str(i)])
"""
        result, _ = preprocess(code)

        self.assertIn("hs_run(0, 0", result)
        self.assertIn("hs_run(1, 1", result)
        self.assertIn("hs_run(2, 2", result)
        # Original loop should be gone
        self.assertNotIn("for i in range(3):", result)

    def test_nested_loops(self) -> None:
        code = """
for i in range(2):
    for j in range(2):
        subprocess.run(['echo', f'{i},{j}'])
"""
        result, _ = preprocess(code)

        # Should unroll both nested loops completely
        call_count = result.count("hs_run(")
        self.assertEqual(call_count, 4)  # 2x2 = 4 calls from unrolled nested loops
        self.assertNotIn("for i in range(2):", result)
        self.assertNotIn("for j in range(2):", result)

    def test_unsupported_subprocess_args(self) -> None:
        code = """
subprocess.run(['echo', 'hello'], env={'FOO': 'bar'})
"""
        with self.assertRaises(ValueError) as cm:
            preprocess(code)

        self.assertIn("Extra kws", str(cm.exception))
        self.assertIn("env", str(cm.exception))

    def test_missing_subprocess_args(self) -> None:
        code = """
subprocess.run()
"""
        with self.assertRaises(ValueError) as cm:
            preprocess(code)

        self.assertIn(
            "subprocess.run requires at least one argument", str(cm.exception)
        )

    def test_popen_without_stdout_pipe(self) -> None:
        code = """
import subprocess
p = subprocess.Popen(['echo', 'hello'])
"""
        with self.assertRaises(ValueError) as cm:
            preprocess(code)

        self.assertIn("Popen without stdout", str(cm.exception))

    def test_unnamed_popen(self) -> None:
        code = """
import subprocess
subprocess.Popen(['echo', 'hello'], stdout=subprocess.PIPE)
"""
        with self.assertRaises(ValueError) as cm:
            preprocess(code)

        self.assertIn("Unnamed Popen", str(cm.exception))

    def test_loop_unrolling_basic(self) -> None:
        code = """
import subprocess
for i in range(2):
    subprocess.run(['echo', str(i)])
"""
        result, _ = preprocess(code)

        # Should contain unrolled hs_run calls instead of original loop
        self.assertIn("hs_run(0, 0", result)
        self.assertIn("hs_run(1, 1", result)
        self.assertNotIn("for i in range(2):", result)
        self.assertNotIn("subprocess.run", result)

    def test_loop_unrolling_with_range_args(self) -> None:
        code = """
import subprocess
for i in range(1, 3):
    subprocess.run(['echo', str(i)])
"""
        result, _ = preprocess(code)

        # Should unroll range(1, 3) which generates i=1, i=2
        self.assertIn("hs_run(0, 0", result)
        self.assertIn("hs_run(1, 1", result)
        self.assertNotIn("for i in range(1, 3):", result)

    def test_loop_unrolling_with_constant(self) -> None:
        code = """
import subprocess
items = [1, 2, 3]
for i in items:
    subprocess.run(['echo', str(i)])
"""
        result, _ = preprocess(code)

        self.assertIn("hs_run(0, 0", result)
        self.assertIn("hs_run(1, 1", result)
        self.assertIn("hs_run(2, 2", result)
        self.assertNotIn("for i in items:", result)

    def test_nested_loops_unrolling(self) -> None:
        code = """
import subprocess
for i in range(2):
    for j in range(2):
        subprocess.run(['echo', f'{i},{j}'])
"""
        result, _ = preprocess(code)

        # Should unroll both loops, creating 4 hs_run calls
        self.assertIn("hs_run(0, 0", result)
        self.assertIn("hs_run(1, 1", result)
        self.assertIn("hs_run(2, 2", result)
        self.assertIn("hs_run(3, 3", result)
        self.assertNotIn("for i in range(2):", result)
        self.assertNotIn("for j in range(2):", result)

    def test_subprocess_with_check(self) -> None:
        """check=True should be passed through to hs_run."""
        code = """
import subprocess
subprocess.run(['echo', 'hello'], check=True)
"""
        result, _ = preprocess(code)
        self.assertIn("hs_run(0, None, 'output', True, False)", result)

    def test_subprocess_with_text(self) -> None:
        """text=True should be passed through to hs_run."""
        code = """
import subprocess
subprocess.run(['echo', 'hello'], text=True)
"""
        result, _ = preprocess(code)
        self.assertIn("hs_run(0, None, 'output', False, True)", result)

    def test_shell_true_uses_shlex(self) -> None:
        """shell=True should be accepted (not raise) and command should be split."""
        code = """
import subprocess
subprocess.run('echo hello', shell=True)
"""
        result, state = preprocess(code)
        self.assertIn("hs_run(", result)
        # shell=True with string arg should shlex.split the command
        self.assertEqual(state.specs[0].args, ["echo", "hello"])


if __name__ == "__main__":
    unittest.main()
