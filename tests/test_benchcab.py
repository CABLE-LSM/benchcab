"""`pytest` tests for `benchcab.py`.

Note: explicit teardown for generated files and directories are not required as
the working directory used for testing is cleaned up in the `_run_around_tests`
pytest autouse fixture.
"""

import contextlib
import io
from pathlib import Path
from subprocess import CalledProcessError

import pytest

from benchcab import internal
from benchcab.benchcab import Benchcab


@pytest.fixture()
def app(config, mock_cwd, mock_subprocess_handler):
    """Returns a mock `Benchcab` instance for testing against."""
    _app = Benchcab(
        argv=["benchcab", "fluxsite"],
        benchcab_exe_path=Path("/path/to/benchcab"),
        config=config,
        validate_env=False,
    )
    _app.subprocess_handler = mock_subprocess_handler
    _app.root_dir = mock_cwd
    return _app


class TestFluxsiteSubmitJob:
    """Tests for `Benchcab.fluxsite_submit_job()`."""

    def test_qsub_execution(self, app, mock_subprocess_handler, mock_cwd):
        """Success case: test qsub command is executed."""
        app.fluxsite_submit_job()
        assert (
            f"qsub {mock_cwd / internal.QSUB_FNAME}" in mock_subprocess_handler.commands
        )

    def test_default_standard_output(self, app, mock_subprocess_handler):
        """Success case: test default standard output."""
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            app.fluxsite_submit_job()
        assert buf.getvalue() == (
            "Creating PBS job script to run fluxsite tasks on compute "
            f"nodes: {internal.QSUB_FNAME}\n"
            f"PBS job submitted: {mock_subprocess_handler.stdout}\n"
            "The CABLE log file for each task is written to "
            f"{internal.FLUXSITE_LOG_DIR}/<task_name>_log.txt\n"
            "The CABLE standard output for each task is written to "
            f"{internal.FLUXSITE_TASKS_DIR}/<task_name>/out.txt\n"
            "The NetCDF output for each task is written to "
            f"{internal.FLUXSITE_OUTPUT_DIR}/<task_name>_out.nc\n"
        )

    def test_qsub_non_zero_exit_code_prints_error(self, app, mock_subprocess_handler):
        """Failure case: qsub non-zero exit code prints an error message."""
        mock_subprocess_handler.error_on_call = True
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            with pytest.raises(CalledProcessError):
                app.fluxsite_submit_job()
        assert buf.getvalue() == (
            "Creating PBS job script to run fluxsite tasks on compute "
            f"nodes: {internal.QSUB_FNAME}\n"
            f"Error when submitting job to NCI queue\n{mock_subprocess_handler.stdout}\n"
        )

    def test_benchcab_exe_path_exception(self, app):
        """Failure case: test exception is raised when benchcab_exe_path is None."""
        app.benchcab_exe_path = None
        with pytest.raises(
            RuntimeError, match="Path to benchcab executable is undefined."
        ):
            app.fluxsite_submit_job()
