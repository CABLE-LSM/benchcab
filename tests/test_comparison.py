"""`pytest` tests for `comparison.py`."""

import contextlib
import io

import pytest

from benchcab import internal
from benchcab.comparison import ComparisonTask


@pytest.fixture()
def files(mock_cwd):
    """Return mock file paths used for comparison."""
    return mock_cwd / "file_a.nc", mock_cwd / "file_b.nc"


@pytest.fixture()
def comparison_task(files, mock_cwd, mock_subprocess_handler):
    """Returns a mock `ComparisonTask` instance for testing against."""
    _comparison_task = ComparisonTask(
        files=files, task_name="mock_comparison_task_name"
    )
    _comparison_task.subprocess_handler = mock_subprocess_handler
    _comparison_task.root_dir = mock_cwd
    return _comparison_task


class TestRun:
    """Tests for `ComparisonTask.run()`."""

    @pytest.fixture()
    def bitwise_cmp_dir(self, mock_cwd):
        """Create and return the fluxsite bitwise comparison directory."""
        _bitwise_cmp_dir = mock_cwd / internal.FLUXSITE_DIRS["BITWISE_CMP"]
        _bitwise_cmp_dir.mkdir(parents=True)
        return _bitwise_cmp_dir

    def test_nccmp_execution(self, comparison_task, files, mock_subprocess_handler):
        """Success case: test nccmp is executed."""
        file_a, file_b = files
        comparison_task.run()
        assert f"nccmp -df {file_a} {file_b}" in mock_subprocess_handler.commands

    def test_default_standard_output(self, comparison_task, files):
        """Success case: test default standard output."""
        file_a, file_b = files
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            comparison_task.run()
        assert (
            buf.getvalue()
            == f"Success: files {file_a.name} {file_b.name} are identical\n"
        )

    def test_verbose_standard_output(self, comparison_task, files):
        """Success case: test verbose standard output."""
        file_a, file_b = files
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            comparison_task.run(verbose=True)
        assert buf.getvalue() == (
            f"Comparing files {file_a.name} and {file_b.name} bitwise...\n"
            f"Success: files {file_a.name} {file_b.name} are identical\n"
        )

    def test_failed_comparison_check(
        self, comparison_task, mock_subprocess_handler, bitwise_cmp_dir
    ):
        """Failure case: test failed comparison check (files differ)."""
        stdout_file = bitwise_cmp_dir / f"{comparison_task.task_name}.txt"
        mock_subprocess_handler.error_on_call = True
        comparison_task.run()
        with stdout_file.open("r", encoding="utf-8") as file:
            assert file.read() == mock_subprocess_handler.stdout

    def test_default_standard_output_on_failure(
        self, comparison_task, files, mock_subprocess_handler, bitwise_cmp_dir
    ):
        """Failure case: test non-verbose standard output on failure."""
        file_a, file_b = files
        stdout_file = bitwise_cmp_dir / f"{comparison_task.task_name}.txt"
        mock_subprocess_handler.error_on_call = True
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            comparison_task.run()
        assert buf.getvalue() == (
            f"Failure: files {file_a.name} {file_b.name} differ. Results of diff "
            f"have been written to {stdout_file}\n"
        )

    def test_verbose_standard_output_on_failure(
        self, comparison_task, files, mock_subprocess_handler, bitwise_cmp_dir
    ):
        """Failure case: test verbose standard output on failure."""
        file_a, file_b = files
        mock_subprocess_handler.error_on_call = True
        stdout_file = bitwise_cmp_dir / f"{comparison_task.task_name}.txt"
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            comparison_task.run(verbose=True)
        assert buf.getvalue() == (
            f"Comparing files {file_a.name} and {file_b.name} bitwise...\n"
            f"Failure: files {file_a.name} {file_b.name} differ. Results of diff "
            f"have been written to {stdout_file}\n"
        )
