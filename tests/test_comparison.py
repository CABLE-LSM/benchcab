"""`pytest` tests for `comparison.py`."""

import contextlib
import io
from pathlib import Path

import pytest

from benchcab import internal
from benchcab.comparison import ComparisonTask

FILE_NAME_A, FILE_NAME_B = "file_a.nc", "file_b.nc"
TASK_NAME = "mock_comparison_task_name"


@pytest.fixture()
def files():
    """Return mock file paths used for comparison."""
    return Path(FILE_NAME_A), Path(FILE_NAME_B)


@pytest.fixture()
def comparison_task(files, mock_cwd, mock_subprocess_handler):
    """Returns a mock `ComparisonTask` instance for testing against."""
    _comparison_task = ComparisonTask(files=files, task_name=TASK_NAME)
    _comparison_task.subprocess_handler = mock_subprocess_handler
    _comparison_task.root_dir = mock_cwd
    return _comparison_task


class TestRun:
    """Tests for `ComparisonTask.run()`."""

    @pytest.fixture()
    def bitwise_cmp_dir(self):
        """Create and return the fluxsite bitwise comparison directory."""
        internal.FLUXSITE_DIRS["BITWISE_CMP"].mkdir(parents=True)
        return internal.FLUXSITE_DIRS["BITWISE_CMP"]

    def test_nccmp_execution(self, comparison_task, files, mock_subprocess_handler):
        """Success case: test nccmp is executed."""
        file_a, file_b = files
        comparison_task.run()
        assert f"nccmp -df {file_a} {file_b}" in mock_subprocess_handler.commands

    @pytest.mark.parametrize(
        ("verbosity", "expected"),
        [
            (
                False,
                f"Success: files {FILE_NAME_A} {FILE_NAME_B} are identical\n",
            ),
            (
                True,
                f"Comparing files {FILE_NAME_A} and {FILE_NAME_B} bitwise...\n"
                f"Success: files {FILE_NAME_A} {FILE_NAME_B} are identical\n",
            ),
        ],
    )
    def test_standard_output(self, comparison_task, verbosity, expected):
        """Success case: test standard output."""
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            comparison_task.run(verbose=verbosity)
        assert buf.getvalue() == expected

    def test_failed_comparison_check(
        self, comparison_task, mock_subprocess_handler, bitwise_cmp_dir
    ):
        """Failure case: test failed comparison check (files differ)."""
        stdout_file = bitwise_cmp_dir / f"{comparison_task.task_name}.txt"
        mock_subprocess_handler.error_on_call = True
        comparison_task.run()
        with stdout_file.open("r", encoding="utf-8") as file:
            assert file.read() == mock_subprocess_handler.stdout

    # TODO(Sean) fix for issue https://github.com/CABLE-LSM/benchcab/issues/162
    @pytest.mark.skip(
        reason="""This will always fail since `parametrize()` parameters are
        dependent on the `mock_cwd` fixture."""
    )
    @pytest.mark.parametrize(
        ("verbosity", "expected"),
        [
            (
                False,
                f"Failure: files {FILE_NAME_A} {FILE_NAME_B} differ. Results of "
                "diff have been written to "
                f"{internal.FLUXSITE_DIRS['BITWISE_CMP']}/{TASK_NAME}\n",
            ),
            (
                True,
                f"Comparing files {FILE_NAME_A} and {FILE_NAME_B} bitwise...\n"
                f"Failure: files {FILE_NAME_A} {FILE_NAME_B} differ. Results of "
                "diff have been written to "
                f"{internal.FLUXSITE_DIRS['BITWISE_CMP']}/{TASK_NAME}\n",
            ),
        ],
    )
    def test_standard_output_on_failure(
        self,
        comparison_task,
        mock_subprocess_handler,
        verbosity,
        expected,
    ):
        """Failure case: test standard output on failure."""
        mock_subprocess_handler.error_on_call = True
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            comparison_task.run(verbose=verbosity)
        assert buf.getvalue() == expected
