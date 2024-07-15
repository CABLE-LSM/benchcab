# Copyright 2022 ACCESS-NRI and contributors. See the top-level COPYRIGHT file for details.
# SPDX-License-Identifier: Apache-2.0

"""Contains helper functions for manipulating PBS job scripts."""

from typing import Optional, TypedDict

from benchcab.utils import interpolate_file_template


class PBSConfig(TypedDict):
    """Default parameters for PBS runs via benchcab."""

    ncpus: int
    mem: str
    walltime: str
    storage: str


def render_job_script(
    project: str,
    config_path: str,
    modules: list,
    benchcab_path: str,
    pbs_config: PBSConfig,
    verbose: Optional[bool] = False,
    skip_bitwise_cmp: Optional[bool] = False,
    skip_codecov: Optional[bool] = True,
) -> str:
    """Returns the text for a PBS job script that executes all computationally expensive commands.

    This includes things such as running CABLE and running bitwise comparison jobs
    between model output files.
    """
    verbose_flag = " -v" if verbose else ""
    storage_flags = ["gdata/ks32", "gdata/hh5", "gdata/wd9", *pbs_config["storage"]]

    context = dict(
        modules=modules,
        verbose_flag=verbose_flag,
        ncpus=pbs_config["ncpus"],
        mem=pbs_config["mem"],
        walltime=pbs_config["walltime"],
        project=project,
        storage="+".join(storage_flags),
        benchcab_path=benchcab_path,
        config_path=config_path,
        skip_bitwise_cmp=skip_bitwise_cmp,
        skip_codecov=skip_codecov,
    )

    return interpolate_file_template("pbs_jobscript.j2", **context)
