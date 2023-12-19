"""`pytest` tests for `comparison.py`.

Note: explicit teardown for generated files and directories are not required as
the working directory used for testing is cleaned up in the `_run_around_tests`
pytest autouse fixture.
"""

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
def comparison_task(files, mock_subprocess_handler):
    """Returns a mock `ComparisonTask` instance for testing against."""
    _comparison_task = ComparisonTask(files=files, task_name=TASK_NAME)
    _comparison_task.subprocess_handler = mock_subprocess_handler
    return _comparison_task


class TestRun:
    """Tests for `ComparisonTask.run()`."""

    @pytest.fixture(autouse=True)
    def bitwise_cmp_dir(self):
        """Create and return the fluxsite bitwise comparison directory."""
        internal.FLUXSITE_DIRS["BITWISE_CMP"].mkdir(parents=True)
        return internal.FLUXSITE_DIRS["BITWISE_CMP"]

    def test_nccmp_execution(self, comparison_task, files, mock_subprocess_handler):
        """Success case: test nccmp is executed."""
        file_a, file_b = files
        comparison_task.run()
        assert f"nccmp -df {file_a} {file_b}" in mock_subprocess_handler.commands

    def test_failed_comparison_check(
        self, comparison_task, mock_subprocess_handler, bitwise_cmp_dir
    ):
        """Failure case: test failed comparison check (files differ)."""
        stdout_file = bitwise_cmp_dir / f"{comparison_task.task_name}.txt"
        mock_subprocess_handler.error_on_call = True
        comparison_task.run()
        with stdout_file.open("r", encoding="utf-8") as file:
            assert file.read() == mock_subprocess_handler.stdout
