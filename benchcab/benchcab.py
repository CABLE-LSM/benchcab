# Copyright 2022 ACCESS-NRI and contributors. See the top-level COPYRIGHT file for details.
# SPDX-License-Identifier: Apache-2.0

"""Contains the main program entry point for `benchcab`."""

import sys
import os
import grp
import shutil
from pathlib import Path
from typing import Optional
from subprocess import CalledProcessError

from benchcab import internal
from benchcab.internal import get_met_forcing_file_names
from benchcab.config import read_config
from benchcab.workdir import setup_fluxsite_directory_tree, setup_src_dir
from benchcab.repository import CableRepository
from benchcab.fluxsite import (
    get_fluxsite_tasks,
    get_fluxsite_comparisons,
    run_tasks,
    run_tasks_in_parallel,
    Task,
)
from benchcab.comparison import run_comparisons, run_comparisons_in_parallel
from benchcab.cli import generate_parser
from benchcab.environment_modules import EnvironmentModules, EnvironmentModulesInterface
from benchcab.utils.subprocess import SubprocessWrapper, SubprocessWrapperInterface
from benchcab.utils.pbs import render_job_script
from benchcab.utils.logging import next_path


class Benchcab:
    """A class that represents the `benchcab` application."""

    root_dir: Path = internal.CWD
    subprocess_handler: SubprocessWrapperInterface = SubprocessWrapper()
    modules_handler: EnvironmentModulesInterface = EnvironmentModules()

    def __init__(
        self,
        argv: list[str],
        benchcab_exe_path: Optional[Path],
        config: Optional[dict] = None,
        validate_env: bool = True,
    ) -> None:
        self.args = generate_parser().parse_args(argv[1:] if argv[1:] else ["-h"])
        self.config = config if config else read_config(self.args.config)
        self.repos = [
            CableRepository(**config, repo_id=id)
            for id, config in enumerate(self.config["realisations"])
        ]
        self.tasks: list[Task] = []  # initialise fluxsite tasks lazily
        self.benchcab_exe_path = benchcab_exe_path

        if validate_env:
            self._validate_environment(
                project=self.config["project"], modules=self.config["modules"]
            )

    def _validate_environment(self, project: str, modules: list):
        """Performs checks on current user environment"""

        if "gadi.nci" not in internal.NODENAME:
            print("Error: benchcab is currently implemented only on Gadi")
            sys.exit(1)

        namelist_dir = Path(internal.CWD / internal.NAMELIST_DIR)
        if not namelist_dir.exists():
            print(
                "Error: cannot find 'namelists' directory in current working directory"
            )
            sys.exit(1)

        required_groups = [project, "ks32", "hh5"]
        groups = [grp.getgrgid(gid).gr_name for gid in os.getgroups()]
        if not set(required_groups).issubset(groups):
            print(
                "Error: user does not have the required group permissions.",
                "The required groups are:",
                ", ".join(required_groups),
            )
            sys.exit(1)

        for modname in modules:
            if not self.modules_handler.module_is_avail(modname):
                print(f"Error: module ({modname}) is not available.")
                sys.exit(1)

        all_site_ids = set(
            internal.MEORG_EXPERIMENTS["five-site-test"]
            + internal.MEORG_EXPERIMENTS["forty-two-site-test"]
        )
        for site_id in all_site_ids:
            paths = list(internal.MET_DIR.glob(f"{site_id}*"))
            if not paths:
                print(
                    f"Error: failed to infer met file for site id '{site_id}' in "
                    f"{internal.MET_DIR}."
                )
                sys.exit(1)
            if len(paths) > 1:
                print(
                    f"Error: multiple paths infered for site id: '{site_id}' in {internal.MET_DIR}."
                )
                sys.exit(1)

    def _initialise_tasks(self) -> list[Task]:
        """A helper method that initialises and returns the `tasks` attribute."""
        self.tasks = get_fluxsite_tasks(
            repos=self.repos,
            science_configurations=self.config.get(
                "science_configurations", internal.DEFAULT_SCIENCE_CONFIGURATIONS
            ),
            fluxsite_forcing_file_names=get_met_forcing_file_names(
                self.config["experiment"]
            ),
        )
        return self.tasks

    def fluxsite_submit_job(self) -> None:
        """Submits the PBS job script step in the fluxsite test workflow."""

        if self.benchcab_exe_path is None:
            raise RuntimeError("Path to benchcab executable is undefined.")

        job_script_path = self.root_dir / internal.QSUB_FNAME
        print(
            "Creating PBS job script to run fluxsite tasks on compute "
            f"nodes: {job_script_path.relative_to(self.root_dir)}"
        )
        with job_script_path.open("w", encoding="utf-8") as file:
            contents = render_job_script(
                project=self.config["project"],
                config_path=self.args.config,
                modules=self.config["modules"],
                verbose=self.args.verbose,
                skip_bitwise_cmp="fluxsite-bitwise-cmp" in self.args.skip,
                benchcab_path=str(self.benchcab_exe_path),
                pbs_config=self.config.get("pbs"),
            )
            file.write(contents)

        try:
            proc = self.subprocess_handler.run_cmd(
                f"qsub {job_script_path}",
                capture_output=True,
                verbose=self.args.verbose,
            )
        except CalledProcessError as exc:
            print("Error when submitting job to NCI queue")
            print(exc.output)
            raise

        print(
            f"PBS job submitted: {proc.stdout.strip()}\n"
            "The CABLE log file for each task is written to "
            f"{internal.FLUXSITE_LOG_DIR}/<task_name>_log.txt\n"
            "The CABLE standard output for each task is written to "
            f"{internal.FLUXSITE_TASKS_DIR}/<task_name>/out.txt\n"
            "The NetCDF output for each task is written to "
            f"{internal.FLUXSITE_OUTPUT_DIR}/<task_name>_out.nc"
        )

    def checkout(self):
        """Endpoint for `benchcab checkout`."""

        setup_src_dir()

        print("Checking out repositories...")
        rev_number_log = ""
        for repo in self.repos:
            repo.checkout(verbose=self.args.verbose)
            rev_number_log += (
                f"{repo.name} last changed revision: "
                f"{repo.svn_info_show_item('last-changed-revision')}\n"
            )

        # TODO(Sean) we should archive revision numbers for CABLE-AUX
        cable_aux_repo = CableRepository(path=internal.CABLE_AUX_RELATIVE_SVN_PATH)
        cable_aux_repo.checkout(verbose=self.args.verbose)

        rev_number_log_path = self.root_dir / next_path(
            self.root_dir, "rev_number-*.log"
        )
        print(
            f"Writing revision number info to {rev_number_log_path.relative_to(self.root_dir)}"
        )
        with open(rev_number_log_path, "w", encoding="utf-8") as file:
            file.write(rev_number_log)

        print("")

    def build(self):
        """Endpoint for `benchcab build`."""
        for repo in self.repos:
            if repo.build_script:
                print(
                    "Compiling CABLE using custom build script for "
                    f"realisation {repo.name}..."
                )
                repo.custom_build(
                    modules=self.config["modules"], verbose=self.args.verbose
                )
            else:
                build_mode = "with MPI" if internal.MPI else "serially"
                print(f"Compiling CABLE {build_mode} for realisation {repo.name}...")
                repo.pre_build(verbose=self.args.verbose)
                repo.run_build(
                    modules=self.config["modules"], verbose=self.args.verbose
                )
                repo.post_build(verbose=self.args.verbose)
            print(f"Successfully compiled CABLE for realisation {repo.name}")
        print("")

    def fluxsite_setup_work_directory(self):
        """Endpoint for `benchcab fluxsite-setup-work-dir`."""
        tasks = self.tasks if self.tasks else self._initialise_tasks()
        print("Setting up run directory tree for fluxsite tests...")
        setup_fluxsite_directory_tree(fluxsite_tasks=tasks, verbose=self.args.verbose)
        print("Setting up tasks...")
        for task in tasks:
            task.setup_task(verbose=self.args.verbose)
        print("Successfully setup fluxsite tasks")
        print("")

    def fluxsite_run_tasks(self):
        """Endpoint for `benchcab fluxsite-run-tasks`."""
        tasks = self.tasks if self.tasks else self._initialise_tasks()
        print("Running fluxsite tasks...")
        try:
            multiprocess = self.config["fluxsite"]["multiprocess"]
        except KeyError:
            multiprocess = internal.FLUXSITE_DEFAULT_MULTIPROCESS
        if multiprocess:
            ncpus = self.config.get("pbs", {}).get(
                "ncpus", internal.FLUXSITE_DEFAULT_PBS["ncpus"]
            )
            run_tasks_in_parallel(tasks, n_processes=ncpus, verbose=self.args.verbose)
        else:
            run_tasks(tasks, verbose=self.args.verbose)
        print("Successfully ran fluxsite tasks")
        print("")

    def fluxsite_bitwise_cmp(self):
        """Endpoint for `benchcab fluxsite-bitwise-cmp`."""

        if not self.modules_handler.module_is_loaded("nccmp/1.8.5.0"):
            self.modules_handler.module_load(
                "nccmp/1.8.5.0"
            )  # use `nccmp -df` for bitwise comparisons

        tasks = self.tasks if self.tasks else self._initialise_tasks()
        comparisons = get_fluxsite_comparisons(tasks)

        print("Running comparison tasks...")
        try:
            multiprocess = self.config["fluxsite"]["multiprocess"]
        except KeyError:
            multiprocess = internal.FLUXSITE_DEFAULT_MULTIPROCESS
        if multiprocess:
            try:
                ncpus = self.config["fluxsite"]["pbs"]["ncpus"]
            except KeyError:
                ncpus = internal.FLUXSITE_DEFAULT_PBS["ncpus"]
            run_comparisons_in_parallel(
                comparisons, n_processes=ncpus, verbose=self.args.verbose
            )
        else:
            run_comparisons(comparisons, verbose=self.args.verbose)
        print("Successfully ran comparison tasks")

    def fluxsite(self):
        """Endpoint for `benchcab fluxsite`."""
        self.checkout()
        self.build()
        self.fluxsite_setup_work_directory()
        if self.args.no_submit:
            self.fluxsite_run_tasks()
            if "fluxsite-bitwise-cmp" not in self.args.skip:
                self.fluxsite_bitwise_cmp()
        else:
            self.fluxsite_submit_job()

    def spatial(self):
        """Endpoint for `benchcab spatial`."""

    def run(self):
        """Endpoint for `benchcab run`."""
        self.fluxsite()
        self.spatial()

    def main(self):
        """Main function for `benchcab`."""

        if self.args.subcommand == "run":
            self.run()

        if self.args.subcommand == "checkout":
            self.checkout()

        if self.args.subcommand == "build":
            self.build()

        if self.args.subcommand == "fluxsite":
            self.fluxsite()

        if self.args.subcommand == "fluxsite-setup-work-dir":
            self.fluxsite_setup_work_directory()

        if self.args.subcommand == "fluxsite-submit-job":
            self.fluxsite_submit_job()

        if self.args.subcommand == "fluxsite-run-tasks":
            self.fluxsite_run_tasks()

        if self.args.subcommand == "fluxsite-bitwise-cmp":
            self.fluxsite_bitwise_cmp()

        if self.args.subcommand == "spatial":
            self.spatial()


def main():
    """Main program entry point for `benchcab`.

    This is required for setup.py entry_points
    """

    app = Benchcab(argv=sys.argv, benchcab_exe_path=shutil.which(sys.argv[0]))
    app.main()


if __name__ == "__main__":
    main()
