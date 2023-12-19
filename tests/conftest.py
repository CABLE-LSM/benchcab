"""Contains pytest fixtures accessible to all tests in the same directory."""

import os
import shutil
import tempfile
from pathlib import Path
from subprocess import CalledProcessError, CompletedProcess
from typing import Optional

import pytest

from benchcab.environment_modules import EnvironmentModulesInterface
from benchcab.utils.subprocess import SubprocessWrapperInterface


@pytest.fixture()
def mock_cwd():
    """Create and return a unique temporary directory to use as the CWD.

    The return value is the path of the directory.
    """
    return Path(tempfile.mkdtemp(prefix="benchcab_tests"))


@pytest.fixture(autouse=True)
def _run_around_tests(mock_cwd):
    """Change into the `mock_cwd` directory."""
    prevdir = Path.cwd()
    os.chdir(mock_cwd.expanduser())

    yield

    os.chdir(prevdir)
    shutil.rmtree(mock_cwd)


@pytest.fixture()
def config():
    """Returns a valid mock config."""
    return {
        "project": "bar",
        "experiment": "five-site-test",
        "modules": [
            "intel-compiler/2021.1.1",
            "openmpi/4.1.0",
            "netcdf/4.7.4",
        ],
        "realisations": [
            {
                "name": "trunk",
                "revision": 9000,
                "path": "trunk",
                "patch": {},
                "patch_remove": {},
                "build_script": "",
            },
            {
                "name": "v3.0-YP-changes",
                "revision": -1,
                "path": "branches/Users/sean/my-branch",
                "patch": {"cable": {"cable_user": {"ENABLE_SOME_FEATURE": False}}},
                "patch_remove": {},
                "build_script": "",
            },
        ],
        "science_configurations": [
            {
                "cable": {
                    "cable_user": {
                        "GS_SWITCH": "medlyn",
                        "FWSOIL_SWITCH": "Haverd2013",
                    }
                }
            },
            {
                "cable": {
                    "cable_user": {
                        "GS_SWITCH": "leuning",
                        "FWSOIL_SWITCH": "Haverd2013",
                    }
                }
            },
        ],
        "fluxsite": {
            "pbs": {
                "ncpus": 16,
                "mem": "64G",
                "walltime": "01:00:00",
                "storage": ["gdata/foo123"],
            },
            "multiprocessing": True,
        },
    }


@pytest.fixture()
def mock_subprocess_handler():
    """Returns a mock implementation of `SubprocessWrapperInterface`."""

    class MockSubprocessWrapper(SubprocessWrapperInterface):
        """A mock implementation of `SubprocessWrapperInterface` used for testing."""

        def __init__(self) -> None:
            self.commands: list[str] = []
            self.stdout = "mock standard output"
            self.error_on_call = False
            self.env = {}

        def run_cmd(
            self,
            cmd: str,
            capture_output: bool = False,
            output_file: Optional[Path] = None,
            verbose: bool = False,
            env: Optional[dict] = None,
        ) -> CompletedProcess:
            self.commands.append(cmd)
            if self.error_on_call:
                raise CalledProcessError(returncode=1, cmd=cmd, output=self.stdout)
            if output_file:
                output_file.touch()
            if env:
                self.env = env
            return CompletedProcess(cmd, returncode=0, stdout=self.stdout)

    return MockSubprocessWrapper()


@pytest.fixture()
def mock_environment_modules_handler():
    """Returns a mock implementation of `EnvironmentModulesInterface`."""

    class MockEnvironmentModules(EnvironmentModulesInterface):
        """A mock implementation of `EnvironmentModulesInterface` used for testing."""

        def __init__(self) -> None:
            self.commands: list[str] = []

        def module_is_avail(self, *args: str) -> bool:
            self.commands.append("module is-avail " + " ".join(args))
            return True

        def module_is_loaded(self, *args: str) -> bool:
            self.commands.append("module is-loaded " + " ".join(args))
            return True

        def module_load(self, *args: str) -> None:
            self.commands.append("module load " + " ".join(args))

        def module_unload(self, *args: str) -> None:
            self.commands.append("module unload " + " ".join(args))

    return MockEnvironmentModules()
