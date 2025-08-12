#!/usr/bin/env python
from __future__ import annotations

import time
import unittest
from unittest.mock import Mock, patch

import python_hs.hs as hs


class TestHS(unittest.TestCase):
    def setUp(self) -> None:
        hs.command_buffer = hs.CommandBuffer()

        hs.PARAMS.min_commit_time = 0
        hs.PARAMS.debug = True
        hs.PARAMS.shell_type = "hs"

    def test_run_multiple_commands(self) -> None:
        hs.run("echo 1")
        hs.run(["echo", "2"])
        self.assertEqual(hs.command_buffer.command_buffer, ["echo 1", ["echo", "2"]])

    @patch("python_hs.hs.commit")
    def test_min_commit_time_timer(self, mock_commit: Mock) -> None:
        hs.PARAMS.min_commit_time = 0.1
        hs.run("echo test")

        time.sleep(0.15)
        mock_commit.assert_called_once()

    def test_unsafe_decorator(self) -> None:
        call_count = 0

        @hs.unsafe
        def test_func() -> str:
            nonlocal call_count
            call_count += 1
            return "called"

        with patch.object(hs, "commit") as mock_commit:
            result = test_func()
            mock_commit.assert_called_once()
            self.assertEqual(result, "called")
            self.assertEqual(call_count, 1)

    def test_parse_good_log_output(self) -> None:
        """Test GOOD_LOG parsing functionality."""
        # Test with mock GOOD_LOG output
        mock_output = """
INFO|2025-08-15 08:24:39,921|[DEBUG_LOG] Node 0@ executing with pid 418562
INFO|2025-08-15 08:24:39,964|[DEBUG_LOG] Node 1@ executing with pid 418565
INFO|2025-08-15 08:24:39,983|[DEBUG_LOG] Node 2@ executing with pid 418568
INFO|2025-08-15 08:24:40,100|[GOOD_LOG] 0@ speculation committed
INFO|2025-08-15 08:24:40,200|[GOOD_LOG] 2@ speculation committed
        """.splitlines()

        result = hs.parse_good_log_output(mock_output)

        expected = [True, False, True]
        self.assertEqual(result, expected)

    def test_run_with_speculated_parameter(self) -> None:
        """Test run function with _speculated parameter."""
        hs.run("echo test1")
        self.assertEqual(hs.command_buffer.expected_speculation, ["yes"])

        hs.run("echo test2", _speculated=False)
        self.assertEqual(hs.command_buffer.expected_speculation, ["yes", "no"])

    @patch("python_hs.hs.subprocess.run")
    def test_subprocess_shell_type(self, mock_subprocess_run: Mock) -> None:
        """Test subprocess shell_type calls subprocess.run directly."""

        hs.PARAMS.shell_type = "subprocess"

        # Test with string command
        hs.run("echo test", _speculated=False)
        mock_subprocess_run.assert_called_with("echo test", shell=True, text=True)

        self.assertEqual(hs.command_buffer.expected_speculation, ["no"])


if __name__ == "__main__":
    unittest.main()
