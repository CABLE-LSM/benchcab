# Copyright 2022 ACCESS-NRI and contributors. See the top-level COPYRIGHT file for details.
# SPDX-License-Identifier: Apache-2.0

"""Contains functions and data structures relating to CABLE models."""

import os
import shlex
import shutil
import stat
from pathlib import Path
from typing import Any, Optional

from benchcab import internal
from benchcab.environment_modules import EnvironmentModules, EnvironmentModulesInterface
from benchcab.utils import get_logger
from benchcab.utils.fs import chdir, prepend_path
from benchcab.utils.repo import GitRepo, LocalRepo, Repo
from benchcab.utils.subprocess import SubprocessWrapper, SubprocessWrapperInterface


class Model:
    """A class used to represent a CABLE model version."""

    subprocess_handler: SubprocessWrapperInterface = SubprocessWrapper()
    modules_handler: EnvironmentModulesInterface = EnvironmentModules()

    def __init__(
        self,
        repo: Optional[Repo] = None,
        name: Optional[str] = None,
        patch: Optional[dict] = None,
        patch_remove: Optional[dict] = None,
        build_script: Optional[str] = None,
        install_dir: Optional[str] = None,
        install_dir_absolute: Optional[str] = None,
        model_id: Optional[int] = None,
    ) -> None:
        """Constructor.

        Parameters
        ----------
        repo : Optional[Repo], optional
            Repository.
        name : Optional[str], optional
            Name, by default None
        patch : Optional[dict], optional
            Patch, by default None
        patch_remove : Optional[dict], optional
            Patch remove, by default None
        build_script : Optional[str], optional
            Build script, by default None
        install_dir : Optional[str], optional
            Path to installed executables relative to the project root directory
            of the CABLE repository, by default None.
        install_dir_absolute: Optional[Path], optional
            Absolute path to installed executables for this model instance, by default None.
        model_id : Optional[int], optional
            Model ID, by default None

        """
        self.repo = repo
        self.name = name
        self.patch = patch
        self.patch_remove = patch_remove
        self.build_script = build_script
        self.install_dir = install_dir
        self.install_dir_absolute = install_dir_absolute
        self._model_id = model_id

        self.metadata: dict[str, str] = {}
        self.src_dir = Path()
        self.logger = get_logger()
        # TODO(Sean) we should not have to know whether `repo` is a `GitRepo` or
        # `SVNRepo`, we should only be working with the `Repo` interface.
        # See issue https://github.com/CABLE-LSM/benchcab/issues/210
        if isinstance(repo, (GitRepo, LocalRepo)):
            self.src_dir = Path("src")

    @property
    def model_id(self) -> int:
        """Get or set the model ID."""
        if self._model_id is None:
            msg = "Attempting to access undefined model ID"
            raise RuntimeError(msg)
        return self._model_id

    @model_id.setter
    def model_id(self, value: int):
        self._model_id = value

    def get_exe_path(self, mpi=False) -> Path:
        """Return the path to the built executable."""
        exe = internal.CABLE_MPI_EXE if mpi else internal.CABLE_EXE
        if self.install_dir and self.name:
            return internal.SRC_DIR / self.name / self.install_dir / exe
        if self.install_dir_absolute:
            return Path(self.install_dir_absolute) / exe
        if self.name:
            return internal.SRC_DIR / self.name / "bin" / exe
        msg = "Unknown path to executable."
        raise RuntimeError(msg)

    def add_metadata(self, data: dict[str, str]):
        """Append metadata which describes the model instance.

        Parameters
        ----------
        data: dict[str, str]
            Data to append.

        """
        self.metadata.update(data)

    def get_metadata(self) -> dict:
        """Return metadata which describes the model instance."""
        return self.metadata

    def custom_build(self, modules: list[str]):
        """Build CABLE using a custom build script."""
        build_script_path = internal.SRC_DIR / self.name / self.build_script

        if not build_script_path.is_file():
            msg = (
                f"The build script, {build_script_path}, could not be found. "
                "Do you need to specify a different build script with the "
                "'build_script' option in config.yaml?"
            )
            raise FileNotFoundError(msg)

        tmp_script_path = build_script_path.parent / "tmp-build.sh"

        self.logger.debug(f"Copying {build_script_path} to {tmp_script_path}")
        shutil.copy(build_script_path, tmp_script_path)

        self.logger.debug(f"chmod +x {tmp_script_path}")
        tmp_script_path.chmod(tmp_script_path.stat().st_mode | stat.S_IEXEC)

        self.logger.debug(
            f"Modifying {tmp_script_path.name}: remove lines that call environment modules"
        )

        remove_module_lines(tmp_script_path)

        with chdir(build_script_path.parent), self.modules_handler.load(modules):
            self.subprocess_handler.run_cmd(f"./{tmp_script_path.name}")

    def build(self, modules: list[str], mpi=False):
        """Build CABLE with CMake."""
        path_to_repo = internal.SRC_DIR / self.name
        cmake_args = [
            "-DCMAKE_BUILD_TYPE=Release",
            "-DCABLE_MPI=" + ("ON" if mpi else "OFF"),
        ]
        with chdir(path_to_repo), self.modules_handler.load(
            [internal.CMAKE_MODULE, *modules]
        ):
            env = os.environ.copy()

            # This is required to prevent CMake from finding the conda
            # installation of netcdf-fortran (#279):
            env.pop("LDFLAGS", None)

            # This is required to prevent CMake from finding MPI libraries in
            # the conda environment (#279):
            env.pop("CMAKE_PREFIX_PATH", None)

            # This is required so that the netcdf-fortran library is discoverable by
            # pkg-config:
            prepend_path(
                "PKG_CONFIG_PATH", f"{env['NETCDF_BASE']}/lib/Intel/pkgconfig", env=env
            )

            if self.modules_handler.module_is_loaded("openmpi"):
                # This is required so that the openmpi MPI libraries are discoverable
                # via CMake's `find_package` mechanism:
                prepend_path(
                    "CMAKE_PREFIX_PATH", f"{env['OPENMPI_BASE']}/include/Intel", env=env
                )

            env["CMAKE_BUILD_PARALLEL_LEVEL"] = str(internal.CMAKE_BUILD_PARALLEL_LEVEL)

            self.subprocess_handler.run_cmd(
                "cmake -S . -B build " + " ".join(cmake_args), env=env
            )
            self.subprocess_handler.run_cmd("cmake --build build ", env=env)
            self.subprocess_handler.run_cmd("cmake --install build --prefix .", env=env)


def remove_module_lines(file_path: Path) -> None:
    """Remove lines from `file_path` that call the environment modules package."""
    with file_path.open("r", encoding="utf-8") as file:
        contents = file.read()
    with file_path.open("w", encoding="utf-8") as file:
        for line in contents.splitlines(True):
            cmds = shlex.split(line, comments=True)
            if "module" not in cmds:
                file.write(line)
