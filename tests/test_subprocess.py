"""`pytest` tests for `utils/subprocess.py`."""

import os
import subprocess

import pytest

pytest.skip(allow_module_level=True)

from benchcab.utils.subprocess import SubprocessWrapper

from .common import TMP_DIR


def test_run_cmd(capfd):
    """Tests for `run_cmd()`."""
    subprocess_handler = SubprocessWrapper()

    # Success case: test stdout is suppressed in non-verbose mode
    subprocess_handler.run_cmd("echo foo")
    captured = capfd.readouterr()
    assert not captured.out
    assert not captured.err

    # Success case: test stderr is suppressed in non-verbose mode
    subprocess_handler.run_cmd("echo foo 1>&2")
    captured = capfd.readouterr()
    assert not captured.out
    assert not captured.err

    # Success case: test command and stdout is printed in verbose mode
    subprocess_handler.run_cmd("echo foo", verbose=True)
    captured = capfd.readouterr()
    assert captured.out == "echo foo\nfoo\n"
    assert not captured.err

    # Success case: test command and stderr is redirected to stdout in verbose mode
    subprocess_handler.run_cmd("echo foo 1>&2", verbose=True)
    captured = capfd.readouterr()
    assert captured.out == "echo foo 1>&2\nfoo\n"
    assert not captured.err

    # Success case: test output is captured with capture_output enabled
    proc = subprocess_handler.run_cmd("echo foo", capture_output=True)
    captured = capfd.readouterr()
    assert not captured.out
    assert not captured.err
    assert proc.stdout == "foo\n"
    assert not proc.stderr

    # Success case: test stderr is captured and redirected to stdout with
    # capture_output enabled
    proc = subprocess_handler.run_cmd("echo foo 1>&2", capture_output=True)
    captured = capfd.readouterr()
    assert not captured.out
    assert not captured.err
    assert proc.stdout == "foo\n"
    assert not proc.stderr

    # Success case: test command is printed and stdout is captured in verbose mode
    proc = subprocess_handler.run_cmd("echo foo", capture_output=True, verbose=True)
    captured = capfd.readouterr()
    assert captured.out == "echo foo\n"
    assert not captured.err
    assert proc.stdout == "foo\n"
    assert not proc.stderr

    # Success case: test stdout is redirected to file
    file_path = TMP_DIR / "out.txt"
    subprocess_handler.run_cmd("echo foo", output_file=file_path)
    with file_path.open("r", encoding="utf-8") as file:
        assert file.read() == "foo\n"
    captured = capfd.readouterr()
    assert not captured.out
    assert not captured.err

    # Success case: test command is printed and stdout is redirected to file in verbose mode
    file_path = TMP_DIR / "out.txt"
    subprocess_handler.run_cmd("echo foo", output_file=file_path, verbose=True)
    with file_path.open("r", encoding="utf-8") as file:
        assert file.read() == "foo\n"
    captured = capfd.readouterr()
    assert captured.out == "echo foo\n"
    assert not captured.err

    # Success case: test command is run with environment
    proc = subprocess_handler.run_cmd(
        "echo $FOO", capture_output=True, env={"FOO": "bar", **os.environ}
    )
    assert proc.stdout == "bar\n"

    # Failure case: check non-zero return code throws an exception
    with pytest.raises(subprocess.CalledProcessError):
        subprocess_handler.run_cmd("exit 1")

    # Failure case: check stderr is redirected to stdout on non-zero
    # return code
    with pytest.raises(subprocess.CalledProcessError) as exc:
        subprocess_handler.run_cmd("echo foo 1>&2; exit 1", capture_output=True)
    assert exc.value.stdout == "foo\n"
    assert not exc.value.stderr
