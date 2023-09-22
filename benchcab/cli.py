# Copyright 2022 ACCESS-NRI and contributors. See the top-level COPYRIGHT file for details.
# SPDX-License-Identifier: Apache-2.0

"""Contains the definition of the command line interface used for `benchcab`."""

import argparse
import benchcab


from benchcab.internal import OPTIONAL_COMMANDS


def generate_parser() -> argparse.ArgumentParser:
    """Returns the instance of `argparse.ArgumentParser` used for `benchcab`."""

    # parent parser that contains the help argument
    args_help = argparse.ArgumentParser(add_help=False)
    args_help.add_argument(
        "-h",
        "--help",
        action="help",
        default=argparse.SUPPRESS,
        help="Show this help message and exit.",
    )

    # parent parser that contains arguments common to all subcommands
    args_subcommand = argparse.ArgumentParser(add_help=False)
    args_subcommand.add_argument(
        "-c", "--config", help="Config filename.", default="config.yaml"
    )
    args_subcommand.add_argument(
        "-v",
        "--verbose",
        help="Enable more detailed output in the command line.",
        action="store_true",
    )

    # parent parser that contains arguments common to all run specific subcommands
    args_run_subcommand = argparse.ArgumentParser(add_help=False)
    args_run_subcommand.add_argument(
        "--no-submit",
        action="store_true",
        help="Force benchcab to execute tasks on the current compute node.",
    )

    # parent parser that contains arguments common to all composite subcommands
    args_composite_subcommand = argparse.ArgumentParser(add_help=False)
    args_composite_subcommand.add_argument(
        "--skip",
        action="append",
        default=[],
        choices=OPTIONAL_COMMANDS,
        help="""Specify subcommand to skip in the workflow. Note, only optional commands
        can be skipped.""",
    )

    # main parser
    main_parser = argparse.ArgumentParser(
        description="benchcab is a tool for evaluation of the CABLE land surface model.",
        parents=[args_help],
        add_help=False,
    )

    main_parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"benchcab {benchcab.__version__}",
        help="Show program's version number and exit.",
    )

    subparsers = main_parser.add_subparsers(dest="subcommand", metavar="command")

    # subcommand: 'benchcab run'
    subparsers.add_parser(
        "run",
        parents=[
            args_help,
            args_subcommand,
            args_run_subcommand,
            args_composite_subcommand,
        ],
        help="Run all test suites for CABLE.",
        description="""Runs all test suites for CABLE: fluxsite and spatial test suites. This
        command runs the full default set of tests for CABLE.""",
        add_help=False,
    )

    # subcommand: 'benchcab fluxsite'
    subparsers.add_parser(
        "fluxsite",
        parents=[
            args_help,
            args_subcommand,
            args_run_subcommand,
            args_composite_subcommand,
        ],
        help="Run the fluxsite test suite for CABLE.",
        description="""Runs the default fluxsite test suite for CABLE. This command is the
        equivalent of running 'benchcab checkout', 'benchcab build', 'benchcab
        fluxsite-setup-work-dir', and 'benchcab fluxsite-submit-job' sequentially.""",
        add_help=False,
    )

    # subcommand: 'benchcab checkout'
    subparsers.add_parser(
        "checkout",
        parents=[args_help, args_subcommand],
        help="Run the checkout step in the benchmarking workflow.",
        description="""Checkout CABLE repositories specified in the config file and the CABLE-AUX
        repository.""",
        add_help=False,
    )

    # subcommand: 'benchcab build'
    subparsers.add_parser(
        "build",
        parents=[args_help, args_subcommand],
        help="Run the build step in the benchmarking workflow.",
        description="""Build the CABLE offline executable for each repository specified in the
        config file.""",
        add_help=False,
    )

    # subcommand: 'benchcab fluxsite-setup-work-dir'
    subparsers.add_parser(
        "fluxsite-setup-work-dir",
        parents=[args_help, args_subcommand],
        help="Run the work directory setup step of the fluxsite command.",
        description="""Generates the fluxsite run directory tree in the current working
        directory so that fluxsite tasks can be run.""",
        add_help=False,
    )

    # subcommand: 'benchcab fluxsite-submit-job'
    subparsers.add_parser(
        "fluxsite-submit-job",
        parents=[args_help, args_subcommand, args_composite_subcommand],
        help="Generate and submit the PBS job script for the fluxsite test suite.",
        description="""Generates and submits the PBS job script for the fluxsite test suite.""",
        add_help=False,
    )

    # subcommand: 'benchcab fluxsite-run-tasks'
    subparsers.add_parser(
        "fluxsite-run-tasks",
        parents=[args_help, args_subcommand],
        help="Run the fluxsite tasks of the main fluxsite command.",
        description="""Runs the fluxsite tasks for the fluxsite test suite. Note, this command should
        ideally be run inside a PBS job. This command is invoked by the PBS job script generated by
        `benchcab run`.""",
        add_help=False,
    )

    # subcommand: 'benchcab fluxsite-bitwise-cmp'
    subparsers.add_parser(
        "fluxsite-bitwise-cmp",
        parents=[args_help, args_subcommand],
        help="Run the bitwise comparison step of the main fluxsite command.",
        description="""Runs the bitwise comparison step for the fluxsite test suite. Bitwise
        comparisons are done on NetCDF output files using the `nccmp -df` command. Comparisons
        are made between outputs that differ in their realisation and are matching in
        all other configurations. Note, this command should ideally be run inside a PBS job.
        This command is invoked by the PBS job script generated by `benchcab run`""",
        add_help=False,
    )

    # subcommand: 'benchcab spatial'
    subparsers.add_parser(
        "spatial",
        parents=[args_help, args_subcommand],
        help="Run the spatial tests only.",
        description="""Runs the default spatial test suite for CABLE.""",
        add_help=False,
    )

    return main_parser
