"""`pytest` tests for `repository.py`."""

import contextlib
import io
import os
import shutil

import pytest

pytest.skip(allow_module_level=True)

from benchcab import internal
from benchcab.environment_modules import EnvironmentModulesInterface
from benchcab.repository import CableRepository, remove_module_lines
from benchcab.utils.subprocess import SubprocessWrapperInterface

from .common import MOCK_CWD, MockEnvironmentModules, MockSubprocessWrapper


def get_mock_repo(
    subprocess_handler: SubprocessWrapperInterface = MockSubprocessWrapper(),
    modules_handler: EnvironmentModulesInterface = MockEnvironmentModules(),
) -> CableRepository:
    """Returns a mock `CableRepository` instance for testing against."""
    repo = CableRepository(path="trunk")
    repo.root_dir = MOCK_CWD
    repo.subprocess_handler = subprocess_handler
    repo.modules_handler = modules_handler
    return repo


def test_repo_id():
    """Tests for `CableRepository.repo_id`."""
    mock_repo_id = 123

    # Success case: get repository ID
    repo = CableRepository("path/to/repo", repo_id=mock_repo_id)
    assert repo.repo_id == mock_repo_id

    # Success case: set repository ID
    new_repo_id = 456
    repo = CableRepository("path/to/repo", repo_id=mock_repo_id)
    repo.repo_id = new_repo_id
    assert repo.repo_id == new_repo_id

    # Failure case: access undefined repository ID
    repo = CableRepository("path/to/repo")
    with pytest.raises(RuntimeError, match="Attempting to access undefined repo ID"):
        _ = repo.repo_id


def test_checkout():
    """Tests for `CableRepository.checkout()`."""
    # Success case: checkout mock repository
    mock_subprocess = MockSubprocessWrapper()
    repo = get_mock_repo(mock_subprocess)
    repo.checkout()
    assert (
        f"svn checkout https://trac.nci.org.au/svn/cable/trunk {MOCK_CWD}/src/trunk"
        in mock_subprocess.commands
    )

    # Success case: checkout mock repository with specified revision number
    mock_subprocess = MockSubprocessWrapper()
    repo = get_mock_repo(mock_subprocess)
    repo.revision = 9000
    repo.checkout()
    assert (
        f"svn checkout -r 9000 https://trac.nci.org.au/svn/cable/trunk {MOCK_CWD}/src/trunk"
        in mock_subprocess.commands
    )

    # Success case: test non-verbose standard output
    mock_subprocess = MockSubprocessWrapper()
    repo = get_mock_repo(mock_subprocess)
    with contextlib.redirect_stdout(io.StringIO()) as buf:
        repo.checkout()
    assert (
        buf.getvalue()
        == f"Successfully checked out trunk at revision {mock_subprocess.stdout}\n"
    )

    # Success case: test verbose standard output
    mock_subprocess = MockSubprocessWrapper()
    repo = get_mock_repo(mock_subprocess)
    with contextlib.redirect_stdout(io.StringIO()) as buf:
        repo.checkout(verbose=True)
    assert (
        buf.getvalue()
        == f"Successfully checked out trunk at revision {mock_subprocess.stdout}\n"
    )


def test_svn_info_show_item():
    """Tests for `CableRepository.svn_info_show_item()`."""
    # Success case: call svn info command and get result
    mock_subprocess = MockSubprocessWrapper()
    mock_subprocess.stdout = "mock standard output"
    repo = get_mock_repo(mock_subprocess)
    assert repo.svn_info_show_item("some-mock-item") == mock_subprocess.stdout
    assert (
        f"svn info --show-item some-mock-item {MOCK_CWD}/src/trunk"
        in mock_subprocess.commands
    )

    # Success case: test leading and trailing white space is removed from standard output
    mock_subprocess = MockSubprocessWrapper()
    mock_subprocess.stdout = " \n\n mock standard output \n\n"
    repo = get_mock_repo(mock_subprocess)
    assert repo.svn_info_show_item("some-mock-item") == mock_subprocess.stdout.strip()
    assert (
        f"svn info --show-item some-mock-item {MOCK_CWD}/src/trunk"
        in mock_subprocess.commands
    )


def test_pre_build():
    """Tests for `CableRepository.pre_build()`."""
    repo_dir = MOCK_CWD / internal.SRC_DIR / "trunk"
    offline_dir = repo_dir / "offline"
    offline_dir.mkdir(parents=True)
    (offline_dir / "Makefile").touch()
    (offline_dir / "parallel_cable").touch()
    (offline_dir / "serial_cable").touch()
    (offline_dir / "foo.f90").touch()

    # Success case: test source files and scripts are copied to .tmp
    repo = get_mock_repo()
    repo.pre_build()
    assert (offline_dir / ".tmp" / "Makefile").exists()
    assert (offline_dir / ".tmp" / "parallel_cable").exists()
    assert (offline_dir / ".tmp" / "serial_cable").exists()
    assert (offline_dir / ".tmp" / "foo.f90").exists()
    shutil.rmtree(offline_dir / ".tmp")

    # Success case: test non-verbose standard output
    repo = get_mock_repo()
    with contextlib.redirect_stdout(io.StringIO()) as buf:
        repo.pre_build()
    assert not buf.getvalue()
    shutil.rmtree(offline_dir / ".tmp")

    # Success case: test verbose standard output
    repo = get_mock_repo()
    with contextlib.redirect_stdout(io.StringIO()) as buf:
        repo.pre_build(verbose=True)
    assert buf.getvalue() == (
        "mkdir src/trunk/offline/.tmp\n"
        "cp -p src/trunk/offline/foo.f90 src/trunk/offline/.tmp\n"
        "cp -p src/trunk/offline/Makefile src/trunk/offline/.tmp\n"
        "cp -p src/trunk/offline/parallel_cable src/trunk/offline/.tmp\n"
        "cp -p src/trunk/offline/serial_cable src/trunk/offline/.tmp\n"
    )
    shutil.rmtree(offline_dir / ".tmp")


def test_run_build():
    """Tests for `CableRepository.run_build()`."""
    mock_netcdf_root = "/mock/path/to/root"
    mock_modules = ["foo", "bar"]
    (MOCK_CWD / internal.SRC_DIR / "trunk" / "offline" / ".tmp").mkdir(parents=True)

    environment_vars = {
        "NCDIR": f"{mock_netcdf_root}/lib/Intel",
        "NCMOD": f"{mock_netcdf_root}/include/Intel",
        "CFLAGS": "-O2 -fp-model precise",
        "LDFLAGS": f"-L{mock_netcdf_root}/lib/Intel -O0",
        "LD": "-lnetcdf -lnetcdff",
        "FC": "ifort",
    }

    # This is required so that we can use the NETCDF_ROOT environment variable
    # when running `make`, and `serial_cable` and `parallel_cable` scripts:
    os.environ["NETCDF_ROOT"] = mock_netcdf_root

    # Success case: test build commands are run
    mock_subprocess = MockSubprocessWrapper()
    repo = get_mock_repo(subprocess_handler=mock_subprocess)
    repo.run_build(mock_modules)
    assert mock_subprocess.commands == [
        "make -f Makefile",
        './serial_cable "ifort" "-O2 -fp-model precise"'
        f' "-L{mock_netcdf_root}/lib/Intel -O0" "-lnetcdf -lnetcdff" '
        f'"{mock_netcdf_root}/include/Intel"',
    ]

    # Success case: test modules are loaded at runtime
    mock_environment_modules = MockEnvironmentModules()
    repo = get_mock_repo(modules_handler=mock_environment_modules)
    repo.run_build(mock_modules)
    assert (
        "module load " + " ".join(mock_modules)
    ) in mock_environment_modules.commands
    assert (
        "module unload " + " ".join(mock_modules)
    ) in mock_environment_modules.commands

    # Success case: test commands are run with the correct environment variables
    mock_subprocess = MockSubprocessWrapper()
    repo = get_mock_repo(subprocess_handler=mock_subprocess)
    repo.run_build(mock_modules)
    for kv in environment_vars.items():
        assert (kv in mock_subprocess.env.items())

    # Success case: test non-verbose standard output
    repo = get_mock_repo()
    with contextlib.redirect_stdout(io.StringIO()) as buf:
        repo.run_build(mock_modules)
    assert not buf.getvalue()

    # Success case: test verbose standard output
    repo = get_mock_repo()
    with contextlib.redirect_stdout(io.StringIO()) as buf:
        repo.run_build(mock_modules, verbose=True)
    assert buf.getvalue() == (
        f"Loading modules: {' '.join(mock_modules)}\n"
        f"Unloading modules: {' '.join(mock_modules)}\n"
    )


def test_post_build():
    """Tests for `CableRepository.post_build()`."""
    repo_dir = MOCK_CWD / internal.SRC_DIR / "trunk"
    offline_dir = repo_dir / "offline"
    tmp_dir = offline_dir / ".tmp"

    # Success case: test executable is moved to offline directory
    tmp_dir.mkdir(parents=True)
    (tmp_dir / internal.CABLE_EXE).touch()
    repo = get_mock_repo()
    repo.post_build()
    assert not (offline_dir / ".tmp" / internal.CABLE_EXE).exists()
    assert (offline_dir / internal.CABLE_EXE).exists()

    # Success case: test non-verbose standard output
    (tmp_dir / internal.CABLE_EXE).touch()
    repo = get_mock_repo()
    with contextlib.redirect_stdout(io.StringIO()) as buf:
        repo.post_build()
    assert not buf.getvalue()

    # Success case: test verbose standard output
    (tmp_dir / internal.CABLE_EXE).touch()
    repo = get_mock_repo()
    with contextlib.redirect_stdout(io.StringIO()) as buf:
        repo.post_build(verbose=True)
    assert buf.getvalue() == (
        "mv src/trunk/offline/.tmp/cable src/trunk/offline/cable\n"
    )


def test_custom_build():
    """Tests for `CableRepository.custom_build()`."""
    repo_dir = MOCK_CWD / internal.SRC_DIR / "trunk"
    custom_build_script_path = repo_dir / "my-custom-build.sh"
    custom_build_script_path.parent.mkdir(parents=True)
    custom_build_script_path.touch()
    mock_modules = ["foo", "bar"]

    # Success case: execute the build command for a custom build script
    mock_subprocess = MockSubprocessWrapper()
    mock_environment_modules = MockEnvironmentModules()
    repo = get_mock_repo(mock_subprocess, mock_environment_modules)
    repo.build_script = str(custom_build_script_path.relative_to(repo_dir))
    repo.custom_build(mock_modules)
    assert "./tmp-build.sh" in mock_subprocess.commands
    assert (
        "module load " + " ".join(mock_modules)
    ) in mock_environment_modules.commands
    assert (
        "module unload " + " ".join(mock_modules)
    ) in mock_environment_modules.commands

    # Success case: test non-verbose standard output for a custom build script
    repo = get_mock_repo()
    repo.build_script = str(custom_build_script_path.relative_to(repo_dir))
    with contextlib.redirect_stdout(io.StringIO()) as buf:
        repo.custom_build(mock_modules)
    assert not buf.getvalue()

    # Success case: test verbose standard output for a custom build script
    repo = get_mock_repo()
    repo.build_script = str(custom_build_script_path.relative_to(repo_dir))
    with contextlib.redirect_stdout(io.StringIO()) as buf:
        repo.custom_build(mock_modules, verbose=True)
    assert buf.getvalue() == (
        f"Copying {custom_build_script_path} to {custom_build_script_path.parent}/tmp-build.sh\n"
        f"chmod +x {custom_build_script_path.parent}/tmp-build.sh\n"
        "Modifying tmp-build.sh: remove lines that call environment "
        "modules\n"
        f"Loading modules: {' '.join(mock_modules)}\n"
        f"Unloading modules: {' '.join(mock_modules)}\n"
    )

    # Failure case: cannot find custom build script
    custom_build_script_path.unlink()
    repo = get_mock_repo()
    repo.build_script = str(custom_build_script_path.relative_to(repo_dir))
    with pytest.raises(
        FileNotFoundError,
        match=f"The build script, {custom_build_script_path}, could not be "
        "found. Do you need to specify a different build script with the 'build_script' "
        "option in config.yaml?",
    ):
        repo.custom_build(mock_modules)


def test_remove_module_lines():
    """Tests for `remove_module_lines()`."""
    # Success case: test 'module' lines are removed from mock shell script
    file_path = MOCK_CWD / "test-build.sh"
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
