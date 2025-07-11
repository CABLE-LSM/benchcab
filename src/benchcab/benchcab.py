# Copyright 2022 ACCESS-NRI and contributors. See the top-level COPYRIGHT file for details.
# SPDX-License-Identifier: Apache-2.0

"""Contains the benchcab application class."""

import grp
import logging
import os
import sys
from pathlib import Path
from subprocess import CalledProcessError
from typing import Optional

import benchcab.utils.meorg as bm
from benchcab import fluxsite, internal, spatial
from benchcab.comparison import run_comparisons, run_comparisons_in_parallel
from benchcab.config import read_config
from benchcab.coverage import (
    get_coverage_tasks_default,
    run_coverage_tasks,
    run_coverages_in_parallel,
)
from benchcab.environment_modules import EnvironmentModules, EnvironmentModulesInterface
from benchcab.internal import get_met_forcing_file_names
from benchcab.model import Model
from benchcab.utils import is_verbose, task_summary
from benchcab.utils.fs import mkdir, next_path
from benchcab.utils.pbs import render_job_script
from benchcab.utils.repo import create_repo
from benchcab.utils.subprocess import SubprocessWrapper, SubprocessWrapperInterface
from benchcab.workdir import (
    clean_realisation_files,
    clean_submission_files,
    setup_fluxsite_directory_tree,
    setup_spatial_directory_tree,
)


class Benchcab:
    """A class that represents the `benchcab` application."""

    subprocess_handler: SubprocessWrapperInterface = SubprocessWrapper()
    modules_handler: EnvironmentModulesInterface = EnvironmentModules()

    def __init__(
        self,
        benchcab_exe_path: Optional[Path],
        validate_env: bool = True,
    ) -> None:
        """Constructor.

        Parameters
        ----------
        benchcab_exe_path : Optional[Path]
            Path to the executable.
        validate_env : bool, optional
            Validate the environment, by default True

        """
        self.benchcab_exe_path = benchcab_exe_path
        self.validate_env = validate_env

        self._config: Optional[dict] = None
        self._models: list[Model] = []
        self._fluxsite_tasks: list[fluxsite.FluxsiteTask] = []
        self._spatial_tasks: list[spatial.SpatialTask] = []

        # Get the logger object
        self._logger: Optional[logging.Logger] = None
        self._set_environment()

    def set_logger(self, logger: logging.Logger):
        """Set logger."""
        self._logger = logger

    def _get_logger(self) -> logging.Logger:
        if self._logger is None:
            msg = "Logger uninitialised."
            raise RuntimeError(msg)
        return self._logger

    def _set_environment(self):
        """Sets environment variables on current user environment."""
        # Prioritize system binaries over externally set $PATHs (#220)
        os.environ["PATH"] = f"{':'.join(internal.SYSTEM_PATHS)}:{os.environ['PATH']}"

    def _validate_environment(self, project: str, modules: list):
        """Performs checks on current user environment."""
        logger = self._get_logger()
        if not self.validate_env:
            return

        if "gadi.nci" not in internal.NODENAME:
            logger.error("benchcab is currently implemented only on Gadi")
            sys.exit(1)

        namelist_dir = Path(internal.NAMELIST_DIR)
        if not namelist_dir.exists():
            logger.error(
                "Cannot find 'namelists' directory in current working directory"
            )
            sys.exit(1)

        if project is None:
            msg = """Couldn't resolve project: check 'project' in config.yaml
                and/or $PROJECT set in ~/.config/gadi-login.conf
                """
            raise AttributeError(msg)

        required_groups = set([project, "ks32", "hh5"])
        groups = [grp.getgrgid(gid).gr_name for gid in os.getgroups()]
        if not required_groups.issubset(groups):
            msg = (
                f"""Error: user does not have the required group permissions.,
                The required groups are:,
                {", ".join(required_groups)}""",
            )
            raise PermissionError(msg)

        for modname in modules:
            if not self.modules_handler.module_is_avail(modname):
                logger.error(f"Module ({modname}) is not available.")
                sys.exit(1)

        system_paths = os.getenv("PATH").split(":")[: len(internal.SYSTEM_PATHS)]
        if set(system_paths) != set(internal.SYSTEM_PATHS):
            msg = f"""Error: System paths are not prioritized over user-defined paths
                    Currently set as: {system_paths}
                    The required system paths are: {internal.SYSTEM_PATHS}
            """
            raise EnvironmentError(msg)

        all_site_ids = set(
            internal.MEORG_EXPERIMENTS["five-site-test"]
            + internal.MEORG_EXPERIMENTS["forty-two-site-test"]
        )
        for site_id in all_site_ids:
            paths = list(internal.MET_DIR.glob(f"{site_id}*"))
            if not paths:
                logger.error(f"Failed to infer met file for site id '{site_id}' in ")
                logger.error(f"{internal.MET_DIR}.")

                sys.exit(1)
            if len(paths) > 1:
                logger.error(
                    f"Multiple paths infered for site id: '{site_id}' in {internal.MET_DIR}."
                )
                sys.exit(1)

    def _get_config(self, config_path: str) -> dict:
        if not self._config:
            self._config = read_config(config_path)
        return self._config

    def _get_models(self, config: dict) -> list[Model]:
        if not self._models:
            for id, sub_config in enumerate(config["realisations"]):
                repo = create_repo(
                    spec=sub_config.pop("repo"),
                    path=internal.SRC_DIR
                    / (sub_config["name"] if sub_config["name"] else Path()),
                )
                self._models.append(Model(repo=repo, model_id=id, **sub_config))
        return self._models

    def _fluxsite_show_task_composition(self, config: dict) -> str:
        n_models = len(self._get_models(config))
        n_sites = len(get_met_forcing_file_names(config["fluxsite"]["experiment"]))
        n_science_configurations = len(config["science_configurations"])
        return (
            f"models: {n_models}, "
            f"sites: {n_sites}, "
            f"science configurations: {n_science_configurations}"
        )

    def _get_fluxsite_tasks(self, config: dict) -> list[fluxsite.FluxsiteTask]:
        if not self._fluxsite_tasks:
            self._fluxsite_tasks = fluxsite.get_fluxsite_tasks(
                models=self._get_models(config),
                science_configurations=config["science_configurations"],
                fluxsite_forcing_file_names=get_met_forcing_file_names(
                    config["fluxsite"]["experiment"]
                ),
            )
        return self._fluxsite_tasks

    def _get_spatial_tasks(self, config) -> list[spatial.SpatialTask]:
        if not self._spatial_tasks:
            self._spatial_tasks = spatial.get_spatial_tasks(
                models=self._get_models(config),
                met_forcings=config["spatial"]["met_forcings"],
                science_configurations=config["science_configurations"],
                payu_args=config["spatial"]["payu"]["args"],
            )
        return self._spatial_tasks

    def validate_config(self, config_path: str):
        """Endpoint for `benchcab validate_config`."""
        _ = self._get_config(config_path)

    def fluxsite_submit_job(self, config_path: str, skip: list[str]) -> None:
        """Submits the PBS job script step in the fluxsite test workflow."""
        logger = self._get_logger()
        config = self._get_config(config_path)
        self._validate_environment(project=config["project"], modules=config["modules"])
        if self.benchcab_exe_path is None:
            msg = "Path to benchcab executable is undefined."
            raise RuntimeError(msg)

        job_script_path = Path(internal.QSUB_FNAME)
        logger.info("Creating PBS job script to run fluxsite tasks on compute nodes")

        logger.info(f"job_script_path = {job_script_path}")

        with job_script_path.open("w", encoding="utf-8") as file:
            contents = render_job_script(
                project=config["project"],
                config_path=config_path,
                pbs_config=config["fluxsite"]["pbs"],
                skip_bitwise_cmp="fluxsite-bitwise-cmp" in skip,
                skip_codecov="gen_codecov" in skip or not config["codecov"],
                verbose=is_verbose(),
                benchcab_path=str(self.benchcab_exe_path),
            )
            file.write(contents)

        try:
            proc = self.subprocess_handler.run_cmd(
                f"qsub {job_script_path}",
                capture_output=True,
            )
        except CalledProcessError as exc:
            logger.error("when submitting job to NCI queue, details to follow")
            logger.error(exc.output)
            raise

        # Get the job ID
        job_id = proc.stdout.strip()

        logger.info(f"PBS job submitted: {job_id}")
        logger.info("CABLE log file for each task is written to:")
        logger.info(f"{internal.FLUXSITE_DIRS['LOG']}/<task_name>_log.txt")
        logger.info("The CABLE standard output for each task is written to:")
        logger.info(f"{internal.FLUXSITE_DIRS['TASKS']}/<task_name>/out.txt")
        logger.info("The NetCDF output for each task is written to:")
        logger.info(f"{internal.FLUXSITE_DIRS['OUTPUT']}/<task_name>_out.nc")

        # Upload to meorg by default
        bm.do_meorg(
            config,
            upload_dir=internal.FLUXSITE_DIRS["OUTPUT"],
            benchcab_bin=str(self.benchcab_exe_path),
            benchcab_job_id=job_id,
        )

    def gen_codecov(self, config_path: str):
        """Endpoint for `benchcab codecov`."""
        logger = self._get_logger()
        config = self._get_config(config_path)
        self._validate_environment(project=config["project"], modules=config["modules"])

        coverage_tasks = get_coverage_tasks_default(
            models=self._get_models(config=config)
        )

        if not config["codecov"]:
            msg = """`config.yaml` should have set `codecov: true` before building and
            running `gen_codecov`."""
            raise ValueError(msg)

        logger.info("Running coverage tasks...")
        if config["fluxsite"]["multiprocess"]:
            ncpus = config["fluxsite"]["pbs"]["ncpus"]
            run_coverages_in_parallel(coverage_tasks, n_processes=ncpus)
        else:
            run_coverage_tasks(coverage_tasks)
        logger.info("Successfully ran coverage tasks")

    def checkout(self, config_path: str):
        """Endpoint for `benchcab checkout`."""
        logger = self._get_logger()
        config = self._get_config(config_path)
        self._validate_environment(project=config["project"], modules=config["modules"])

        mkdir(internal.SRC_DIR, exist_ok=True)

        logger.info("Checking out repositories...")
        rev_number_log = ""

        for model in self._get_models(config):
            try:
                model.repo.checkout()
            except Exception:
                msg = "Try using `benchcab clean realisations` first"
                logger.error(
                    "Model checkout failed, probably due to existing realisation name"
                )
                raise FileExistsError(msg)
            rev_number_log += f"{model.name}: {model.repo.get_revision()}\n"

        rev_number_log_path = next_path("rev_number-*.log")
        logger.info(f"Writing revision number info to {rev_number_log_path}")
        with rev_number_log_path.open("w", encoding="utf-8") as file:
            file.write(rev_number_log)

    def build(self, config_path: str, mpi=False):
        """Endpoint for `benchcab build`."""
        logger = self._get_logger()
        config = self._get_config(config_path)
        self._validate_environment(project=config["project"], modules=config["modules"])

        for repo in self._get_models(config):
            if repo.build_script:

                logger.info("Compiling CABLE using custom build script for")
                logger.info(f"realisation {repo.name}")
                repo.custom_build(modules=config["modules"])

            else:
                build_mode = "serial and MPI" if mpi else "serial"
                logger.info(
                    f"Compiling CABLE {build_mode} for realisation {repo.name}..."
                )
                repo.build(
                    modules=config["modules"],
                    mpi=mpi,
                    coverage=config["codecov"],
                )
            logger.info(f"Successfully compiled CABLE for realisation {repo.name}")

    def fluxsite_setup_work_directory(self, config_path: str):
        """Endpoint for `benchcab fluxsite-setup-work-dir`."""
        logger = self._get_logger()
        config = self._get_config(config_path)
        self._validate_environment(project=config["project"], modules=config["modules"])

        logger.info("Setting up run directory tree for fluxsite tests...")
        setup_fluxsite_directory_tree()
        logger.info("Setting up tasks...")
        for task in self._get_fluxsite_tasks(config):
            task.setup_task()
        logger.info("Successfully setup fluxsite tasks")

    def fluxsite_run_tasks(self, config_path: str):
        """Endpoint for `benchcab fluxsite-run-tasks`."""
        logger = self._get_logger()
        config = self._get_config(config_path)
        self._validate_environment(project=config["project"], modules=config["modules"])
        tasks = self._get_fluxsite_tasks(config)

        logger.info("Running fluxsite tasks...")
        logger.info(
            f"tasks: {len(tasks)} ({self._fluxsite_show_task_composition(config)})"
        )
        if config["fluxsite"]["multiprocess"]:
            ncpus = config["fluxsite"]["pbs"]["ncpus"]
            fluxsite.run_tasks_in_parallel(tasks, n_processes=ncpus)
        else:
            fluxsite.run_tasks(tasks)

        _, n_success, n_failed, _ = task_summary(tasks)
        logger.info(f"{n_failed} failed, {n_success} passed")

    def fluxsite_bitwise_cmp(self, config_path: str):
        """Endpoint for `benchcab fluxsite-bitwise-cmp`."""
        logger = self._get_logger()
        config = self._get_config(config_path)
        self._validate_environment(project=config["project"], modules=config["modules"])

        if not self.modules_handler.module_is_loaded("nccmp/1.8.5.0"):
            self.modules_handler.module_load(
                "nccmp/1.8.5.0"
            )  # use `nccmp -df` for bitwise comparisons

        comparisons = fluxsite.get_fluxsite_comparisons(
            self._get_fluxsite_tasks(config)
        )

        logger.info("Running comparison tasks...")
        logger.info(
            f"tasks: {len(comparisons)} ({self._fluxsite_show_task_composition(config)})"
        )
        if config["fluxsite"]["multiprocess"]:
            ncpus = config["fluxsite"]["pbs"]["ncpus"]
            run_comparisons_in_parallel(comparisons, n_processes=ncpus)
        else:
            run_comparisons(comparisons)

        _, n_success, n_failed, _ = task_summary(comparisons)
        logger.info(f"{n_failed} failed, {n_success} passed")

    def fluxsite(self, config_path: str, no_submit: bool, skip: list[str]):
        """Endpoint for `benchcab fluxsite`."""
        self.checkout(config_path)
        self.build(config_path)
        self.fluxsite_setup_work_directory(config_path)
        if no_submit:
            self.fluxsite_run_tasks(config_path)
            if "fluxsite-bitwise-cmp" not in skip:
                self.fluxsite_bitwise_cmp(config_path)
            if "codecov" not in skip:
                self.gen_codecov(config_path)
        else:
            self.fluxsite_submit_job(config_path, skip)

    def clean(self, config_path: str, clean_option: str):
        """Endpoint for `benchcab clean`."""
        if clean_option in ["all", "realisations"]:
            clean_realisation_files()
        if clean_option in ["all", "submissions"]:
            clean_submission_files()

    def spatial_setup_work_directory(self, config_path: str):
        """Endpoint for `benchcab spatial-setup-work-dir`."""
        logger = self._get_logger()
        config = self._get_config(config_path)
        self._validate_environment(project=config["project"], modules=config["modules"])

        logger.info("Setting up run directory tree for spatial tests...")
        setup_spatial_directory_tree()
        logger.info("Setting up tasks...")
        try:
            payu_config = config["spatial"]["payu"]["config"]
        except KeyError:
            payu_config = None
        for task in self._get_spatial_tasks(config):
            task.setup_task(payu_config=payu_config)
        logger.info("Successfully setup spatial tasks")

    def spatial_run_tasks(self, config_path: str):
        """Endpoint for `benchcab spatial-run-tasks`."""
        logger = self._get_logger()
        config = self._get_config(config_path)
        self._validate_environment(project=config["project"], modules=config["modules"])

        logger.info("Running spatial tasks...")
        spatial.run_tasks(tasks=self._get_spatial_tasks(config))
        logger.info("Successfully dispatched payu jobs")

    def spatial(self, config_path: str, skip: list):
        """Endpoint for `benchcab spatial`."""
        self.checkout(config_path)
        self.build(config_path, mpi=True)
        self.spatial_setup_work_directory(config_path)
        self.spatial_run_tasks(config_path)

    def run(self, config_path: str, skip: list[str]):
        """Endpoint for `benchcab run`."""
        self.checkout(config_path)
        self.build(config_path, mpi=True)
        self.fluxsite_setup_work_directory(config_path)
        self.spatial_setup_work_directory(config_path)
        self.fluxsite_submit_job(config_path, skip)
        self.spatial_run_tasks(config_path)
