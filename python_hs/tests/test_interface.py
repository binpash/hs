#!/usr/bin/env python

from __future__ import annotations

import ast
import os
import subprocess
import unittest

from python_hs.constants import PASH_SPEC_TOP, PYTHON_SPEC_TOP
from python_hs.preprocessor import preprocess

INTERFACE_TESTS = list((PYTHON_SPEC_TOP / "tests" / "interface_tests").rglob("*.py"))

HS_SCRIPT = PASH_SPEC_TOP / "hs"
FD_UTIL = PASH_SPEC_TOP / "executor" / "fd_util"

# Tests safe for end-to-end comparison (pipe_test.py outputs binary data)
E2E_TESTS = [
    PYTHON_SPEC_TOP / "tests" / "interface_tests" / "simple.py",
    PYTHON_SPEC_TOP / "tests" / "interface_tests" / "for_test.py",
]


class TestPreprocessIntegration(unittest.TestCase):
    """Verify that the interface_tests/ scripts preprocess into valid Python."""

    def test_preprocess_interface_scripts(self) -> None:
        self.assertGreater(len(INTERFACE_TESTS), 0, "No interface test scripts found")
        for test_file in INTERFACE_TESTS:
            with self.subTest(test_file=test_file.name):
                source = test_file.read_text()
                result, state = preprocess(source)
                # The preprocessed code should be valid Python
                ast.parse(result)
                # Should have replaced all subprocess calls
                self.assertNotIn("subprocess.run", result)
                self.assertNotIn("subprocess.Popen", result)
                # Should have at least one hs_run call
                self.assertIn("hs_run(", result)
                # State should have specs
                self.assertGreater(len(state.specs), 0)


@unittest.skipUnless(FD_UTIL.exists(), "fd_util not compiled (run make in executor/)")
class TestEndToEnd(unittest.TestCase):
    """Run interface tests through hs --python and compare to plain python3."""

    def test_hs_python_matches_python(self) -> None:
        for test_file in E2E_TESTS:
            with self.subTest(test_file=test_file.name):
                expected = subprocess.run(
                    ["python3", str(test_file)],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                actual = subprocess.run(
                    [str(HS_SCRIPT), "--python", str(test_file)],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=30,
                    env={**os.environ, "PASH_TMP_DIR": "/tmp"},
                )
                self.assertEqual(expected.stdout, actual.stdout)


if __name__ == "__main__":
    unittest.main()
