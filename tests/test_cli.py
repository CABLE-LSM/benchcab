"""`pytest` tests for `cli.py`."""

import pytest

from benchcab.benchcab import Benchcab
from benchcab.cli import generate_parser


def test_cli_parser():
    """Tests for `generate_parser()`."""
    app = Benchcab(benchcab_exe_path=None)
    parser = generate_parser(app)

    # Success case: default benchcab command
    res = vars(parser.parse_args(["run"]))
    assert res == {
        "config_path": "config.yaml",
        "verbose": False,
        "skip": [],
        "func": app.run,
    }

    # Success case: default validate_config command
    res = vars(parser.parse_args(["validate_config"]))
    assert res == {
        "config_path": "config.yaml",
        "verbose": False,
        "func": app.validate_config,
    }

    # Success case: default checkout command
    res = vars(parser.parse_args(["checkout"]))
    assert res == {
        "config_path": "config.yaml",
        "verbose": False,
        "func": app.checkout,
    }

    # Success case: default build command
    res = vars(parser.parse_args(["build"]))
    assert res == {
        "config_path": "config.yaml",
        "verbose": False,
        "mpi": False,
        "func": app.build,
    }

    # Success case: default fluxsite command
    res = vars(parser.parse_args(["fluxsite"]))
    assert res == {
        "config_path": "config.yaml",
        "no_submit": False,
        "verbose": False,
        "skip": [],
        "func": app.fluxsite,
    }

    # Success case: default fluxsite-setup-work-dir command
    res = vars(parser.parse_args(["fluxsite-setup-work-dir"]))
    assert res == {
        "config_path": "config.yaml",
        "verbose": False,
        "func": app.fluxsite_setup_work_directory,
    }

    # Success case: default fluxsite-submit-job command
    res = vars(parser.parse_args(["fluxsite-submit-job"]))
    assert res == {
        "config_path": "config.yaml",
        "verbose": False,
        "skip": [],
        "func": app.fluxsite_submit_job,
    }

    # Success case: default fluxsite run-tasks command
    res = vars(parser.parse_args(["fluxsite-run-tasks"]))
    assert res == {
        "config_path": "config.yaml",
        "verbose": False,
        "func": app.fluxsite_run_tasks,
    }

    # Success case: default fluxsite-bitwise-cmp command
    res = vars(parser.parse_args(["fluxsite-bitwise-cmp"]))
    assert res == {
        "config_path": "config.yaml",
        "verbose": False,
        "func": app.fluxsite_bitwise_cmp,
    }

    # Success case: default spatial command
    res = vars(parser.parse_args(["spatial"]))
    assert res == {
        "config_path": "config.yaml",
        "verbose": False,
        "skip": [],
        "func": app.spatial,
    }

    # Success case: default spatial-setup-work-dir command
    res = vars(parser.parse_args(["spatial-setup-work-dir"]))
    assert res == {
        "config_path": "config.yaml",
        "verbose": False,
        "func": app.spatial_setup_work_directory,
    }

    # Success case: default spatial-run-tasks command
    res = vars(parser.parse_args(["spatial-run-tasks"]))
    assert res == {
        "config_path": "config.yaml",
        "verbose": False,
        "func": app.spatial_run_tasks,
    }

    # Success case: default gen_codecov command
    res = vars(parser.parse_args(["gen_codecov"]))
    assert res == {
        "config_path": "config.yaml",
        "verbose": False,
        "func": app.gen_codecov,
    }

    # Failure case: pass --no-submit to a non 'run' command
    with pytest.raises(SystemExit):
        parser.parse_args(["fluxsite-setup-work-dir", "--no-submit"])

    # Failure case: pass non-optional command to --skip
    with pytest.raises(SystemExit):
        parser.parse_args(["run", "--skip", "checkout"])
