"""`pytest` tests for `workdir.py`."""

import contextlib
import io
import shutil
from pathlib import Path

import pytest

pytest.skip(allow_module_level=True)

from benchcab.fluxsite import Task
from benchcab.repository import CableRepository
from benchcab.workdir import (
    clean_directory_tree,
    setup_fluxsite_directory_tree,
    setup_src_dir,
)
from tests.common import MOCK_CWD, get_mock_config


def setup_mock_tasks() -> list[Task]:
    """Return a mock list of fluxsite tasks."""
    config = get_mock_config()
    repo_a = CableRepository("trunk", repo_id=0)
    repo_b = CableRepository("path/to/my-branch", repo_id=1)
    met_forcing_file_a, met_forcing_file_b = "site_foo", "site_bar"
    (sci_id_a, sci_config_a), (sci_id_b, sci_config_b) = enumerate(
        config["science_configurations"]
    )

    tasks = [
        Task(repo_a, met_forcing_file_a, sci_id_a, sci_config_a),
        Task(repo_a, met_forcing_file_a, sci_id_b, sci_config_b),
        Task(repo_a, met_forcing_file_b, sci_id_a, sci_config_a),
        Task(repo_a, met_forcing_file_b, sci_id_b, sci_config_b),
        Task(repo_b, met_forcing_file_a, sci_id_a, sci_config_a),
        Task(repo_b, met_forcing_file_a, sci_id_b, sci_config_b),
        Task(repo_b, met_forcing_file_b, sci_id_a, sci_config_a),
        Task(repo_b, met_forcing_file_b, sci_id_b, sci_config_b),
    ]

    return tasks


def test_setup_directory_tree():
    """Tests for `setup_fluxsite_directory_tree()`."""
    # Success case: generate fluxsite directory structure
    tasks = setup_mock_tasks()
    setup_fluxsite_directory_tree(fluxsite_tasks=tasks, root_dir=MOCK_CWD)

    assert len(list(MOCK_CWD.glob("*"))) == 1
    assert Path(MOCK_CWD, "runs").exists()
    assert Path(MOCK_CWD, "runs", "fluxsite").exists()
    assert Path(MOCK_CWD, "runs", "fluxsite", "logs").exists()
    assert Path(MOCK_CWD, "runs", "fluxsite", "outputs").exists()
    assert Path(MOCK_CWD, "runs", "fluxsite", "tasks").exists()
    assert Path(
        MOCK_CWD, "runs", "fluxsite", "analysis", "bitwise-comparisons"
    ).exists()

    assert Path(MOCK_CWD, "runs", "fluxsite", "tasks", "site_foo_R0_S0").exists()
    assert Path(MOCK_CWD, "runs", "fluxsite", "tasks", "site_foo_R0_S1").exists()
    assert Path(MOCK_CWD, "runs", "fluxsite", "tasks", "site_bar_R0_S0").exists()
    assert Path(MOCK_CWD, "runs", "fluxsite", "tasks", "site_bar_R0_S1").exists()
    assert Path(MOCK_CWD, "runs", "fluxsite", "tasks", "site_foo_R1_S0").exists()
    assert Path(MOCK_CWD, "runs", "fluxsite", "tasks", "site_foo_R1_S1").exists()
    assert Path(MOCK_CWD, "runs", "fluxsite", "tasks", "site_bar_R1_S0").exists()
    assert Path(MOCK_CWD, "runs", "fluxsite", "tasks", "site_bar_R1_S1").exists()

    shutil.rmtree(MOCK_CWD / "runs")

    # Success case: test non-verbose output
    with contextlib.redirect_stdout(io.StringIO()) as buf:
        setup_fluxsite_directory_tree(fluxsite_tasks=tasks, root_dir=MOCK_CWD)
    assert buf.getvalue() == (
        f"Creating runs/fluxsite/logs directory: {MOCK_CWD}/runs/fluxsite/logs\n"
        f"Creating runs/fluxsite/outputs directory: {MOCK_CWD}/runs/fluxsite/outputs\n"
        f"Creating runs/fluxsite/tasks directory: {MOCK_CWD}/runs/fluxsite/tasks\n"
        f"Creating runs/fluxsite/analysis directory: {MOCK_CWD}/runs/fluxsite/analysis\n"
        f"Creating runs/fluxsite/analysis/bitwise-comparisons directory: {MOCK_CWD}"
        "/runs/fluxsite/analysis/bitwise-comparisons\n"
        f"Creating task directories...\n"
    )

    shutil.rmtree(MOCK_CWD / "runs")

    # Success case: test verbose output
    with contextlib.redirect_stdout(io.StringIO()) as buf:
        setup_fluxsite_directory_tree(
            fluxsite_tasks=tasks, verbose=True, root_dir=MOCK_CWD
        )
    assert buf.getvalue() == (
        f"Creating runs/fluxsite/logs directory: {MOCK_CWD}/runs/fluxsite/logs\n"
        f"Creating runs/fluxsite/outputs directory: {MOCK_CWD}/runs/fluxsite/outputs\n"
        f"Creating runs/fluxsite/tasks directory: {MOCK_CWD}/runs/fluxsite/tasks\n"
        f"Creating runs/fluxsite/analysis directory: {MOCK_CWD}/runs/fluxsite/analysis\n"
        f"Creating runs/fluxsite/analysis/bitwise-comparisons directory: {MOCK_CWD}"
        "/runs/fluxsite/analysis/bitwise-comparisons\n"
        f"Creating task directories...\n"
        f"Creating runs/fluxsite/tasks/site_foo_R0_S0: "
        f"{MOCK_CWD}/runs/fluxsite/tasks/site_foo_R0_S0\n"
        f"Creating runs/fluxsite/tasks/site_foo_R0_S1: "
        f"{MOCK_CWD}/runs/fluxsite/tasks/site_foo_R0_S1\n"
        f"Creating runs/fluxsite/tasks/site_bar_R0_S0: "
        f"{MOCK_CWD}/runs/fluxsite/tasks/site_bar_R0_S0\n"
        f"Creating runs/fluxsite/tasks/site_bar_R0_S1: "
        f"{MOCK_CWD}/runs/fluxsite/tasks/site_bar_R0_S1\n"
        f"Creating runs/fluxsite/tasks/site_foo_R1_S0: "
        f"{MOCK_CWD}/runs/fluxsite/tasks/site_foo_R1_S0\n"
        f"Creating runs/fluxsite/tasks/site_foo_R1_S1: "
        f"{MOCK_CWD}/runs/fluxsite/tasks/site_foo_R1_S1\n"
        f"Creating runs/fluxsite/tasks/site_bar_R1_S0: "
        f"{MOCK_CWD}/runs/fluxsite/tasks/site_bar_R1_S0\n"
        f"Creating runs/fluxsite/tasks/site_bar_R1_S1: "
        f"{MOCK_CWD}/runs/fluxsite/tasks/site_bar_R1_S1\n"
    )

    shutil.rmtree(MOCK_CWD / "runs")


def test_clean_directory_tree():
    """Tests for `clean_directory_tree()`."""
    # Success case: directory tree does not exist after clean
    tasks = setup_mock_tasks()
    setup_fluxsite_directory_tree(fluxsite_tasks=tasks, root_dir=MOCK_CWD)

    clean_directory_tree(root_dir=MOCK_CWD)
    assert not Path(MOCK_CWD, "runs").exists()

    setup_src_dir(root_dir=MOCK_CWD)
    clean_directory_tree(root_dir=MOCK_CWD)
    assert not Path(MOCK_CWD, "src").exists()


def test_setup_src_dir():
    """Tests for `setup_src_dir()`."""
    # Success case: make src directory
    setup_src_dir(root_dir=MOCK_CWD)
    assert Path(MOCK_CWD, "src").exists()
