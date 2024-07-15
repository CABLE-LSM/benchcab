"""`pytest` tests for `model.py`.

Note: explicit teardown for generated files and directories are not required as
the working directory used for testing is cleaned up in the `_run_around_tests`
pytest autouse fixture.
"""

import re
from pathlib import Path

import pytest

from benchcab import internal
from benchcab.model import Model, remove_module_lines
from benchcab.utils.repo import Repo

TEST_MODEL_ID = 0


@pytest.fixture()
def mock_repo():
    """Return a mock implementation of the `Repo` interface."""

    class MockRepo(Repo):
        """A mock implementation of the `Repo` interface used for testing."""

        def __init__(self) -> None:
            self.handle = "trunk"

        def checkout(self, path: Path):
            pass

        def get_branch_name(self) -> str:
            return self.handle

        def get_revision(self, path: Path) -> str:
            pass

    return MockRepo()


@pytest.fixture(params=[False, True])
def mpi(request):
    """Return a parametrized mpi flag for testing."""
    return request.param


@pytest.fixture()
def model(mock_repo, mock_subprocess_handler, mock_environment_modules_handler):
    """Return a mock `Model` instance for testing against."""
    _model = Model(repo=mock_repo, model_id=TEST_MODEL_ID)
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

    @pytest.mark.parametrize(
        ("mpi", "expected_exe"),
        [(False, internal.CABLE_EXE), (True, internal.CABLE_MPI_EXE)],
    )
    def test_get_exe_path(self, model, mpi, expected_exe):
        """Success case: get path to executable."""
        assert (
            model.get_exe_path(mpi=mpi)
            == internal.SRC_DIR / model.name / "bin" / expected_exe
        )


class TestGetBuildFlags:
    """Tests for `Model.get_build_flags()`."""

    @pytest.fixture(params=[False, True])
    def codecov(self, request) -> bool:
        """Return a parametrized codecov option for testing."""
        return request.param

    @pytest.fixture(params=["gfortran", "ifort"])
    def compiler_id(self, request):
        """Return a parametrized compiler_id flag for testing."""
        return request.param

    @pytest.fixture()
    def cmake_flags(self, codecov, mpi, compiler_id):
        """Generate build flags used in CMake build."""
        codecov_build_type = {
            False: "Release",
            True: "Debug",
        }

        mpi_args = {True: "ON", False: "OFF"}

        codecov_init_args = {
            False: "",
            True: (
                f"\"-prof-gen=srcpos -prof-dir={(internal.CODECOV_DIR / 'R0').absolute()}\""
                if compiler_id in ["ifort", "ifx"]
                else ""
            ),
        }

        return {
            "build_type": codecov_build_type[codecov],
            "mpi": mpi_args[mpi],
            "flags_init": codecov_init_args[codecov],
        }

    def test_get_build_flags(self, model, mpi, codecov, compiler_id, cmake_flags):
        """Failure case: If coverage flags are passed to non-Intel compiler."""
        codecov_compilers = ["ifort", "ifx"]
        if compiler_id not in codecov_compilers and codecov:
            with pytest.raises(
                RuntimeError,
                match=re.escape(
                    f"""For code coverage, the only supported compilers are {codecov_compilers}
                User has {compiler_id} in their environment"""
                ),
            ):
                model._get_build_flags(mpi, codecov, compiler_id)
            return

        # Success case: get expected build flags to pass to CMake.
        assert model._get_build_flags(mpi, codecov, compiler_id) == cmake_flags


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
