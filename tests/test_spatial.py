"""`pytest` tests for spatial.py.

Note: explicit teardown for generated files and directories are not required as
the working directory used for testing is cleaned up in the `_run_around_tests`
pytest autouse fixture.
"""

import logging

import f90nml
import pytest
import yaml
from benchcab import internal
from benchcab.model import Model
from benchcab.spatial import SpatialTask, get_spatial_tasks
from benchcab.utils.repo import Repo


@pytest.fixture()
def mock_repo():
    class MockRepo(Repo):
        def __init__(self) -> None:
            self.branch = "test-branch"
            self.revision = "1234"

        def checkout(self):
            pass

        def get_branch_name(self) -> str:
            return self.branch

        def get_revision(self) -> str:
            return self.revision

    return MockRepo()


@pytest.fixture()
def model(mock_subprocess_handler, mock_repo):
    """Returns a `Model` instance."""
    _model = Model(
        model_id=1,
        repo=mock_repo,
        name=mock_repo.get_branch_name(),
        patch={"cable": {"some_branch_specific_setting": True}},
    )
    _model.subprocess_handler = mock_subprocess_handler
    return _model


@pytest.fixture()
def task(model, mock_subprocess_handler):
    """Returns a mock `SpatialTask` instance."""
    _task = SpatialTask(
        model=model,
        met_forcing_name="crujra_access",
        met_forcing_payu_experiment="https://github.com/CABLE-LSM/cable_example.git",
        sci_conf_id=0,
        sci_config={"cable": {"some_setting": True}},
    )
    _task.subprocess_handler = mock_subprocess_handler
    return _task


class TestGetTaskName:
    """Tests for `SpatialTask.get_task_name()`."""

    def test_task_name_convention(self, task):
        """Success case: check task name convention."""
        assert task.get_task_name() == "crujra_access_R1_S0"


class TestConfigureExperiment:
    """Tests for `SpatialTask.configure_experiment()`."""

    @pytest.fixture(autouse=True)
    def _create_task_dir(self):
        task_dir = internal.SPATIAL_TASKS_DIR / "crujra_access_R1_S0"
        task_dir.mkdir(parents=True)
        (task_dir / "config.yaml").touch()
        (task_dir / "cable.nml").touch()

    def test_payu_config_parameters(self, task):
        """Success case: check config.yaml parameters."""
        task.configure_experiment(payu_config={"some_parameter": "foo"})
        config_path = internal.SPATIAL_TASKS_DIR / task.get_task_name() / "config.yaml"
        with config_path.open("r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
        assert config["exe"] == str(
            (
                internal.SRC_DIR / "test-branch" / "bin" / internal.CABLE_MPI_EXE
            ).absolute()
        )
        assert config["laboratory"] == str(internal.PAYU_LABORATORY_DIR.absolute())
        assert config["some_parameter"] == "foo"

    @pytest.mark.parametrize(
        ("verbosity", "expected"),
        [
            (logging.INFO, ""),
            (
                logging.DEBUG,
                "  Updating experiment config parameters in "
                "runs/spatial/tasks/crujra_access_R1_S0/config.yaml",
            ),
        ],
    )
    def test_standard_output(self, task, verbosity, expected, caplog):
        """Success case: test standard output."""
        caplog.set_level(verbosity)
        task.configure_experiment()
        output = "\n".join(caplog.messages) if caplog.messages else ""
        assert output == expected


class TestUpdateNamelist:
    """Tests for `SpatialTask.update_namelist()`."""

    @pytest.fixture(autouse=True)
    def _create_task_dir(self):
        task_dir = internal.SPATIAL_TASKS_DIR / "crujra_access_R1_S0"
        task_dir.mkdir(parents=True)
        (task_dir / "config.yaml").touch()
        (task_dir / "cable.nml").touch()

    def test_namelist_parameters_are_patched(self, task):
        """Success case: test namelist parameters are patched."""
        task.update_namelist()
        res_nml = f90nml.read(
            str(internal.SPATIAL_TASKS_DIR / task.get_task_name() / internal.CABLE_NML)
        )
        assert res_nml["cable"] == {
            "some_setting": True,
            "some_branch_specific_setting": True,
        }

    @pytest.mark.parametrize(
        ("verbosity", "expected"),
        [
            (logging.INFO, ""),
            (
                logging.DEBUG,
                "  Adding science configurations to CABLE namelist file "
                "runs/spatial/tasks/crujra_access_R1_S0/cable.nml\n"
                "  Adding branch specific configurations to CABLE namelist file "
                "runs/spatial/tasks/crujra_access_R1_S0/cable.nml",
            ),
        ],
    )
    def test_standard_output(self, task, verbosity, expected, caplog):
        """Success case: test standard output."""
        caplog.set_level(verbosity)
        task.update_namelist()
        output = "\n".join(caplog.messages) if caplog.messages else ""
        assert output == expected


class TestRun:
    """Tests for `SpatialTask.run()`."""

    @pytest.fixture(autouse=True)
    def _setup(self, task):
        task_dir = internal.SPATIAL_TASKS_DIR / task.get_task_name()
        task_dir.mkdir(parents=True, exist_ok=True)

    def test_payu_run_command(self, task, mock_subprocess_handler):
        """Success case: test payu run command."""
        task.run()
        assert "payu run" in mock_subprocess_handler.commands

    def test_payu_run_with_optional_arguments(self, task, mock_subprocess_handler):
        """Success case: test payu run command with optional arguments."""
        task.payu_args = "--some-flag"
        task.run()
        assert "payu run --some-flag" in mock_subprocess_handler.commands


class TestGetSpatialTasks:
    """Tests for `get_spatial_tasks()`."""

    @pytest.fixture()
    def models(self, mock_repo):
        """Return a list of `Model` instances used for testing."""
        return [Model(repo=mock_repo, model_id=id) for id in range(2)]

    @pytest.fixture()
    def met_forcings(self, config):
        """Return a list of spatial met forcing specifications."""
        return config["spatial"]["met_forcings"]

    @pytest.fixture()
    def science_configurations(self, config):
        """Return a list of science configurations used for testing."""
        return config["science_configurations"]

    def test_task_product_across_branches_forcings_and_configurations(
        self, models, met_forcings, science_configurations
    ):
        """Success case: test task product across branches, forcings and configurations."""
        tasks = get_spatial_tasks(
            models=models,
            met_forcings=met_forcings,
            science_configurations=science_configurations,
        )
        met_forcing_names = list(met_forcings.keys())
        assert [
            (task.model, task.met_forcing_name, task.sci_config) for task in tasks
        ] == [
            (models[0], met_forcing_names[0], science_configurations[0]),
            (models[0], met_forcing_names[0], science_configurations[1]),
            (models[0], met_forcing_names[1], science_configurations[0]),
            (models[0], met_forcing_names[1], science_configurations[1]),
            (models[1], met_forcing_names[0], science_configurations[0]),
            (models[1], met_forcing_names[0], science_configurations[1]),
            (models[1], met_forcing_names[1], science_configurations[0]),
            (models[1], met_forcing_names[1], science_configurations[1]),
        ]
