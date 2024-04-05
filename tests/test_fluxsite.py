"""`pytest` tests for `fluxsite.py`.

Note: explicit teardown for generated files and directories are not required as
the working directory used for testing is cleaned up in the `_run_around_tests`
pytest autouse fixture.
"""

import math

import f90nml
import netCDF4
import pytest
from benchcab import __version__, internal
from benchcab.fluxsite import (
    CableError,
    FluxsiteTask,
    get_comparison_name,
    get_fluxsite_comparisons,
    get_fluxsite_tasks,
)
from benchcab.model import Model
from benchcab.utils.repo import Repo


@pytest.fixture()
def mock_repo():  # noqa: D103
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
        patch={"cable": {"some_branch_specific_setting": True}},
    )
    _model.subprocess_handler = mock_subprocess_handler
    return _model


@pytest.fixture()
def task(model, mock_subprocess_handler):
    """Returns a mock `FluxsiteTask` instance."""
    _task = FluxsiteTask(
        model=model,
        met_forcing_file="forcing-file.nc",
        sci_conf_id=0,
        sci_config={"cable": {"some_setting": True}},
    )
    _task.subprocess_handler = mock_subprocess_handler
    return _task


class TestGetTaskName:
    """tests for `FluxsiteTask.get_task_name()`."""

    def test_task_name_convention(self, task):
        """Success case: check task name convention."""
        assert task.get_task_name() == "forcing-file_R1_S0"


class TestGetLogFilename:
    """Tests for `FluxsiteTask.get_log_filename()`."""

    def test_log_filename_convention(self, task):
        """Success case: check log file name convention."""
        assert task.get_log_filename() == "forcing-file_R1_S0_log.txt"


class TestGetOutputFilename:
    """Tests for `FluxsiteTask.get_output_filename()`."""

    def test_output_filename_convention(self, task):
        """Success case: check output file name convention."""
        assert task.get_output_filename() == "forcing-file_R1_S0_out.nc"


class TestFetchFiles:
    """Tests for `FluxsiteTask.fetch_files()`."""

    @pytest.fixture(autouse=True)
    def _setup(self, task):
        """Setup precondition for `FluxsiteTask.fetch_files()`."""
        internal.NAMELIST_DIR.mkdir()
        (internal.NAMELIST_DIR / internal.CABLE_NML).touch()
        (internal.NAMELIST_DIR / internal.CABLE_SOIL_NML).touch()
        (internal.NAMELIST_DIR / internal.CABLE_VEGETATION_NML).touch()

        task_name = task.get_task_name()
        (internal.FLUXSITE_DIRS["TASKS"] / task_name).mkdir(parents=True)
        (internal.FLUXSITE_DIRS["OUTPUT"]).mkdir(parents=True)
        (internal.FLUXSITE_DIRS["LOG"]).mkdir(parents=True)

        exe_build_dir = internal.SRC_DIR / "test-branch" / "bin"
        exe_build_dir.mkdir(parents=True)
        (exe_build_dir / internal.CABLE_EXE).touch()

    def test_required_files_are_copied_to_task_dir(self, task):
        """Success case: test required files are copied to task directory."""
        task.fetch_files()
        task_dir = internal.FLUXSITE_DIRS["TASKS"] / task.get_task_name()
        assert (task_dir / internal.CABLE_NML).exists()
        assert (task_dir / internal.CABLE_VEGETATION_NML).exists()
        assert (task_dir / internal.CABLE_SOIL_NML).exists()
        assert (task_dir / internal.CABLE_EXE).exists()


class TestCleanTask:
    """Tests for `FluxsiteTask.clean_task()`."""

    @pytest.fixture(autouse=True)
    def _setup(self, task):
        """Setup precondition for `FluxsiteTask.clean_task()`."""
        task_dir = internal.FLUXSITE_DIRS["TASKS"] / task.get_task_name()
        task_dir.mkdir(parents=True)
        (task_dir / internal.CABLE_NML).touch()
        (task_dir / internal.CABLE_VEGETATION_NML).touch()
        (task_dir / internal.CABLE_SOIL_NML).touch()
        (task_dir / internal.CABLE_EXE).touch()

        internal.FLUXSITE_DIRS["OUTPUT"].mkdir(parents=True)
        (internal.FLUXSITE_DIRS["OUTPUT"] / task.get_output_filename()).touch()

        internal.FLUXSITE_DIRS["LOG"].mkdir(parents=True)
        (internal.FLUXSITE_DIRS["LOG"] / task.get_log_filename()).touch()

    def test_clean_files(self, task):
        """Success case: clean files produced from run."""
        task_dir = internal.FLUXSITE_DIRS["TASKS"] / task.get_task_name()
        task.clean_task()
        assert not (task_dir / internal.CABLE_NML).exists()
        assert not (task_dir / internal.CABLE_VEGETATION_NML).exists()
        assert not (task_dir / internal.CABLE_SOIL_NML).exists()
        assert not (task_dir / internal.CABLE_EXE).exists()
        assert not (
            internal.FLUXSITE_DIRS["OUTPUT"] / task.get_output_filename()
        ).exists()
        assert not (internal.FLUXSITE_DIRS["LOG"] / task.get_log_filename()).exists()


class TestSetupTask:
    """Tests for `FluxsiteTask.setup_task()`."""

    @pytest.fixture(autouse=True)
    def _setup(self, task):
        """Setup precondition for `FluxsiteTask.setup_task()`."""
        (internal.NAMELIST_DIR).mkdir()
        (internal.NAMELIST_DIR / internal.CABLE_NML).touch()
        (internal.NAMELIST_DIR / internal.CABLE_SOIL_NML).touch()
        (internal.NAMELIST_DIR / internal.CABLE_VEGETATION_NML).touch()

        task_name = task.get_task_name()
        (internal.FLUXSITE_DIRS["TASKS"] / task_name).mkdir(parents=True)
        (internal.FLUXSITE_DIRS["OUTPUT"]).mkdir(parents=True)
        (internal.FLUXSITE_DIRS["LOG"]).mkdir(parents=True)

        exe_build_dir = internal.SRC_DIR / "test-branch" / "bin"
        exe_build_dir.mkdir(parents=True)
        (exe_build_dir / internal.CABLE_EXE).touch()

    def test_all_settings_are_patched_into_namelist_file(self, task):
        """Success case: test all settings are patched into task namelist file."""
        task.setup_task()
        task_dir = internal.FLUXSITE_DIRS["TASKS"] / task.get_task_name()
        res_nml = f90nml.read(str(task_dir / internal.CABLE_NML))
        assert res_nml["cable"] == {
            "filename": {
                "met": str(internal.MET_DIR / "forcing-file.nc"),
                "out": str(
                    (
                        internal.FLUXSITE_DIRS["OUTPUT"] / task.get_output_filename()
                    ).absolute()
                ),
                "log": str(
                    (internal.FLUXSITE_DIRS["LOG"] / task.get_log_filename()).absolute()
                ),
                "restart_out": " ",
                "type": str(internal.GRID_FILE.absolute()),
            },
            "output": {"restart": False},
            "fixedco2": internal.CABLE_FIXED_CO2_CONC,
            "spinup": False,
            "some_setting": True,
            "some_branch_specific_setting": True,
        }


class TestRunCable:
    """Tests for `FluxsiteTask.run_cable()`."""

    @pytest.fixture(autouse=True)
    def _setup(self, task):
        """Setup precondition for `FluxsiteTask.run_cable()`."""
        task_dir = internal.FLUXSITE_DIRS["TASKS"] / task.get_task_name()
        task_dir.mkdir(parents=True)

    def test_cable_execution(self, task, mock_subprocess_handler):
        """Success case: run CABLE executable in subprocess."""
        task_dir = internal.FLUXSITE_DIRS["TASKS"] / task.get_task_name()
        task.run_cable()
        assert (
            f"./{internal.CABLE_EXE} {internal.CABLE_NML}"
            in mock_subprocess_handler.commands
        )
        assert (task_dir / internal.CABLE_STDOUT_FILENAME).exists()

    def test_cable_error_exception(self, task, mock_subprocess_handler):
        """Failure case: raise CableError on subprocess non-zero exit code."""
        mock_subprocess_handler.error_on_call = True
        with pytest.raises(CableError):
            task.run_cable()


class TestAddProvenanceInfo:
    """Tests for `FluxsiteTask.add_provenance_info()`."""

    @pytest.fixture()
    def nml(self):
        """Return a namelist dictionary used for testing."""
        return {
            "cable": {
                "filename": {"met": "/path/to/met/file", "foo": 123},
                "bar": True,
            }
        }

    @pytest.fixture()
    def nc_output_path(self, task):
        """Create and return a netcdf output file as if CABLE had just been run.

        Return value is the path to the file.
        """
        _nc_output_path = internal.FLUXSITE_DIRS["OUTPUT"] / task.get_output_filename()
        netCDF4.Dataset(_nc_output_path, "w")
        return _nc_output_path

    @pytest.fixture(autouse=True)
    def _setup(self, task, nml):
        """Setup precondition for `FluxsiteTask.add_provenance_info()`."""
        task_dir = internal.FLUXSITE_DIRS["TASKS"] / task.get_task_name()
        task_dir.mkdir(parents=True)
        fluxsite_output_dir = internal.FLUXSITE_DIRS["OUTPUT"]
        fluxsite_output_dir.mkdir()

        # Create mock namelist file in task directory:
        f90nml.write(nml, task_dir / internal.CABLE_NML)

    def test_netcdf_global_attributes(self, task, nc_output_path, mock_repo, nml):
        """Success case: add global attributes to netcdf file."""
        task.add_provenance_info()
        with netCDF4.Dataset(str(nc_output_path), "r") as nc_output:
            atts = vars(nc_output)
            assert atts["cable_branch"] == mock_repo.branch
            assert atts["svn_revision_number"] == mock_repo.revision
            assert atts["benchcab_version"] == __version__
            assert atts[r"filename%met"] == nml["cable"]["filename"]["met"]
            assert atts[r"filename%foo"] == nml["cable"]["filename"]["foo"]
            assert atts[r"bar"] == ".true."


class TestGetFluxsiteTasks:
    """Tests for `get_fluxsite_tasks()`."""

    @pytest.fixture()
    def models(self, mock_repo):
        """Return a list of `Model` instances used for testing."""
        return [Model(repo=mock_repo, model_id=id) for id in range(2)]

    @pytest.fixture()
    def met_forcings(self):
        """Return a list of forcing file names used for testing."""
        return ["foo", "bar"]

    @pytest.fixture()
    def science_configurations(self, config):
        """Return a list of science configurations used for testing."""
        return config["science_configurations"]

    def test_task_product_across_branches_forcings_and_configurations(
        self, models, met_forcings, science_configurations
    ):
        """Success case: test task product across branches, forcings and configurations."""
        tasks = get_fluxsite_tasks(
            models=models,
            science_configurations=science_configurations,
            fluxsite_forcing_file_names=met_forcings,
        )
        assert [
            (task.model, task.met_forcing_file, task.sci_config) for task in tasks
        ] == [
            (models[0], met_forcings[0], science_configurations[0]),
            (models[0], met_forcings[0], science_configurations[1]),
            (models[0], met_forcings[1], science_configurations[0]),
            (models[0], met_forcings[1], science_configurations[1]),
            (models[1], met_forcings[0], science_configurations[0]),
            (models[1], met_forcings[0], science_configurations[1]),
            (models[1], met_forcings[1], science_configurations[0]),
            (models[1], met_forcings[1], science_configurations[1]),
        ]


class TestGetFluxsiteComparisons:
    """Tests for `get_fluxsite_comparisons()`."""

    def test_comparisons_for_two_branches_with_two_tasks(self, mock_repo):
        """Success case: comparisons for two branches with two tasks."""
        tasks = [
            FluxsiteTask(
                model=Model(repo=mock_repo, model_id=model_id),
                met_forcing_file="foo.nc",
                sci_config={"foo": "bar"},
                sci_conf_id=0,
            )
            for model_id in range(2)
        ]
        comparisons = get_fluxsite_comparisons(tasks)
        n_models, n_science_configurations, n_met_forcings = 2, 1, 1
        assert (
            len(comparisons)
            == math.comb(n_models, 2) * n_science_configurations * n_met_forcings
        )
        assert comparisons[0].files == (
            internal.FLUXSITE_DIRS["OUTPUT"] / tasks[0].get_output_filename(),
            internal.FLUXSITE_DIRS["OUTPUT"] / tasks[1].get_output_filename(),
        )
        assert comparisons[0].task_name == "foo_S0_R0_R1"

    def test_comparisons_for_three_branches_with_three_tasks(self, mock_repo):
        """Success case: comparisons for three branches with three tasks."""
        tasks = [
            FluxsiteTask(
                model=Model(repo=mock_repo, model_id=model_id),
                met_forcing_file="foo.nc",
                sci_config={"foo": "bar"},
                sci_conf_id=0,
            )
            for model_id in range(3)
        ]
        comparisons = get_fluxsite_comparisons(tasks)
        n_models, n_science_configurations, n_met_forcings = 3, 1, 1
        assert (
            len(comparisons)
            == math.comb(n_models, 2) * n_science_configurations * n_met_forcings
        )
        assert comparisons[0].files == (
            internal.FLUXSITE_DIRS["OUTPUT"] / tasks[0].get_output_filename(),
            internal.FLUXSITE_DIRS["OUTPUT"] / tasks[1].get_output_filename(),
        )
        assert comparisons[1].files == (
            internal.FLUXSITE_DIRS["OUTPUT"] / tasks[0].get_output_filename(),
            internal.FLUXSITE_DIRS["OUTPUT"] / tasks[2].get_output_filename(),
        )
        assert comparisons[2].files == (
            internal.FLUXSITE_DIRS["OUTPUT"] / tasks[1].get_output_filename(),
            internal.FLUXSITE_DIRS["OUTPUT"] / tasks[2].get_output_filename(),
        )
        assert comparisons[0].task_name == "foo_S0_R0_R1"
        assert comparisons[1].task_name == "foo_S0_R0_R2"
        assert comparisons[2].task_name == "foo_S0_R1_R2"


class TestGetComparisonName:
    """Tests for `get_comparison_name()`."""

    def test_comparison_name_convention(self, mock_repo):
        """Success case: check comparison name convention."""
        assert (
            get_comparison_name(
                Model(repo=mock_repo, model_id=0),
                Model(repo=mock_repo, model_id=1),
                met_forcing_file="foo.nc",
                sci_conf_id=0,
            )
            == "foo_S0_R0_R1"
        )
