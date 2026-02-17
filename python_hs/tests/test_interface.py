#!/usr/bin/env python

from __future__ import annotations

import ast
import unittest

from python_hs.constants import PYTHON_SPEC_TOP
from python_hs.preprocessor import preprocess

INTERFACE_TESTS = list((PYTHON_SPEC_TOP / "tests" / "interface_tests").rglob("*.py"))


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


if __name__ == "__main__":
    unittest.main()
