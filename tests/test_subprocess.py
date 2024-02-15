"""`pytest` tests for `utils/subprocess.py`."""

import itertools
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

    # Parameterization
    @pytest.fixture(params=list(itertools.product([False, True], repeat=3)))
    def generate_params(self, request):
        possible_inputs = request.param
        return {
            "param_verbose": possible_inputs[0],
            "param_capture": possible_inputs[1],
            "param_file": possible_inputs[2],
        }

    @pytest.fixture(params=[("echo foo", "foo\n"), ("echo foo 1>&2", "foo\n")])
    def generated_input(self, request, generate_params):
        command = request.param
        return generate_params | {
            "command": {
                "input": command[0],
                "expected": command[1],
            }
        }

    def _test_verbose(self, is_stdout_verbose, param_verbose, captured, command):
        assert not captured.err
        expected = command["input"] + "\n"
        if param_verbose and is_stdout_verbose:
            expected += command["expected"]
        if is_stdout_verbose or param_verbose:
            assert captured.out == expected
        else:
            assert not captured.out

    def _test_capture_output(self, is_stdout_capture, proc, expected):
        assert not proc.stderr
        if is_stdout_capture:
            assert proc.stdout == expected
        else:
            assert not proc.stdout

    def _test_output_file(self, is_stdout_file, file_path, expected):
        if is_stdout_file:
            with file_path.open("r", encoding="utf-8") as file:
                assert file.read() == expected
        else:
            # TODO: Check for non-existent file
            pass

    def test_subprocess_logic(self, subprocess_handler, generated_input, capfd):

        is_stdout_verbose, is_stdout_output, is_stdout_capture = (False, False, False)
        file_path = None

        if generated_input["param_capture"]:
            is_stdout_capture = True
        elif generated_input["param_file"]:
            is_stdout_output = True
            file_path = Path("out.txt")
        elif generated_input["param_verbose"]:
            is_stdout_verbose = True

        proc = subprocess_handler.run_cmd(
            generated_input["command"]["input"],
            verbose=generated_input["param_verbose"],
            capture_output=generated_input["param_capture"],
            output_file=file_path,
        )
        captured = capfd.readouterr()

        self._test_verbose(
            is_stdout_verbose,
            generated_input["param_verbose"],
            captured,
            generated_input["command"],
        )
        self._test_capture_output(
            is_stdout_capture, proc, generated_input["command"]["expected"]
        )
        self._test_output_file(
            is_stdout_output, file_path, generated_input["command"]["expected"]
        )

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
