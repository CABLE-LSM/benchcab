"""`pytest` tests for `model.py`.

Note: explicit teardown for generated files and directories are not required as
the working directory used for testing is cleaned up in the `_run_around_tests`
pytest autouse fixture.
"""

import os
from pathlib import Path

import pytest

from benchcab import internal
from benchcab.model import Model, remove_module_lines
from benchcab.utils.repo import Repo


@pytest.fixture()
def mock_repo():
    """Return a mock implementation of the `Repo` interface."""

    class MockRepo(Repo):
        """A mock implementation of the `Repo` interface used for testing."""

        def __init__(self) -> None:
            self.handle = "trunk"

        def checkout(self, verbose=False):
            pass

        def get_branch_name(self) -> str:
            return self.handle

        def get_revision(self) -> str:
            pass

    return MockRepo()


@pytest.fixture()
def model(mock_repo, mock_subprocess_handler, mock_environment_modules_handler):
    """Return a mock `Model` instance for testing against."""
    _model = Model(repo=mock_repo)
    _model.subprocess_handler = mock_subprocess_handler
    _model.modules_handler = mock_environment_modules_handler
    return _model


class TestModelID:
    """Tests for `Model.model_id`."""

    def test_set_and_get_model_id(self, model):
        """Success case: set and get model ID."""
        val = 456
        model.model_id = val
        assert model.model_id == val

    def test_undefined_model_id(self, model):
        """Failure case: access undefined model ID."""
        model.model_id = None
        with pytest.raises(
            RuntimeError, match="Attempting to access undefined model ID"
        ):
            _ = model.model_id


class TestGetExePath:
    """Tests for `Model.get_exe_path()`."""

    def test_serial_exe_path(self, model):
        """Success case: get path to serial executable."""
        assert (
            model.get_exe_path()
            == internal.SRC_DIR / model.name / "offline" / internal.CABLE_EXE
        )


# TODO(Sean) remove for issue https://github.com/CABLE-LSM/benchcab/issues/211
@pytest.mark.skip(
    reason="""Skip tests for `checkout` until tests for repo.py
    have been implemented."""
)
class TestCheckout:
    """Tests for `Model.checkout()`."""

    def test_checkout_command_execution(self, model, mock_subprocess_handler):
        """Success case: `svn checkout` command is executed."""
        model.checkout()
        assert (
            "svn checkout https://trac.nci.org.au/svn/cable/trunk src/trunk"
            in mock_subprocess_handler.commands
        )

    def test_checkout_command_execution_with_revision_number(
        self, model, mock_subprocess_handler
    ):
        """Success case: `svn checkout` command is executed with specified revision number."""
        model.revision = 9000
        model.checkout()
        assert (
            "svn checkout -r 9000 https://trac.nci.org.au/svn/cable/trunk src/trunk"
            in mock_subprocess_handler.commands
        )


# TODO(Sean) remove for issue https://github.com/CABLE-LSM/benchcab/issues/211
@pytest.mark.skip(
    reason="""Skip tests for `svn_info_show_item` until tests for repo.py
    have been implemented."""
)
class TestSVNInfoShowItem:
    """Tests for `Model.svn_info_show_item()`."""

    def test_svn_info_command_execution(self, model, mock_subprocess_handler):
        """Success case: call svn info command and get result."""
        assert (
            model.svn_info_show_item("some-mock-item") == mock_subprocess_handler.stdout
        )
        assert (
            "svn info --show-item some-mock-item src/trunk"
            in mock_subprocess_handler.commands
        )

    def test_white_space_removed_from_standard_output(
        self, model, mock_subprocess_handler
    ):
        """Success case: test leading and trailing white space is removed from standard output."""
        mock_subprocess_handler.stdout = " \n\n mock standard output \n\n"
        assert (
            model.svn_info_show_item("some-mock-item")
            == mock_subprocess_handler.stdout.strip()
        )


class TestPreBuild:
    """Tests for `Model.pre_build()`."""

    @pytest.fixture(autouse=True)
    def _setup(self, model):
        """Setup precondition for `Model.pre_build()`."""
        (internal.SRC_DIR / model.name / "offline").mkdir(parents=True)
        (internal.SRC_DIR / model.name / "offline" / "Makefile").touch()
        (internal.SRC_DIR / model.name / "offline" / "parallel_cable").touch()
        (internal.SRC_DIR / model.name / "offline" / "serial_cable").touch()
        (internal.SRC_DIR / model.name / "offline" / "foo.f90").touch()

    def test_source_files_and_scripts_are_copied_to_tmp_dir(self, model):
        """Success case: test source files and scripts are copied to .tmp."""
        model.pre_build()
        tmp_dir = internal.SRC_DIR / model.name / "offline" / ".tmp"
        assert (tmp_dir / "Makefile").exists()
        assert (tmp_dir / "parallel_cable").exists()
        assert (tmp_dir / "serial_cable").exists()
        assert (tmp_dir / "foo.f90").exists()


class TestRunBuild:
    """Tests for `Model.run_build()`."""

    @pytest.fixture()
    def netcdf_root(self):
        """Return an absolute path to use as the NETCDF_ROOT environment variable."""
        return "/mock/path/to/root"

    @pytest.fixture()
    def modules(self):
        """Return a list of modules for testing."""
        return ["foo", "bar"]

    @pytest.fixture()
    def env(self, netcdf_root):
        """Return a dictionary containing the required environment variables."""
        return {
            "NCDIR": f"{netcdf_root}/lib/Intel",
            "NCMOD": f"{netcdf_root}/include/Intel",
            "CFLAGS": "-O2 -fp-model precise",
            "LDFLAGS": f"-L{netcdf_root}/lib/Intel -O0",
            "LD": "-lnetcdf -lnetcdff",
            "FC": "ifort",
        }

    @pytest.fixture(autouse=True)
    def _setup(self, model, netcdf_root):
        """Setup precondition for `Model.run_build()`."""
        (internal.SRC_DIR / model.name / "offline" / ".tmp").mkdir(parents=True)

        # This is required so that we can use the NETCDF_ROOT environment variable
        # when running `make`, and `serial_cable` and `parallel_cable` scripts:
        os.environ["NETCDF_ROOT"] = netcdf_root

    def test_build_command_execution(
        self, model, mock_subprocess_handler, modules, netcdf_root
    ):
        """Success case: test build commands are run."""
        model.run_build(modules)
        assert mock_subprocess_handler.commands == [
            "make -f Makefile",
            './serial_cable "ifort" "-O2 -fp-model precise"'
            f' "-L{netcdf_root}/lib/Intel -O0" "-lnetcdf -lnetcdff" '
            f'"{netcdf_root}/include/Intel"',
        ]

    def test_modules_loaded_at_runtime(
        self, model, mock_environment_modules_handler, modules
    ):
        """Success case: test modules are loaded at runtime."""
        model.run_build(modules)
        assert (
            "module load " + " ".join(modules)
        ) in mock_environment_modules_handler.commands
        assert (
            "module unload " + " ".join(modules)
        ) in mock_environment_modules_handler.commands

    def test_commands_are_run_with_environment_variables(
        self, model, mock_subprocess_handler, modules, env
    ):
        """Success case: test commands are run with the correct environment variables."""
        model.run_build(modules)
        for kv in env.items():
            assert kv in mock_subprocess_handler.env.items()


class TestPostBuild:
    """Tests for `Model.post_build()`."""

    @pytest.fixture(autouse=True)
    def _setup(self, model):
        """Setup precondition for `Model.post_build()`."""
        (internal.SRC_DIR / model.name / "offline" / ".tmp").mkdir(parents=True)
        (
            internal.SRC_DIR / model.name / "offline" / ".tmp" / internal.CABLE_EXE
        ).touch()

    def test_exe_moved_to_offline_dir(self, model):
        """Success case: test executable is moved to offline directory."""
        model.post_build()
        tmp_dir = internal.SRC_DIR / model.name / "offline" / ".tmp"
        assert not (tmp_dir / internal.CABLE_EXE).exists()
        offline_dir = internal.SRC_DIR / model.name / "offline"
        assert (offline_dir / internal.CABLE_EXE).exists()


class TestCustomBuild:
    """Tests for `Model.custom_build()`."""

    @pytest.fixture()
    def build_script(self, model):
        """Create a custom build script and return its path.

        The return value is the path relative to root directory of the repository.
        """
        _build_script = internal.SRC_DIR / model.name / "my-custom-build.sh"
        _build_script.parent.mkdir(parents=True)
        _build_script.touch()
        return _build_script.relative_to(internal.SRC_DIR / model.name)

    @pytest.fixture()
    def modules(self):
        """Return a list of modules for testing."""
        return ["foo", "bar"]

    def test_build_command_execution(
        self, model, mock_subprocess_handler, build_script, modules
    ):
        """Success case: execute the build command for a custom build script."""
        model.build_script = str(build_script)
        model.custom_build(modules)
        assert "./tmp-build.sh" in mock_subprocess_handler.commands

    def test_modules_loaded_at_runtime(
        self, model, mock_environment_modules_handler, build_script, modules
    ):
        """Success case: test modules are loaded at runtime."""
        model.build_script = str(build_script)
        model.custom_build(modules)
        assert (
            "module load " + " ".join(modules)
        ) in mock_environment_modules_handler.commands
        assert (
            "module unload " + " ".join(modules)
        ) in mock_environment_modules_handler.commands

    def test_file_not_found_exception(self, model, build_script, modules):
        """Failure case: cannot find custom build script."""
        build_script_path = internal.SRC_DIR / model.name / build_script
        build_script_path.unlink()
        model.build_script = str(build_script)
        with pytest.raises(
            FileNotFoundError,
            match=f"The build script, {build_script_path}, could not be "
            "found. Do you need to specify a different build script with the 'build_script' "
            "option in config.yaml?",
        ):
            model.custom_build(modules)


class TestRemoveModuleLines:
    """Tests for `remove_module_lines()`."""

    def test_module_lines_removed_from_shell_script(self):
        """Success case: test 'module' lines are removed from mock shell script."""
        file_path = Path("test-build.sh")
        with file_path.open("w", encoding="utf-8") as file:
            file.write(
                """#!/bin/bash
module add bar
module purge

host_gadi()
{
   . /etc/bashrc
   module purge
   module add intel-compiler/2019.5.281
   module add netcdf/4.6.3
   module load foo
   modules
   echo foo && module load
   echo foo # module load
   # module load foo

   if [[ $1 = 'mpi' ]]; then
      module add intel-mpi/2019.5.281
   fi
}
"""
            )

        remove_module_lines(file_path)

        with file_path.open("r", encoding="utf-8") as file:
            assert file.read() == (
                """#!/bin/bash

host_gadi()
{
   . /etc/bashrc
   modules
   echo foo # module load
   # module load foo

   if [[ $1 = 'mpi' ]]; then
   fi
}
"""
            )
