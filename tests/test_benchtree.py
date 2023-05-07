"""`pytest` tests for benchtree.py"""

from pathlib import Path


from tests.common import TMP_DIR
from tests.common import make_barebones_config
from benchcab.task import Task
from benchcab.benchtree import (
    setup_fluxnet_directory_tree,
    clean_directory_tree,
    setup_src_dir,
)


def setup_mock_tasks() -> list[Task]:
    """Return a mock list of fluxnet tasks."""

    config = make_barebones_config()
    (branch_id_a, branch_a), (branch_id_b, branch_b) = enumerate(config["realisations"])
    met_site_a, met_site_b = "site_foo", "site_bar"
    (sci_id_a, sci_config_a), (sci_id_b, sci_config_b) = enumerate(
        config["science_configurations"]
    )

    tasks = [
        Task(branch_id_a, branch_a["name"], {}, met_site_a, sci_id_a, sci_config_a),
        Task(branch_id_a, branch_a["name"], {}, met_site_a, sci_id_b, sci_config_b),
        Task(branch_id_a, branch_a["name"], {}, met_site_b, sci_id_a, sci_config_a),
        Task(branch_id_a, branch_a["name"], {}, met_site_b, sci_id_b, sci_config_b),
        Task(branch_id_b, branch_b["name"], {}, met_site_a, sci_id_a, sci_config_a),
        Task(branch_id_b, branch_b["name"], {}, met_site_a, sci_id_b, sci_config_b),
        Task(branch_id_b, branch_b["name"], {}, met_site_b, sci_id_a, sci_config_a),
        Task(branch_id_b, branch_b["name"], {}, met_site_b, sci_id_b, sci_config_b),
    ]

    return tasks


def test_setup_directory_tree():
    """Tests for `setup_fluxnet_directory_tree()`."""

    # Success case: generate fluxnet directory structure
    tasks = setup_mock_tasks()
    setup_fluxnet_directory_tree(fluxnet_tasks=tasks, root_dir=TMP_DIR)

    assert len(list(TMP_DIR.glob("*"))) == 1
    assert Path(TMP_DIR, "runs").exists()
    assert Path(TMP_DIR, "runs", "site").exists()
    assert Path(TMP_DIR, "runs", "site", "logs").exists()
    assert Path(TMP_DIR, "runs", "site", "outputs").exists()
    assert Path(TMP_DIR, "runs", "site", "analysis", "bitwise-comparisons").exists()
    assert Path(TMP_DIR, "runs", "site", "tasks").exists()

    assert Path(TMP_DIR, "runs", "site", "tasks", "site_foo_R0_S0").exists()
    assert Path(TMP_DIR, "runs", "site", "tasks", "site_foo_R0_S1").exists()
    assert Path(TMP_DIR, "runs", "site", "tasks", "site_bar_R0_S0").exists()
    assert Path(TMP_DIR, "runs", "site", "tasks", "site_bar_R0_S1").exists()
    assert Path(TMP_DIR, "runs", "site", "tasks", "site_foo_R1_S0").exists()
    assert Path(TMP_DIR, "runs", "site", "tasks", "site_foo_R1_S1").exists()
    assert Path(TMP_DIR, "runs", "site", "tasks", "site_bar_R1_S0").exists()
    assert Path(TMP_DIR, "runs", "site", "tasks", "site_bar_R1_S1").exists()


def test_clean_directory_tree():
    """Tests for `clean_directory_tree()`."""

    # Success case: directory tree does not exist after clean
    tasks = setup_mock_tasks()
    setup_fluxnet_directory_tree(fluxnet_tasks=tasks, root_dir=TMP_DIR)

    clean_directory_tree(root_dir=TMP_DIR)
    assert not Path(TMP_DIR, "runs").exists()

    setup_src_dir(root_dir=TMP_DIR)
    clean_directory_tree(root_dir=TMP_DIR)
    assert not Path(TMP_DIR, "src").exists()


def test_setup_src_dir():
    """Tests for `setup_src_dir()`."""

    # Success case: make src directory
    setup_src_dir(root_dir=TMP_DIR)
    assert Path(TMP_DIR, "src").exists()
