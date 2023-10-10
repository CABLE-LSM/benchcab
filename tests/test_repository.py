"""`pytest` tests for `repository.py`."""

import contextlib
import io
import os
from pathlib import Path

import pytest

from benchcab import internal
from benchcab.repository import CableRepository, remove_module_lines


@pytest.fixture()
def repo(mock_cwd, mock_subprocess_handler, mock_environment_modules_handler):
    """Return a mock `CableRepository` instance for testing against."""
    _repo = CableRepository(path="trunk")
    _repo.root_dir = mock_cwd
    _repo.subprocess_handler = mock_subprocess_handler
    _repo.modules_handler = mock_environment_modules_handler
    return _repo


class TestRepoID:
    """Tests for `CableRepository.repo_id`."""

    def test_set_and_get_repo_id(self, repo):
        """Success case: set and get repository ID."""
        val = 456
        repo.repo_id = val
        assert repo.repo_id == val

    def test_undefined_repo_id(self, repo):
        """Failure case: access undefined repository ID."""
        repo.repo_id = None
        with pytest.raises(
            RuntimeError, match="Attempting to access undefined repo ID"
        ):
            _ = repo.repo_id


class TestCheckout:
    """Tests for `CableRepository.checkout()`."""

    def test_checkout_command_execution(self, repo, mock_cwd, mock_subprocess_handler):
        """Success case: `svn checkout` command is executed."""
        repo.checkout()
        assert (
            f"svn checkout https://trac.nci.org.au/svn/cable/trunk {mock_cwd}/src/trunk"
            in mock_subprocess_handler.commands
        )

    def test_checkout_command_execution_with_revision_number(
        self, repo, mock_cwd, mock_subprocess_handler
    ):
        """Success case: `svn checkout` command is executed with specified revision number."""
        repo.revision = 9000
        repo.checkout()
        assert (
            f"svn checkout -r 9000 https://trac.nci.org.au/svn/cable/trunk {mock_cwd}/src/trunk"
            in mock_subprocess_handler.commands
        )

    def test_standard_output(self, repo, mock_subprocess_handler):
        """Success case: test standard output."""
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            repo.checkout()
        assert (
            buf.getvalue()
            == f"Successfully checked out trunk at revision {mock_subprocess_handler.stdout}\n"
        )
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            repo.checkout(verbose=True)
        assert (
            buf.getvalue()
            == f"Successfully checked out trunk at revision {mock_subprocess_handler.stdout}\n"
        )


class TestSVNInfoShowItem:
    """Tests for `CableRepository.svn_info_show_item()`."""

    def test_svn_info_command_execution(self, repo, mock_subprocess_handler, mock_cwd):
        """Success case: call svn info command and get result."""
        assert (
            repo.svn_info_show_item("some-mock-item") == mock_subprocess_handler.stdout
        )
        assert (
            f"svn info --show-item some-mock-item {mock_cwd}/src/trunk"
            in mock_subprocess_handler.commands
        )

    def test_white_space_removed_from_standard_output(
        self, repo, mock_subprocess_handler
    ):
        """Success case: test leading and trailing white space is removed from standard output."""
        mock_subprocess_handler.stdout = " \n\n mock standard output \n\n"
        assert (
            repo.svn_info_show_item("some-mock-item")
            == mock_subprocess_handler.stdout.strip()
        )


class TestPreBuild:
    """Tests for `CableRepository.pre_build()`."""

    @pytest.fixture(autouse=True)
    def _setup(self, repo):
        """Setup precondition for `CableRepository.pre_build()`."""
        (internal.SRC_DIR / repo.name / "offline").mkdir(parents=True)
        (internal.SRC_DIR / repo.name / "offline" / "Makefile").touch()
        (internal.SRC_DIR / repo.name / "offline" / "parallel_cable").touch()
        (internal.SRC_DIR / repo.name / "offline" / "serial_cable").touch()
        (internal.SRC_DIR / repo.name / "offline" / "foo.f90").touch()

    def test_source_files_and_scripts_are_copied_to_tmp_dir(self, repo):
        """Success case: test source files and scripts are copied to .tmp."""
        repo.pre_build()
        tmp_dir = internal.SRC_DIR / repo.name / "offline" / ".tmp"
        assert (tmp_dir / "Makefile").exists()
        assert (tmp_dir / "parallel_cable").exists()
        assert (tmp_dir / "serial_cable").exists()
        assert (tmp_dir / "foo.f90").exists()

    @pytest.mark.parametrize(
        ("verbosity", "expected"),
        [
            (
                False,
                "",
            ),
            (
                True,
                "mkdir src/trunk/offline/.tmp\n"
                "cp -p src/trunk/offline/foo.f90 src/trunk/offline/.tmp\n"
                "cp -p src/trunk/offline/Makefile src/trunk/offline/.tmp\n"
                "cp -p src/trunk/offline/parallel_cable src/trunk/offline/.tmp\n"
                "cp -p src/trunk/offline/serial_cable src/trunk/offline/.tmp\n",
            ),
        ],
    )
    def test_standard_output(self, repo, verbosity, expected):
        """Success case: test standard output."""
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            repo.pre_build(verbose=verbosity)
        assert buf.getvalue() == expected


class TestRunBuild:
    """Tests for `CableRepository.run_build()`."""

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
    def _setup(self, repo, netcdf_root):
        """Setup precondition for `CableRepository.run_build()`."""
        (internal.SRC_DIR / repo.name / "offline" / ".tmp").mkdir(parents=True)

        # This is required so that we can use the NETCDF_ROOT environment variable
        # when running `make`, and `serial_cable` and `parallel_cable` scripts:
        os.environ["NETCDF_ROOT"] = netcdf_root

    def test_build_command_execution(
        self, repo, mock_subprocess_handler, modules, netcdf_root
    ):
        """Success case: test build commands are run."""
        repo.run_build(modules)
        assert mock_subprocess_handler.commands == [
            "make -f Makefile",
            './serial_cable "ifort" "-O2 -fp-model precise"'
            f' "-L{netcdf_root}/lib/Intel -O0" "-lnetcdf -lnetcdff" '
            f'"{netcdf_root}/include/Intel"',
        ]

    def test_modules_loaded_at_runtime(
        self, repo, mock_environment_modules_handler, modules
    ):
        """Success case: test modules are loaded at runtime."""
        repo.run_build(modules)
        assert (
            "module load " + " ".join(modules)
        ) in mock_environment_modules_handler.commands
        assert (
            "module unload " + " ".join(modules)
        ) in mock_environment_modules_handler.commands

    def test_commands_are_run_with_environment_variables(
        self, repo, mock_subprocess_handler, modules, env
    ):
        """Success case: test commands are run with the correct environment variables."""
        repo.run_build(modules)
        for kv in env.items():
            assert kv in mock_subprocess_handler.env.items()

    @pytest.mark.parametrize(
        ("verbosity", "expected"),
        [
            (False, ""),
            (True, "Loading modules: foo bar\nUnloading modules: foo bar\n"),
        ],
    )
    def test_standard_output(self, repo, modules, verbosity, expected):
        """Success case: test standard output."""
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            repo.run_build(modules, verbose=verbosity)
        assert buf.getvalue() == expected


class TestPostBuild:
    """Tests for `CableRepository.post_build()`."""

    @pytest.fixture(autouse=True)
    def _setup(self, repo):
        """Setup precondition for `CableRepository.post_build()`."""
        (internal.SRC_DIR / repo.name / "offline" / ".tmp").mkdir(parents=True)
        (internal.SRC_DIR / repo.name / "offline" / ".tmp" / internal.CABLE_EXE).touch()

    def test_exe_moved_to_offline_dir(self, repo):
        """Success case: test executable is moved to offline directory."""
        repo.post_build()
        tmp_dir = internal.SRC_DIR / repo.name / "offline" / ".tmp"
        assert not (tmp_dir / internal.CABLE_EXE).exists()
        offline_dir = internal.SRC_DIR / repo.name / "offline"
        assert (offline_dir / internal.CABLE_EXE).exists()

    @pytest.mark.parametrize(
        ("verbosity", "expected"),
        [
            (False, ""),
            (True, "mv src/trunk/offline/.tmp/cable src/trunk/offline/cable\n"),
        ],
    )
    def test_standard_output(self, repo, verbosity, expected):
        """Success case: test non-verbose standard output."""
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            repo.post_build(verbose=verbosity)
        assert buf.getvalue() == expected


class TestCustomBuild:
    """Tests for `CableRepository.custom_build()`."""

    @pytest.fixture()
    def build_script(self, repo):
        """Create a custom build script and return its path.

        The return value is the path relative to root directory of the repository.
        """
        _build_script = internal.SRC_DIR / repo.name / "my-custom-build.sh"
        _build_script.parent.mkdir(parents=True)
        _build_script.touch()
        return _build_script.relative_to(internal.SRC_DIR / repo.name)

    @pytest.fixture()
    def modules(self):
        """Return a list of modules for testing."""
        return ["foo", "bar"]

    def test_build_command_execution(
        self, repo, mock_subprocess_handler, build_script, modules
    ):
        """Success case: execute the build command for a custom build script."""
        repo.build_script = str(build_script)
        repo.custom_build(modules)
        assert "./tmp-build.sh" in mock_subprocess_handler.commands

    def test_modules_loaded_at_runtime(
        self, repo, mock_environment_modules_handler, build_script, modules
    ):
        """Success case: test modules are loaded at runtime."""
        repo.build_script = str(build_script)
        repo.custom_build(modules)
        assert (
            "module load " + " ".join(modules)
        ) in mock_environment_modules_handler.commands
        assert (
            "module unload " + " ".join(modules)
        ) in mock_environment_modules_handler.commands

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
                "",
            ),
            (
                True,
                "Copying src/trunk/my-custom-build.sh to src/trunk/tmp-build.sh\n"
                "chmod +x src/trunk/tmp-build.sh\n"
                "Modifying tmp-build.sh: remove lines that call environment "
                "modules\n"
                "Loading modules: foo bar\n"
                "Unloading modules: foo bar\n",
            ),
        ],
    )
    def test_standard_output(self, repo, build_script, modules, verbosity, expected):
        """Success case: test non-verbose standard output for a custom build script."""
        repo.build_script = str(build_script)
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            repo.custom_build(modules, verbose=verbosity)
        assert buf.getvalue() == expected

    def test_file_not_found_exception(self, repo, build_script, modules, mock_cwd):
        """Failure case: cannot find custom build script."""
        build_script_path = mock_cwd / internal.SRC_DIR / repo.name / build_script
        build_script_path.unlink()
        repo.build_script = str(build_script)
        with pytest.raises(
            FileNotFoundError,
            match=f"The build script, {build_script_path}, could not be "
            "found. Do you need to specify a different build script with the 'build_script' "
            "option in config.yaml?",
        ):
            repo.custom_build(modules)


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
