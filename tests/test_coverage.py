"""`pytest` tests for `coverage.py`.

Note: explicit teardown for generated files and directories are not required as
the working directory used for testing is cleaned up in the `_run_around_tests`
pytest autouse fixture.
"""

from pathlib import Path

import pytest

from benchcab import internal
from benchcab.coverage import CoverageTask

COVERAGE_REALISATION = "R0"
PROJECT_NAME = "BENCHCAB_TEST"
DPI_FILE = "test.dpi"
SPI_FILE = "test.spi"


@pytest.fixture()
def coverage_task(
    coverage_dir, mock_subprocess_handler, mock_environment_modules_handler
):
    """Returns a mock `CoverageTask` instance for testing against."""
    _coverage_task = CoverageTask(
        coverage_dir=coverage_dir,
        project_name=PROJECT_NAME,
        dpi_file=DPI_FILE,
        spi_file=SPI_FILE,
    )
    _coverage_task.subprocess_handler = mock_subprocess_handler
    _coverage_task.modules_handler = mock_environment_modules_handler
    return _coverage_task


class TestRun:
    """Tests for `CoverageTask.run()`."""

    @pytest.fixture(autouse=True)
    def coverage_dir(self) -> Path:
        """Create and return the fluxsite bitwise coverage directory."""
        coverage_path = internal.CODECOV_DIR / COVERAGE_REALISATION
        coverage_path.mkdir(parents=True)
        return coverage_path

    def test_profmerge_execution(self, coverage_task, mock_subprocess_handler):
        """Success case: test profmerge is executed."""
        coverage_task.run()
        assert f"profmerge -prof-dpi {DPI_FILE}" in mock_subprocess_handler.commands

    def test_codecov_execution(self, coverage_task, mock_subprocess_handler):
        """Success case: test codecov is executed."""
        coverage_task.run()
        assert (
            f"codecov -prj {PROJECT_NAME} -dpi {DPI_FILE} -spi {SPI_FILE}"
            in mock_subprocess_handler.commands
        )
