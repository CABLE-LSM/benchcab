#!/usr/bin/env python

# To run the CABLE benchmarking at single sites
import argparse
import sys
import os
from pathlib import Path
import yaml

from benchcab.run_cable_site import RunCableSite
from benchcab.bench_config import BenchSetup

# Define names of default config files globally
default_config = "config.yaml"
default_science = "site_configs.yaml"


def myparse(arglist):
    """
    Parse arguments given as list (arglist)
    """
    parser = argparse.ArgumentParser(
        description="Run CABLE simulations at single sites for benchmarking"
    )
    parser.add_argument(
        "-q",
        "--qsub",
        help="Creates a qsub job script if running at NCI",
        action="store_true",
    )
    parser.add_argument(
        "-c", "--config", help="Config filename", default=default_config
    )
    parser.add_argument(
        "-s",
        "--science_config",
        help="Config file to define the various configurations to run",
        default=default_science,
    )

    args = parser.parse_args(arglist)

    (_, nodename, _, _, _) = os.uname()
    if args.qsub and not "nci" in nodename:
        print("Remote scripts are only implemented for NCI machine")
        print("You can not invoke benchsiterun -q if not running at NCI")
        raise

    if not "nci" in nodename and not args.met_dir:
        raise (
            "You need to specify the path to the meteorological data if you are not running at NCI."
        )

    return args


def read_sci_configs(sci_configfile):
    """Read the science config file"""

    with open(sci_configfile, "r") as fin:
        sci_configs = yaml.safe_load(fin)

    return sci_configs


def main(qsub=False, config=default_config, science_config=default_science, **kwargs):
    """To run CABLE on single sites for the benchmarking.
    Keyword arguments are the same as the command line arguments for the benchsiterun command
    """
    # Always run site simulations without mpi and with multiprocess
    mpi = False
    multiprocess = True

    # Read setup and create directory structure for single site runs
    mysetup = BenchSetup(config)
    opt, compilation_opt, benchdirs = mysetup.setup_bench()
    benchdirs.create_sitebenchtree()

    # Read science configurations
    sci_configs = read_sci_configs(science_config)

    if qsub:
        # Create a script to launch on NCI's compute nodes if requested
        # Create a run object instance using default values since we won't use those values
        R = RunCableSite()
        R.create_qsub_script(opt["project"], opt["user"], config, science_config)

    else:

        # Aliases to branches to use:
        branch_alias = opt["use_branches"]
        run_branches = [
            opt[branch_alias[0]],
        ]
        run_branches.append(opt[branch_alias[1]])

        start_dir = Path.cwd()
        os.chdir(benchdirs.runroot_dir / "site")
        for branchid, branch in enumerate(run_branches):
            branch_name = branch["name"]
            cable_src = benchdirs.src_dir / branch_name

            # Define the name for the executable: cable for serial, cable-mpi for mpi runs
            cable_exe = f"cable{'-mpi'*mpi}"

            R = RunCableSite(
                met_dir=compilation_opt["met_dir"],
                log_dir=benchdirs.site_run["log_dir"],
                output_dir=benchdirs.site_run["output_dir"],
                restart_dir=benchdirs.site_run["restart_dir"],
                aux_dir=benchdirs.aux_dir,
                namelist_dir=benchdirs.site_run["namelist_dir"],
                met_subset=opt["met_subset"],
                cable_src=cable_src,
                num_cores=None,
                cable_exe=cable_exe,
                multiprocess=multiprocess,
            )

            for sci_id, sci_config in enumerate(sci_configs.values()):
                R.main(sci_config, branchid, sci_id)

        os.chdir(start_dir)


def main_parse_args(arglist):
    """
    Call main with list of arguments. Callable from tests
    """
    # Must return so that check command return value is passed back to calling routine
    # otherwise py.test will fail
    return main(**vars(myparse(arglist)))


def main_argv():
    """
    Call main and pass command line arguments. This is required for setup.py entry_points
    """
    mess = main_parse_args(sys.argv[1:])


if __name__ == "__main__":

    main_argv()
