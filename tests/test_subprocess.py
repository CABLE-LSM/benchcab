"""`pytest` tests for `utils/subprocess.py`."""

import os
import subprocess
from pathlib import Path

import pytest

from benchcab.utils.subprocess import SubprocessWrapper


class TestRunCmd:
    """Tests for `run_cmd()`."""

    @pytest.fixture()
    def subprocess_handler(self):
        """Return an instance of `SubprocessWrapper` for testing."""
        return SubprocessWrapper()

    def test_stdout_is_suppressed_in_non_verbose_mode(self, subprocess_handler, capfd):
        """Success case: test stdout is suppressed in non-verbose mode."""
        subprocess_handler.run_cmd("echo foo")
        captured = capfd.readouterr()
        assert not captured.out
        assert not captured.err

    def test_stderr_is_suppressed_in_non_verbose_mode(self, subprocess_handler, capfd):
        """Success case: test stderr is suppressed in non-verbose mode."""
        subprocess_handler.run_cmd("echo foo 1>&2")
        captured = capfd.readouterr()
        assert not captured.out
        assert not captured.err

    def test_command_and_stdout_is_printed_in_verbose_mode(
        self, subprocess_handler, capfd
    ):
        """Success case: test command and stdout is printed in verbose mode."""
        subprocess_handler.run_cmd("echo foo", verbose=True)
        captured = capfd.readouterr()
        assert captured.out == "echo foo\nfoo\n"
        assert not captured.err

    def test_command_and_stderr_is_redirected_to_stdout_in_verbose_mode(
        self, subprocess_handler, capfd
    ):
        """Success case: test command and stderr is redirected to stdout in verbose mode."""
        subprocess_handler.run_cmd("echo foo 1>&2", verbose=True)
        captured = capfd.readouterr()
        assert captured.out == "echo foo 1>&2\nfoo\n"
        assert not captured.err

    def test_output_is_captured_with_capture_output_enabled(
        self, subprocess_handler, capfd
    ):
        """Success case: test output is captured with capture_output enabled."""
        proc = subprocess_handler.run_cmd("echo foo", capture_output=True)
        captured = capfd.readouterr()
        assert not captured.out
        assert not captured.err
        assert proc.stdout == "foo\n"
        assert not proc.stderr

    def test_stderr_captured_to_stdout(self, subprocess_handler, capfd):
        """Success case: test stderr is captured to stdout with capture_output enabled."""
        proc = subprocess_handler.run_cmd("echo foo 1>&2", capture_output=True)
        captured = capfd.readouterr()
        assert not captured.out
        assert not captured.err
        assert proc.stdout == "foo\n"
        assert not proc.stderr

    def test_command_is_printed_and_stdout_is_captured_in_verbose_mode(
        self, subprocess_handler, capfd
    ):
        """Success case: test command is printed and stdout is captured in verbose mode."""
        proc = subprocess_handler.run_cmd("echo foo", capture_output=True, verbose=True)
        captured = capfd.readouterr()
        assert captured.out == "echo foo\n"
        assert not captured.err
        assert proc.stdout == "foo\n"
        assert not proc.stderr

    def test_stdout_is_redirected_to_file(self, subprocess_handler, capfd):
        """Success case: test stdout is redirected to file."""
        file_path = Path("out.txt")
        subprocess_handler.run_cmd("echo foo", output_file=file_path)
        with file_path.open("r", encoding="utf-8") as file:
            assert file.read() == "foo\n"
        captured = capfd.readouterr()
        assert not captured.out
        assert not captured.err

    def test_command_is_printed_and_stdout_is_redirected_to_file_in_verbose_mode(
        self, subprocess_handler, capfd
    ):
        """Success case: test command is printed and stdout is redirected to file in verbose mode."""
        file_path = Path("out.txt")
        subprocess_handler.run_cmd("echo foo", output_file=file_path, verbose=True)
        with file_path.open("r", encoding="utf-8") as file:
            assert file.read() == "foo\n"
        captured = capfd.readouterr()
        assert captured.out == "echo foo\n"
        assert not captured.err

    def test_command_is_run_with_environment(self, subprocess_handler):
        """Success case: test command is run with environment."""
        proc = subprocess_handler.run_cmd(
            "echo $FOO", capture_output=True, env={"FOO": "bar", **os.environ}
        )
        assert proc.stdout == "bar\n"

    def test_check_non_zero_return_code_throws_an_exception(self, subprocess_handler):
        """Failure case: check non-zero return code throws an exception."""
        with pytest.raises(subprocess.CalledProcessError):
            subprocess_handler.run_cmd("exit 1")

    def test_stderr_is_redirected_to_stdout_on_non_zero_return_code(
        self, subprocess_handler
    ):
        """Failure case: check stderr is redirected to stdout on non-zero return code."""
        with pytest.raises(subprocess.CalledProcessError) as exc:
            subprocess_handler.run_cmd("echo foo 1>&2; exit 1", capture_output=True)
        assert exc.value.stdout == "foo\n"
        assert not exc.value.stderr
