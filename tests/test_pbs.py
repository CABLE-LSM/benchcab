"""`pytest` tests for `utils/pbs.py`."""

import pytest

pytest.skip(allow_module_level=True)

from benchcab import internal
from benchcab.utils.pbs import render_job_script


def test_render_job_script():
    """Tests for `render_job_script()`."""
    # Success case: test default job script generated is correct
    assert render_job_script(
        project="tm70",
        config_path="/path/to/config.yaml",
        modules=["foo", "bar", "baz"],
        benchcab_path="/absolute/path/to/benchcab",
    ) == (
        f"""#!/bin/bash
#PBS -l wd
#PBS -l ncpus={internal.FLUXSITE_DEFAULT_PBS["ncpus"]}
#PBS -l mem={internal.FLUXSITE_DEFAULT_PBS["mem"]}
#PBS -l walltime={internal.FLUXSITE_DEFAULT_PBS["walltime"]}
#PBS -q normal
#PBS -P tm70
#PBS -j oe
#PBS -m e
#PBS -l storage=gdata/ks32+gdata/hh5

set -ex

module purge
module load foo
module load bar
module load baz

/absolute/path/to/benchcab fluxsite-run-tasks --config=/path/to/config.yaml 

/absolute/path/to/benchcab fluxsite-bitwise-cmp --config=/path/to/config.yaml 

"""
    )

    # Success case: test verbose flag is added to command line arguments
    assert render_job_script(
        project="tm70",
        config_path="/path/to/config.yaml",
        modules=["foo", "bar", "baz"],
        verbose=True,
        benchcab_path="/absolute/path/to/benchcab",
    ) == (
        f"""#!/bin/bash
#PBS -l wd
#PBS -l ncpus={internal.FLUXSITE_DEFAULT_PBS["ncpus"]}
#PBS -l mem={internal.FLUXSITE_DEFAULT_PBS["mem"]}
#PBS -l walltime={internal.FLUXSITE_DEFAULT_PBS["walltime"]}
#PBS -q normal
#PBS -P tm70
#PBS -j oe
#PBS -m e
#PBS -l storage=gdata/ks32+gdata/hh5

set -ex

module purge
module load foo
module load bar
module load baz

/absolute/path/to/benchcab fluxsite-run-tasks --config=/path/to/config.yaml -v

/absolute/path/to/benchcab fluxsite-bitwise-cmp --config=/path/to/config.yaml -v

"""
    )

    # Success case: skip fluxsite-bitwise-cmp step
    assert render_job_script(
        project="tm70",
        config_path="/path/to/config.yaml",
        modules=["foo", "bar", "baz"],
        skip_bitwise_cmp=True,
        benchcab_path="/absolute/path/to/benchcab",
    ) == (
        f"""#!/bin/bash
#PBS -l wd
#PBS -l ncpus={internal.FLUXSITE_DEFAULT_PBS["ncpus"]}
#PBS -l mem={internal.FLUXSITE_DEFAULT_PBS["mem"]}
#PBS -l walltime={internal.FLUXSITE_DEFAULT_PBS["walltime"]}
#PBS -q normal
#PBS -P tm70
#PBS -j oe
#PBS -m e
#PBS -l storage=gdata/ks32+gdata/hh5

set -ex

module purge
module load foo
module load bar
module load baz

/absolute/path/to/benchcab fluxsite-run-tasks --config=/path/to/config.yaml 

"""
    )

    # Success case: specify parameters in pbs_config
    assert render_job_script(
        project="tm70",
        config_path="/path/to/config.yaml",
        modules=["foo", "bar", "baz"],
        skip_bitwise_cmp=True,
        benchcab_path="/absolute/path/to/benchcab",
        pbs_config={
            "ncpus": 4,
            "mem": "16GB",
            "walltime": "00:00:30",
            "storage": ["gdata/foo"],
        },
    ) == (
        """#!/bin/bash
#PBS -l wd
#PBS -l ncpus=4
#PBS -l mem=16GB
#PBS -l walltime=00:00:30
#PBS -q normal
#PBS -P tm70
#PBS -j oe
#PBS -m e
#PBS -l storage=gdata/ks32+gdata/hh5+gdata/foo

set -ex

module purge
module load foo
module load bar
module load baz

/absolute/path/to/benchcab fluxsite-run-tasks --config=/path/to/config.yaml 

"""
    )

    # Success case: if the pbs_config is empty, use the default values
    assert render_job_script(
        project="tm70",
        config_path="/path/to/config.yaml",
        modules=["foo", "bar", "baz"],
        skip_bitwise_cmp=True,
        benchcab_path="/absolute/path/to/benchcab",
        pbs_config={},
    ) == (
        f"""#!/bin/bash
#PBS -l wd
#PBS -l ncpus={internal.FLUXSITE_DEFAULT_PBS["ncpus"]}
#PBS -l mem={internal.FLUXSITE_DEFAULT_PBS["mem"]}
#PBS -l walltime={internal.FLUXSITE_DEFAULT_PBS["walltime"]}
#PBS -q normal
#PBS -P tm70
#PBS -j oe
#PBS -m e
#PBS -l storage=gdata/ks32+gdata/hh5

set -ex

module purge
module load foo
module load bar
module load baz

/absolute/path/to/benchcab fluxsite-run-tasks --config=/path/to/config.yaml 

"""
    )
