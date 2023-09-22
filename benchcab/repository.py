# Copyright 2022 ACCESS-NRI and contributors. See the top-level COPYRIGHT file for details.
# SPDX-License-Identifier: Apache-2.0

"""A module containing functions and data structures for manipulating CABLE repositories."""

import os
import shlex
import shutil
import stat
from pathlib import Path
from typing import Optional

from benchcab import internal
from benchcab.environment_modules import EnvironmentModulesInterface, EnvironmentModules
from benchcab.utils.subprocess import SubprocessWrapperInterface, SubprocessWrapper
from benchcab.utils.fs import chdir, copy2, rename


class CableRepository:
    """A class used to represent a CABLE repository."""

    root_dir: Path = internal.CWD
    subprocess_handler: SubprocessWrapperInterface = SubprocessWrapper()
    modules_handler: EnvironmentModulesInterface = EnvironmentModules()

    def __init__(
        self,
        path: str,
        name: Optional[str] = None,
        revision: Optional[int] = None,
        patch: Optional[dict] = None,
        patch_remove: Optional[dict] = None,
        build_script: Optional[str] = None,
        repo_id: Optional[int] = None,
    ) -> None:
        self.path = Path(path)
        self.name = name if name else self.path.name
        self.revision = revision
        self.patch = patch
        self.patch_remove = patch_remove
        self.build_script = build_script
        self._repo_id = repo_id

    @property
    def repo_id(self) -> int:
        """Get or set the repo ID."""
        if self._repo_id is None:
            raise RuntimeError("Attempting to access undefined repo ID")
        return self._repo_id

    @repo_id.setter
    def repo_id(self, value: int):
        self._repo_id = value

    def checkout(self, verbose=False) -> None:
        """Checkout a branch of CABLE."""
        # TODO(Sean) do nothing if the repository has already been checked out?
        # This also relates the 'clean' feature.

        cmd = "svn checkout"

        if self.revision:
            cmd += f" -r {self.revision}"

        path_to_repo = self.root_dir / internal.SRC_DIR / self.name
        cmd += f" {internal.CABLE_SVN_ROOT}/{self.path} {path_to_repo}"

        self.subprocess_handler.run_cmd(cmd, verbose=verbose)

        revision = self.svn_info_show_item("revision")
        print(f"Successfully checked out {self.name} at revision {revision}")

    def svn_info_show_item(self, item: str) -> str:
        """A wrapper around `svn info --show-item <item> <path-to-repo>`."""
        path_to_repo = self.root_dir / internal.SRC_DIR / self.name
        proc = self.subprocess_handler.run_cmd(
            f"svn info --show-item {item} {path_to_repo}", capture_output=True
        )
        return proc.stdout.strip()

    def custom_build(self, modules: list[str], verbose=False):
        """Build CABLE using a custom build script."""

        build_script_path = (
            self.root_dir / internal.SRC_DIR / self.name / self.build_script
        )

        if not build_script_path.is_file():
            raise FileNotFoundError(
                f"The build script, {build_script_path}, could not be found. "
                "Do you need to specify a different build script with the "
                "'build_script' option in config.yaml?",
            )

        tmp_script_path = build_script_path.parent / "tmp-build.sh"

        if verbose:
            print(f"Copying {build_script_path} to {tmp_script_path}")
        shutil.copy(build_script_path, tmp_script_path)

        if verbose:
            print(f"chmod +x {tmp_script_path}")
        tmp_script_path.chmod(tmp_script_path.stat().st_mode | stat.S_IEXEC)

        if verbose:
            print(
                f"Modifying {tmp_script_path.name}: remove lines that call "
                "environment modules"
            )
        remove_module_lines(tmp_script_path)

        with chdir(build_script_path.parent), self.modules_handler.load(
            modules, verbose=verbose
        ):
            self.subprocess_handler.run_cmd(
                f"./{tmp_script_path.name}",
                verbose=verbose,
            )

    def pre_build(self, verbose=False):
        """Runs CABLE pre-build steps."""

        path_to_repo = self.root_dir / internal.SRC_DIR / self.name
        tmp_dir = path_to_repo / "offline" / ".tmp"
        if not tmp_dir.exists():
            if verbose:
                print(f"mkdir {tmp_dir.relative_to(self.root_dir)}")
            tmp_dir.mkdir()

        for pattern in internal.OFFLINE_SOURCE_FILES:
            for path in path_to_repo.glob(pattern):
                if not path.is_file():
                    continue
                copy2(
                    path.relative_to(self.root_dir),
                    tmp_dir.relative_to(self.root_dir),
                    verbose=verbose,
                )

        copy2(
            (path_to_repo / "offline" / "Makefile").relative_to(self.root_dir),
            tmp_dir.relative_to(self.root_dir),
            verbose=verbose,
        )

        copy2(
            (path_to_repo / "offline" / "parallel_cable").relative_to(self.root_dir),
            tmp_dir.relative_to(self.root_dir),
            verbose=verbose,
        )

        copy2(
            (path_to_repo / "offline" / "serial_cable").relative_to(self.root_dir),
            tmp_dir.relative_to(self.root_dir),
            verbose=verbose,
        )

    def run_build(self, modules: list[str], verbose=False):
        """Runs CABLE build scripts."""

        path_to_repo = self.root_dir / internal.SRC_DIR / self.name
        tmp_dir = path_to_repo / "offline" / ".tmp"

        with chdir(tmp_dir), self.modules_handler.load(modules, verbose=verbose):
            env = os.environ.copy()
            env["NCDIR"] = f"{env['NETCDF_ROOT']}/lib/Intel"
            env["NCMOD"] = f"{env['NETCDF_ROOT']}/include/Intel"
            env["CFLAGS"] = "-O2 -fp-model precise"
            env["LDFLAGS"] = f"-L{env['NETCDF_ROOT']}/lib/Intel -O0"
            env["LD"] = "-lnetcdf -lnetcdff"
            env["FC"] = "mpif90" if internal.MPI else "ifort"

            self.subprocess_handler.run_cmd(
                "make -f Makefile", env=env, verbose=verbose
            )
            self.subprocess_handler.run_cmd(
                f"./{'parallel_cable' if internal.MPI else 'serial_cable'} \"{env['FC']}\" "
                f"\"{env['CFLAGS']}\" \"{env['LDFLAGS']}\" \"{env['LD']}\" \"{env['NCMOD']}\"",
                env=env,
                verbose=verbose,
            )

    def post_build(self, verbose=False):
        """Runs CABLE post-build steps."""

        path_to_repo = self.root_dir / internal.SRC_DIR / self.name
        tmp_dir = path_to_repo / "offline" / ".tmp"

        rename(
            (tmp_dir / internal.CABLE_EXE).relative_to(self.root_dir),
            (path_to_repo / "offline" / internal.CABLE_EXE).relative_to(self.root_dir),
            verbose=verbose,
        )


def remove_module_lines(file_path: Path) -> None:
    """Remove lines from `file_path` that call the environment modules package."""
    with file_path.open("r", encoding="utf-8") as file:
        contents = file.read()
    with file_path.open("w", encoding="utf-8") as file:
        for line in contents.splitlines(True):
            cmds = shlex.split(line, comments=True)
            if "module" not in cmds:
                file.write(line)
