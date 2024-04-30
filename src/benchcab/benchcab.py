# Copyright 2022 ACCESS-NRI and contributors. See the top-level COPYRIGHT file for details.
# SPDX-License-Identifier: Apache-2.0

"""Contains the benchcab application class."""

import grp
import json
import logging
import os
import sys
from pathlib import Path
from subprocess import CalledProcessError
from typing import Optional

from benchcab import fluxsite, internal, spatial
from benchcab.comparison import run_comparisons, run_comparisons_in_parallel
from benchcab.config import read_config
from benchcab.environment_modules import EnvironmentModules, EnvironmentModulesInterface
from benchcab.internal import get_met_forcing_file_names
from benchcab.model import Model
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


def _get_spack_exe():
    return Path(os.environ["SPACK_ROOT"]) / "bin" / "spack"


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

    def _spack_enabled(self) -> bool:
        return Path("spack.yaml").is_file()

    def _get_models_via_spack(self, config: dict) -> list[Model]:
        logger = self._get_logger()
        models: list[Model] = []
        spack_path = _get_spack_exe()
        self.subprocess_handler.run_cmd(
            f"{spack_path} concretize --force && {spack_path} install",
            env={**os.environ, "SPACK_ENV": "."},
        )
        for model_spec in config["model_specs"]:
            proc = self.subprocess_handler.run_cmd(
                f"{spack_path} find --json {model_spec['spec']}",
                capture_output=True,
                env={**os.environ, "SPACK_ENV": "."},
            )
            data = json.loads(proc.stdout)
            for package_data in data:
                id = len(models)
                proc = self.subprocess_handler.run_cmd(
                    f"{spack_path} find --format '{{name}} {{version}} {{hash:10}} {{prefix}}' /{package_data['hash']}",
                    capture_output=True,
                )
                name, version, hash, prefix = proc.stdout.strip().split(" ")
                model = Model(
                    install_dir_absolute=os.path.join(prefix, "bin"),
                    model_id=id,
                    patch=model_spec["patch"],
                    patch_remove=model_spec["patch_remove"],
                )
                model.add_metadata(
                    {
                        "model_id": str(id),
                        "spack-model-name": name,
                        "spack-model-version": version,
                        "spack-model-hash": hash,
                    }
                )
                models.append(model)

        logger.info(f"Model realisations found: {len(models)}")
        for m in models:
            data = m.get_metadata()
            logger.info(
                f"  R{m.model_id} : {data['spack-model-name']}@{data['spack-model-version']} (spack-model-hash={data['spack-model-hash']})"
            )

        return models

    def _get_models(self, config: dict) -> list[Model]:
        if self._models:
            return self._models

        if self._spack_enabled():
            self._models = self._get_models_via_spack(config)
            return self._models

        for id, sub_config in enumerate(config["realisations"]):
            repo = create_repo(
                spec=sub_config.pop("repo"),
                path=internal.SRC_DIR
                / (sub_config["name"] if sub_config["name"] else Path()),
            )
            model = Model(
                repo=repo, name=repo.get_branch_name(), model_id=id, **sub_config
            )
            model.add_metadata(
                {
                    "model_id": str(id),
                    "branch": repo.get_branch_name(),
                    "revision": repo.get_revision(),
                }
            )
            self._models.append(model)
        return self._models

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
                modules=config["modules"],
                pbs_config=config["fluxsite"]["pbs"],
                skip_bitwise_cmp="fluxsite-bitwise-cmp" in skip,
                benchcab_path=str(self.benchcab_exe_path),
            )
            file.write(contents)

        try:
            proc = self.subprocess_handler.run_cmd(
                "qsub"
                + (
                    f" -v SPACK_ROOT={os.environ['SPACK_ROOT']}"
                    if self._spack_enabled()
                    else ""
                )
                + f" {job_script_path}",
                capture_output=True,
            )
        except CalledProcessError as exc:
            logger.error("when submitting job to NCI queue, details to follow")
            logger.error(exc.output)
            raise

        logger.info(f"PBS job submitted: {proc.stdout.strip()}")
        logger.info("CABLE log file for each task is written to:")
        logger.info(f"{internal.FLUXSITE_DIRS['LOG']}/<task_name>_log.txt")
        logger.info("The CABLE standard output for each task is written to:")
        logger.info(f"{internal.FLUXSITE_DIRS['TASKS']}/<task_name>/out.txt")
        logger.info("The NetCDF output for each task is written to:")
        logger.info(f"{internal.FLUXSITE_DIRS['OUTPUT']}/<task_name>_out.nc")

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
                repo.build(modules=config["modules"], mpi=mpi)
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
        if config["fluxsite"]["multiprocess"]:
            ncpus = config["fluxsite"]["pbs"]["ncpus"]
            fluxsite.run_tasks_in_parallel(tasks, n_processes=ncpus)
        else:
            fluxsite.run_tasks(tasks)
        logger.info("Successfully ran fluxsite tasks")

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
        if config["fluxsite"]["multiprocess"]:
            ncpus = config["fluxsite"]["pbs"]["ncpus"]
            run_comparisons_in_parallel(comparisons, n_processes=ncpus)
        else:
            run_comparisons(comparisons)
        logger.info("Successfully ran comparison tasks")

    def fluxsite(self, config_path: str, no_submit: bool, skip: list[str]):
        """Endpoint for `benchcab fluxsite`."""
        if not self._spack_enabled():
            self.checkout(config_path)
            self.build(config_path)
        self.fluxsite_setup_work_directory(config_path)
        if no_submit:
            self.fluxsite_run_tasks(config_path)
            if "fluxsite-bitwise-cmp" not in skip:
                self.fluxsite_bitwise_cmp(config_path)
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
        if not self._spack_enabled():
            self.checkout(config_path)
            self.build(config_path, mpi=True)
        self.spatial_setup_work_directory(config_path)
        self.spatial_run_tasks(config_path)

    def run(self, config_path: str, skip: list[str]):
        """Endpoint for `benchcab run`."""
        if not self._spack_enabled():
            self.checkout(config_path)
            self.build(config_path, mpi=True)
        self.fluxsite_setup_work_directory(config_path)
        self.spatial_setup_work_directory(config_path)
        self.fluxsite_submit_job(config_path, skip)
        self.spatial_run_tasks(config_path)
