# Copyright 2022 ACCESS-NRI and contributors. See the top-level COPYRIGHT file for details.
# SPDX-License-Identifier: Apache-2.0

"""A module containing functions and data structures for running fluxsite tasks."""

import multiprocessing
import operator
import shutil
import sys
from subprocess import CalledProcessError

import f90nml
import flatdict
import netCDF4

from benchcab import __version__, internal
from benchcab.comparison import ComparisonTask
from benchcab.model import Model
from benchcab.utils import get_logger
from benchcab.utils.fs import chdir, mkdir
from benchcab.utils.namelist import patch_namelist, patch_remove_namelist
from benchcab.utils.subprocess import SubprocessWrapper, SubprocessWrapperInterface

f90_logical_repr = {True: ".true.", False: ".false."}


class CableError(Exception):
    """Custom exception class for CABLE errors."""


class FluxsiteTask:
    """A class used to represent a single fluxsite task."""

    subprocess_handler: SubprocessWrapperInterface = SubprocessWrapper()

    def __init__(
        self,
        model: Model,
        met_forcing_file: str,
        sci_conf_id: int,
        sci_config: dict,
    ) -> None:
        """Constructor.

        Parameters
        ----------
        model : Model
            Model.
        met_forcing_file : str
            Met forcing file.
        sci_conf_id : int
            Science configuration ID.
        sci_config : dict
            Science configuration.

        """
        self.model = model
        self.met_forcing_file = met_forcing_file
        self.sci_conf_id = sci_conf_id
        self.sci_config = sci_config
        self.logger = get_logger()

    def get_task_name(self) -> str:
        """Returns the file name convention used for this task."""
        met_forcing_base_filename = self.met_forcing_file.split(".")[0]
        return f"{met_forcing_base_filename}_R{self.model.model_id}_S{self.sci_conf_id}"

    def get_output_filename(self) -> str:
        """Returns the file name convention used for the netcdf output file."""
        return f"{self.get_task_name()}_out.nc"

    def get_log_filename(self) -> str:
        """Returns the file name convention used for the log file."""
        return f"{self.get_task_name()}_log.txt"

    def setup_task(self):
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
        self.logger.debug(f"Setting up task: {self.get_task_name()}")

        mkdir(
            internal.FLUXSITE_DIRS["TASKS"] / self.get_task_name(),
            parents=True,
            exist_ok=True,
        )

        self.clean_task()
        self.fetch_files()

        nml_path = (
            internal.FLUXSITE_DIRS["TASKS"] / self.get_task_name() / internal.CABLE_NML
        )

        self.logger.debug(
            f"  Adding base configurations to CABLE namelist file {nml_path}"
        )
        patch_namelist(
            nml_path,
            {
                "cable": {
                    "filename": {
                        "met": str(internal.MET_DIR / self.met_forcing_file),
                        "out": str(
                            (
                                internal.FLUXSITE_DIRS["OUTPUT"]
                                / self.get_output_filename()
                            ).absolute()
                        ),
                        "log": str(
                            (
                                internal.FLUXSITE_DIRS["LOG"] / self.get_log_filename()
                            ).absolute()
                        ),
                        "restart_out": " ",
                        "type": str(internal.GRID_FILE.absolute()),
                    },
                    "output": {
                        "restart": False,
                    },
                    "fixedCO2": internal.CABLE_FIXED_CO2_CONC,
                    "spinup": False,
                }
            },
        )

        self.logger.debug(
            f"  Adding science configurations to CABLE namelist file {nml_path}"
        )
        patch_namelist(nml_path, self.sci_config)

        if self.model.patch:
            self.logger.debug(
                f"  Adding branch specific configurations to CABLE namelist file {nml_path}"
            )
            patch_namelist(nml_path, self.model.patch)

        if self.model.patch_remove:
            self.logger.debug(
                f"  Removing branch specific configurations from CABLE namelist file {nml_path}"
            )
            patch_remove_namelist(nml_path, self.model.patch_remove)

    def clean_task(self):
        """Cleans output files, namelist files, log files and cable executables if they exist."""
        self.logger.debug("  Cleaning task")

        task_dir = internal.FLUXSITE_DIRS["TASKS"] / self.get_task_name()

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

        output_file = internal.FLUXSITE_DIRS["OUTPUT"] / self.get_output_filename()
        if output_file.exists():
            output_file.unlink()

        log_file = internal.FLUXSITE_DIRS["LOG"] / self.get_log_filename()
        if log_file.exists():
            log_file.unlink()

        return self

    def fetch_files(self):
        """Retrieves all files necessary to run cable in the task directory.

        Namely:
        - copies contents of 'namelists' directory to 'runs/fluxsite/tasks/<task_name>' directory.
        - copies cable executable from source to 'runs/fluxsite/tasks/<task_name>' directory.
        """
        task_dir = internal.FLUXSITE_DIRS["TASKS"] / self.get_task_name()

        self.logger.debug(
            f"  Copying namelist files from {internal.NAMELIST_DIR} to {task_dir}"
        )

        shutil.copytree(internal.NAMELIST_DIR, task_dir, dirs_exist_ok=True)

        exe_src = self.model.get_exe_path()
        exe_dest = task_dir / internal.CABLE_EXE

        self.logger.debug(f"  Copying CABLE executable from {exe_src} to {exe_dest}")

        shutil.copy(exe_src, exe_dest)

        return self

    def run(self):
        """Runs a single fluxsite task."""
        task_name = self.get_task_name()
        task_dir = internal.FLUXSITE_DIRS["TASKS"] / task_name
        self.logger.debug(f"Running task {task_name}... CABLE standard output ")
        self.logger.debug(f"saved in {task_dir / internal.CABLE_STDOUT_FILENAME}")

        try:
            self.run_cable()
            self.add_provenance_info()
        except CableError:
            # Note: here we suppress CABLE specific errors so that `benchcab`
            # exits successfully. This then allows us to run bitwise comparisons
            # checks on whatever output files were produced without having any
            # sort of task dependence between CABLE tasks and comparison tasks.
            pass
        sys.stdout.flush()

    def run_cable(self):
        """Run the CABLE executable for the given task.

        Raises `CableError` when CABLE returns a non-zero exit code.
        """
        task_name = self.get_task_name()
        task_dir = internal.FLUXSITE_DIRS["TASKS"] / task_name
        stdout_path = task_dir / internal.CABLE_STDOUT_FILENAME

        try:
            with chdir(task_dir):
                self.subprocess_handler.run_cmd(
                    f"./{internal.CABLE_EXE} {internal.CABLE_NML}",
                    output_file=stdout_path.relative_to(task_dir),
                )
        except CalledProcessError as exc:
            self.logger.debug(f"Error: CABLE returned an error for task {task_name}")
            raise CableError from exc

    def add_provenance_info(self):
        """Adds provenance information to global attributes of netcdf output file.

        Attributes include branch url, branch revision number and key value pairs in
        the namelist file used to run cable.
        """
        nc_output_path = internal.FLUXSITE_DIRS["OUTPUT"] / self.get_output_filename()
        nml = f90nml.read(
            internal.FLUXSITE_DIRS["TASKS"] / self.get_task_name() / internal.CABLE_NML
        )
        self.logger.debug(f"Adding attributes to output file: {nc_output_path}")
        with netCDF4.Dataset(nc_output_path, "r+") as nc_output:
            nc_output.setncatts(
                {
                    **{
                        key: f90_logical_repr[val] if isinstance(val, bool) else val
                        for key, val in flatdict.FlatDict(
                            nml["cable"], delimiter="%"
                        ).items()
                    },
                    **self.model.get_metadata(),
                    "benchcab_version": __version__,
                }
            )


def get_fluxsite_tasks(
    models: list[Model],
    science_configurations: list[dict],
    fluxsite_forcing_file_names: list[str],
) -> list[FluxsiteTask]:
    """Returns a list of fluxsite tasks to run."""
    tasks = [
        FluxsiteTask(
            model=model,
            met_forcing_file=file_name,
            sci_conf_id=sci_conf_id,
            sci_config=sci_config,
        )
        for model in models
        for file_name in fluxsite_forcing_file_names
        for sci_conf_id, sci_config in enumerate(science_configurations)
    ]
    return tasks


def run_tasks(tasks: list[FluxsiteTask]):
    """Runs tasks in `tasks` serially."""
    for task in tasks:
        task.run()


def run_tasks_in_parallel(
    tasks: list[FluxsiteTask],
    n_processes=internal.FLUXSITE_DEFAULT_PBS["ncpus"],
):
    """Runs tasks in `tasks` in parallel across multiple processes."""
    run_task = operator.methodcaller("run")
    with multiprocessing.Pool(n_processes) as pool:
        pool.map(run_task, tasks, chunksize=1)


def get_fluxsite_comparisons(tasks: list[FluxsiteTask]) -> list[ComparisonTask]:
    """Returns a list of `ComparisonTask` objects to run comparisons with.

    Pairs should be matching in science configurations and meteorological
    forcing, but differ in realisations. When multiple realisations are
    specified, return all pair wise combinations between all realisations.
    """
    output_dir = internal.FLUXSITE_DIRS["OUTPUT"]
    return [
        ComparisonTask(
            files=(
                output_dir / task_a.get_output_filename(),
                output_dir / task_b.get_output_filename(),
            ),
            task_name=get_comparison_name(
                task_a.model, task_b.model, task_a.met_forcing_file, task_a.sci_conf_id
            ),
        )
        for task_a in tasks
        for task_b in tasks
        if task_a.met_forcing_file == task_b.met_forcing_file
        and task_a.sci_conf_id == task_b.sci_conf_id
        and task_a.model.model_id < task_b.model.model_id
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
    model_a: Model,
    model_b: Model,
    met_forcing_file: str,
    sci_conf_id: int,
) -> str:
    """Returns the naming convention used for bitwise comparisons."""
    met_forcing_base_filename = met_forcing_file.split(".")[0]
    return (
        f"{met_forcing_base_filename}_S{sci_conf_id}"
        f"_R{model_a.model_id}_R{model_b.model_id}"
    )
