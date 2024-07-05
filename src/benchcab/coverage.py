# Copyright 2024 ACCESS-NRI and contributors. See the top-level COPYRIGHT file for details.
# SPDX-License-Identifier: Apache-2.0

"""A module containing functions and data structures for running coverage tasks."""

import multiprocessing
import operator
from contextlib import nullcontext
from pathlib import Path
from typing import Optional

from benchcab import internal
from benchcab.environment_modules import EnvironmentModules, EnvironmentModulesInterface
from benchcab.model import Model
from benchcab.utils import get_logger
from benchcab.utils.fs import chdir
from benchcab.utils.subprocess import SubprocessWrapper, SubprocessWrapperInterface


class CoverageTask:
    """A class used to represent a single coverage report generation task."""

    subprocess_handler: SubprocessWrapperInterface = SubprocessWrapper()
    modules_handler: EnvironmentModulesInterface = EnvironmentModules()

    def __init__(
        self,
        coverage_dir: str,
        project_name: Optional[str] = "CABLE",
        dpi_file: Optional[str] = "pgopti.dpi",
        spi_file: Optional[str] = "pgopti.spi",
    ) -> None:
        """Constructor.

        Parameters
        ----------
        coverage_dir:
            Name of directory where coverage analysis is to be done

        project_name:
            Name of project on which codecov is run
        dpi_file:
            name of DPI file created after merging .dyn files created after all runs
        spi_file:
            Static profile information on compilation

        """
        self.logger = get_logger()
        self.coverage_dir = coverage_dir
        self.project_name = project_name
        self.dpi_file = dpi_file
        self.spi_file = spi_file

    def run(self) -> None:
        """Executes `profmerge` and `codecov` to run codecov analysis for a given realisation."""
        if not Path(self.coverage_dir).is_dir():
            msg = f"""The coverage directory: {self.coverage_dir}
            does not exist. Did you run the jobs and/or set `coverage: true` in `config.yaml`
            before the building stage"""
            raise OSError(msg)

        self.logger.info(f"Generating coverage report in {self.coverage_dir}")

        # Load intel-compiler in case we run from CLI, otherwise assuming
        # PBS jobscript loads
        with chdir(self.coverage_dir), (
            nullcontext()
            if self.modules_handler.module_is_loaded("intel-compiler")
            else self.modules_handler.load([internal.DEFAULT_MODULES["intel-compiler"]])
        ):
            self.subprocess_handler.run_cmd(f"profmerge -prof-dpi {self.dpi_file}")
            self.subprocess_handler.run_cmd(
                f"codecov -prj {self.project_name} -dpi {self.dpi_file} -spi {self.spi_file}"
            )


def run_coverage_tasks(coverage_tasks: list[CoverageTask]) -> None:
    """Runs coverage tasks serially."""
    for task in coverage_tasks:
        task.run()


def get_coverage_tasks_default(models: list[Model]) -> list[CoverageTask]:
    """Returns list of Coveragee Tasks setting default values for optional parameters."""
    return [CoverageTask(model.get_coverage_dir()) for model in models]


def run_coverages_in_parallel(
    coverage_tasks: list[CoverageTask],
    n_processes=internal.FLUXSITE_DEFAULT_PBS["ncpus"],
) -> None:
    """Runs coverage tasks in parallel across multiple processes."""
    run_task = operator.methodcaller("run")
    with multiprocessing.Pool(n_processes) as pool:
        pool.map(run_task, coverage_tasks, chunksize=1)
