"""A module containing functions and data structures for running fluxsite tasks."""

import multiprocessing
import operator
import shutil
import sys
from pathlib import Path
from subprocess import CalledProcessError
from typing import Any, Dict, TypeVar

import f90nml
import flatdict
import netCDF4

from benchcab import __version__, internal
from benchcab.comparison import ComparisonTask
from benchcab.model import Model
from benchcab.utils.fs import chdir, mkdir
from benchcab.utils.subprocess import SubprocessWrapper, SubprocessWrapperInterface

# fmt: off
# ======================================================
# Copyright (c) 2017 - 2022 Samuel Colvin and other contributors
# from https://github.com/pydantic/pydantic/blob/fd2991fe6a73819b48c906e3c3274e8e47d0f761/pydantic/utils.py#L200

KeyType = TypeVar('KeyType')


def deep_update(mapping: Dict[KeyType, Any], *updating_mappings: Dict[KeyType, Any]) -> Dict[KeyType, Any]:
    updated_mapping = mapping.copy()
    for updating_mapping in updating_mappings:
        for k, v in updating_mapping.items():
            if k in updated_mapping and isinstance(updated_mapping[k], dict) and isinstance(v, dict):
                updated_mapping[k] = deep_update(updated_mapping[k], v)
            else:
                updated_mapping[k] = v
    return updated_mapping

# ======================================================
# fmt: on


def deep_del(
    mapping: Dict[KeyType, Any], *updating_mappings: Dict[KeyType, Any]
) -> Dict[KeyType, Any]:
    """Deletes all key-value 'leaf nodes' in `mapping` specified by `updating_mappings`."""
    updated_mapping = mapping.copy()
    for updating_mapping in updating_mappings:
        for key, value in updating_mapping.items():
            if isinstance(updated_mapping[key], dict) and isinstance(value, dict):
                updated_mapping[key] = deep_del(updated_mapping[key], value)
            else:
                del updated_mapping[key]
    return updated_mapping


def patch_namelist(nml_path: Path, patch: dict):
    """Writes a namelist patch specified by `patch` to `nml_path`.

    The `patch` dictionary must comply with the `f90nml` api.
    """
    if not nml_path.exists():
        f90nml.write(patch, nml_path)
        return

    nml = f90nml.read(nml_path)
    f90nml.write(deep_update(nml, patch), nml_path, force=True)


def patch_remove_namelist(nml_path: Path, patch_remove: dict):
    """Removes a subset of namelist parameters specified by `patch_remove` from `nml_path`.

    The `patch_remove` dictionary must comply with the `f90nml` api.
    """
    nml = f90nml.read(nml_path)
    try:
        f90nml.write(deep_del(nml, patch_remove), nml_path, force=True)
    except KeyError as exc:
        msg = f"Namelist parameters specified in `patch_remove` do not exist in {nml_path.name}."
        raise KeyError(msg) from exc


f90_logical_repr = {True: ".true.", False: ".false."}


class CableError(Exception):
    """Custom exception class for CABLE errors."""


class Task:
    """A class used to represent a single fluxsite task."""

    root_dir: Path = internal.CWD
    subprocess_handler: SubprocessWrapperInterface = SubprocessWrapper()

    def __init__(
        self,
        repo: Model,
        met_forcing_file: str,
        sci_conf_id: int,
        sci_config: dict,
    ) -> None:
        self.repo = repo
        self.met_forcing_file = met_forcing_file
        self.sci_conf_id = sci_conf_id
        self.sci_config = sci_config

    def get_task_name(self) -> str:
        """Returns the file name convention used for this task."""
        met_forcing_base_filename = self.met_forcing_file.split(".")[0]
        return f"{met_forcing_base_filename}_R{self.repo.repo_id}_S{self.sci_conf_id}"

    def get_output_filename(self) -> str:
        """Returns the file name convention used for the netcdf output file."""
        return f"{self.get_task_name()}_out.nc"

    def get_log_filename(self) -> str:
        """Returns the file name convention used for the log file."""
        return f"{self.get_task_name()}_log.txt"

    def setup_task(self, verbose=False):
        """Does all file manipulations to run cable in the task directory.

        These include:
        1. creating the task directory if it does not exist.
        2. cleaning output, namelist, log files and cable executables if they exist
        3. copying namelist files (cable.nml, pft_params.nml and cable_soil_parm.nml)
        into the `runs/fluxsite/tasks/<task_name>` directory.
        4. copying the cable executable from the source directory
        5. make appropriate adjustments to namelist files
        6. apply a branch patch if specified
        """
        if verbose:
            print(f"Setting up task: {self.get_task_name()}")

        mkdir(
            internal.FLUXSITE_DIRS["TASKS"] / self.get_task_name(),
            verbose=verbose,
            parents=True,
            exist_ok=True,
        )

        self.clean_task(verbose=verbose)
        self.fetch_files(verbose=verbose)

        nml_path = (
            self.root_dir
            / internal.FLUXSITE_DIRS["TASKS"]
            / self.get_task_name()
            / internal.CABLE_NML
        )

        if verbose:
            print(f"  Adding base configurations to CABLE namelist file {nml_path}")
        patch_namelist(
            nml_path,
            {
                "cable": {
                    "filename": {
                        "met": str(internal.MET_DIR / self.met_forcing_file),
                        "out": str(
                            self.root_dir
                            / internal.FLUXSITE_DIRS["OUTPUT"]
                            / self.get_output_filename()
                        ),
                        "log": str(
                            self.root_dir
                            / internal.FLUXSITE_DIRS["LOG"]
                            / self.get_log_filename()
                        ),
                        "restart_out": " ",
                        "type": str(self.root_dir / internal.GRID_FILE),
                    },
                    "output": {
                        "restart": False,
                    },
                    "fixedCO2": internal.CABLE_FIXED_CO2_CONC,
                    "casafile": {
                        "phen": str(self.root_dir / internal.PHEN_FILE),
                        "cnpbiome": str(self.root_dir / internal.CNPBIOME_FILE),
                    },
                    "spinup": False,
                }
            },
        )

        if verbose:
            print(f"  Adding science configurations to CABLE namelist file {nml_path}")
        patch_namelist(nml_path, self.sci_config)

        if self.repo.patch:
            if verbose:
                print(
                    f"  Adding branch specific configurations to CABLE namelist file {nml_path}"
                )
            patch_namelist(nml_path, self.repo.patch)

        if self.repo.patch_remove:
            if verbose:
                print(
                    f"  Removing branch specific configurations from CABLE namelist file {nml_path}"
                )
            patch_remove_namelist(nml_path, self.repo.patch_remove)

    def clean_task(self, verbose=False):
        """Cleans output files, namelist files, log files and cable executables if they exist."""
        if verbose:
            print("  Cleaning task")

        task_dir = (
            self.root_dir / internal.FLUXSITE_DIRS["TASKS"] / self.get_task_name()
        )

        cable_exe = task_dir / internal.CABLE_EXE
        if cable_exe.exists():
            cable_exe.unlink()

        cable_nml = task_dir / internal.CABLE_NML
        if cable_nml.exists():
            cable_nml.unlink()

        cable_vegetation_nml = task_dir / internal.CABLE_VEGETATION_NML
        if cable_vegetation_nml.exists():
            cable_vegetation_nml.unlink()

        cable_soil_nml = task_dir / internal.CABLE_SOIL_NML
        if cable_soil_nml.exists():
            cable_soil_nml.unlink()

        output_file = (
            self.root_dir
            / internal.FLUXSITE_DIRS["OUTPUT"]
            / self.get_output_filename()
        )
        if output_file.exists():
            output_file.unlink()

        log_file = (
            self.root_dir / internal.FLUXSITE_DIRS["LOG"] / self.get_log_filename()
        )
        if log_file.exists():
            log_file.unlink()

        return self

    def fetch_files(self, verbose=False):
        """Retrieves all files necessary to run cable in the task directory.

        Namely:
        - copies contents of 'namelists' directory to 'runs/fluxsite/tasks/<task_name>' directory.
        - copies cable executable from source to 'runs/fluxsite/tasks/<task_name>' directory.
        """
        task_dir = (
            self.root_dir / internal.FLUXSITE_DIRS["TASKS"] / self.get_task_name()
        )

        if verbose:
            print(
                f"  Copying namelist files from {self.root_dir / internal.NAMELIST_DIR} "
                f"to {task_dir}"
            )

        shutil.copytree(
            self.root_dir / internal.NAMELIST_DIR, task_dir, dirs_exist_ok=True
        )

        exe_src = (
            self.root_dir
            / internal.SRC_DIR
            / self.repo.name
            / "offline"
            / internal.CABLE_EXE
        )
        exe_dest = task_dir / internal.CABLE_EXE

        if verbose:
            print(f"  Copying CABLE executable from {exe_src} to {exe_dest}")

        shutil.copy(exe_src, exe_dest)

        return self

    def run(self, verbose=False):
        """Runs a single fluxsite task."""
        task_name = self.get_task_name()
        task_dir = self.root_dir / internal.FLUXSITE_DIRS["TASKS"] / task_name
        if verbose:
            print(
                f"Running task {task_name}... CABLE standard output "
                f"saved in {task_dir / internal.CABLE_STDOUT_FILENAME}"
            )
        try:
            self.run_cable(verbose=verbose)
            self.add_provenance_info(verbose=verbose)
        except CableError:
            # Note: here we suppress CABLE specific errors so that `benchcab`
            # exits successfully. This then allows us to run bitwise comparisons
            # checks on whatever output files were produced without having any
            # sort of task dependence between CABLE tasks and comparison tasks.
            pass
        sys.stdout.flush()

    def run_cable(self, verbose=False):
        """Run the CABLE executable for the given task.

        Raises `CableError` when CABLE returns a non-zero exit code.
        """
        task_name = self.get_task_name()
        task_dir = self.root_dir / internal.FLUXSITE_DIRS["TASKS"] / task_name
        stdout_path = task_dir / internal.CABLE_STDOUT_FILENAME

        try:
            with chdir(task_dir):
                self.subprocess_handler.run_cmd(
                    f"./{internal.CABLE_EXE} {internal.CABLE_NML}",
                    output_file=stdout_path,
                    verbose=verbose,
                )
        except CalledProcessError as exc:
            print(f"Error: CABLE returned an error for task {task_name}")
            raise CableError from exc

    def add_provenance_info(self, verbose=False):
        """Adds provenance information to global attributes of netcdf output file.

        Attributes include branch url, branch revision number and key value pairs in
        the namelist file used to run cable.
        """
        nc_output_path = (
            self.root_dir
            / internal.FLUXSITE_DIRS["OUTPUT"]
            / self.get_output_filename()
        )
        nml = f90nml.read(
            self.root_dir
            / internal.FLUXSITE_DIRS["TASKS"]
            / self.get_task_name()
            / internal.CABLE_NML
        )
        if verbose:
            print(f"Adding attributes to output file: {nc_output_path}")
        with netCDF4.Dataset(nc_output_path, "r+") as nc_output:
            nc_output.setncatts(
                {
                    **{
                        key: f90_logical_repr[val] if isinstance(val, bool) else val
                        for key, val in flatdict.FlatDict(
                            nml["cable"], delimiter="%"
                        ).items()
                    },
                    **{
                        "cable_branch": self.repo.svn_info_show_item("url"),
                        "svn_revision_number": self.repo.svn_info_show_item("revision"),
                        "benchcab_version": __version__,
                    },
                }
            )


def get_fluxsite_tasks(
    repos: list[Model],
    science_configurations: list[dict],
    fluxsite_forcing_file_names: list[str],
) -> list[Task]:
    """Returns a list of fluxsite tasks to run."""
    tasks = [
        Task(
            repo=repo,
            met_forcing_file=file_name,
            sci_conf_id=sci_conf_id,
            sci_config=sci_config,
        )
        for repo in repos
        for file_name in fluxsite_forcing_file_names
        for sci_conf_id, sci_config in enumerate(science_configurations)
    ]
    return tasks


def run_tasks(tasks: list[Task], verbose=False):
    """Runs tasks in `tasks` serially."""
    for task in tasks:
        task.run(verbose=verbose)


def run_tasks_in_parallel(
    tasks: list[Task], n_processes=internal.FLUXSITE_DEFAULT_PBS["ncpus"], verbose=False
):
    """Runs tasks in `tasks` in parallel across multiple processes."""
    run_task = operator.methodcaller("run", verbose=verbose)
    with multiprocessing.Pool(n_processes) as pool:
        pool.map(run_task, tasks, chunksize=1)


def get_fluxsite_comparisons(
    tasks: list[Task], root_dir=internal.CWD
) -> list[ComparisonTask]:
    """Returns a list of `ComparisonTask` objects to run comparisons with.

    Pairs should be matching in science configurations and meteorological
    forcing, but differ in realisations. When multiple realisations are
    specified, return all pair wise combinations between all realisations.
    """
    output_dir = root_dir / internal.FLUXSITE_DIRS["OUTPUT"]
    return [
        ComparisonTask(
            files=(
                output_dir / task_a.get_output_filename(),
                output_dir / task_b.get_output_filename(),
            ),
            task_name=get_comparison_name(
                task_a.repo, task_b.repo, task_a.met_forcing_file, task_a.sci_conf_id
            ),
        )
        for task_a in tasks
        for task_b in tasks
        if task_a.met_forcing_file == task_b.met_forcing_file
        and task_a.sci_conf_id == task_b.sci_conf_id
        and task_a.repo.repo_id < task_b.repo.repo_id
        # TODO(Sean): Review later - the following code avoids using a double
        # for loop to generate pair wise combinations, however we would have
        # to re-initialize task instances to get access to the output file path
        # for each task. There is probably a better way but should be fine for
        # now...
        # for file_name in fluxsite_forcing_file_names
        # for sci_conf_id in range(len(science_configurations))
        # for branch_id_first, branch_id_second in itertools.combinations(
        #     range(len(realisations)), 2
        # )
    ]


def get_comparison_name(
    repo_a: Model,
    repo_b: Model,
    met_forcing_file: str,
    sci_conf_id: int,
) -> str:
    """Returns the naming convention used for bitwise comparisons."""
    met_forcing_base_filename = met_forcing_file.split(".")[0]
    return (
        f"{met_forcing_base_filename}_S{sci_conf_id}"
        f"_R{repo_a.repo_id}_R{repo_b.repo_id}"
    )
