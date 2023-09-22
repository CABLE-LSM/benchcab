# Copyright 2022 ACCESS-NRI and contributors. See the top-level COPYRIGHT file for details.
# SPDX-License-Identifier: Apache-2.0

"""Contains helper functions for manipulating PBS job scripts."""

from typing import Optional

from benchcab import internal


def render_job_script(
    project: str,
    config_path: str,
    modules: list,
    benchcab_path: str,
    verbose=False,
    skip_bitwise_cmp=False,
    pbs_config: Optional[dict] = None,
) -> str:
    """Returns the text for a PBS job script that executes all computationally expensive commands.

    This includes things such as running CABLE and running bitwise comparison jobs
    between model output files.
    """

    if pbs_config is None:
        pbs_config = internal.FLUXSITE_DEFAULT_PBS

    module_load_lines = "\n".join(
        f"module load {module_name}" for module_name in modules
    )
    verbose_flag = "-v" if verbose else ""
    ncpus = pbs_config.get("ncpus", internal.FLUXSITE_DEFAULT_PBS["ncpus"])
    mem = pbs_config.get("mem", internal.FLUXSITE_DEFAULT_PBS["mem"])
    walltime = pbs_config.get("walltime", internal.FLUXSITE_DEFAULT_PBS["walltime"])
    storage_flags = [
        "gdata/ks32",
        "gdata/hh5",
        f"gdata/{project}",
        *pbs_config.get("storage", internal.FLUXSITE_DEFAULT_PBS["storage"]),
    ]
    return f"""#!/bin/bash
#PBS -l wd
#PBS -l ncpus={ncpus}
#PBS -l mem={mem}
#PBS -l walltime={walltime}
#PBS -q normal
#PBS -P {project}
#PBS -j oe
#PBS -m e
#PBS -l storage={'+'.join(storage_flags)}

module purge
{module_load_lines}

{benchcab_path} fluxsite-run-tasks --config={config_path} {verbose_flag}
if [ $? -ne 0 ]; then
    echo 'Error: benchcab fluxsite-run-tasks failed. Exiting...'
    exit 1
fi
{'' if skip_bitwise_cmp else f'''
{benchcab_path} fluxsite-bitwise-cmp --config={config_path} {verbose_flag}
if [ $? -ne 0 ]; then
    echo 'Error: benchcab fluxsite-bitwise-cmp failed. Exiting...'
    exit 1
fi''' }
"""
