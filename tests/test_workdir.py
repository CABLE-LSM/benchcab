"""`pytest` tests for `workdir.py`.

Note: explicit teardown for generated files and directories are not required as
the working directory used for testing is cleaned up in the `_run_around_tests`
pytest autouse fixture.
"""

from pathlib import Path
from typing import List

import pytest

from benchcab.workdir import (
    clean_realisation_files,
    clean_submission_files,
    setup_fluxsite_directory_tree,
    setup_spatial_directory_tree,
)


class TestSetupFluxsiteDirectoryTree:
    """Tests for `setup_fluxsite_directory_tree()`."""

    @pytest.fixture(autouse=True)
    def fluxsite_directory_list(self):
        """Return the list of work directories we want benchcab to create."""
        return [
            Path("runs", "fluxsite"),
            Path("runs", "fluxsite", "logs"),
            Path("runs", "fluxsite", "outputs"),
            Path("runs", "fluxsite", "tasks"),
            Path("runs", "fluxsite", "analysis"),
            Path("runs", "fluxsite", "analysis", "bitwise-comparisons"),
        ]

    def test_directory_structure_generated(self, fluxsite_directory_list):
        """Success case: generate the full fluxsite directory structure."""
        setup_fluxsite_directory_tree()
        for path in fluxsite_directory_list:
            assert path.exists()


class TestSetupSpatialDirectoryTree:
    """Tests for `setup_spatial_directory_tree()`."""

    @pytest.fixture()
    def spatial_directory_list(self):
        """Return the list of work directories we want benchcab to create."""
        return [
            Path("runs", "spatial"),
            Path("runs", "spatial", "tasks"),
            Path("runs", "payu-laboratory"),
        ]

    def test_directory_structure_generated(self, spatial_directory_list):
        """Success case: generate spatial directory structure."""
        setup_spatial_directory_tree()
        for path in spatial_directory_list:
            assert path.exists()


class TestCleanFiles:
    """Tests for `clean_realisation_files()` and `clean_submission_files()`."""

    # Helper functions
    def _create_files_in_cwd(self, filenames: List[Path]):
        """Given a list of filenames, create files in current working directory."""
        for filename in filenames:
            filename.touch()

    def _check_if_any_files_exist(self, filenames: List[Path]):
        """Given a list of filenames, check if any of them exist w.r.t. current working directory."""
        return any(filename.exists() for filename in filenames)

    @pytest.fixture()
    def src_path(self) -> Path:
        """Mock internal.SRC_DIR."""
        src_path = Path("src")
        src_path.mkdir()
        return src_path

    @pytest.fixture()
    def runs_path(self) -> Path:
        """Mock internal.RUN_DIR."""
        runs_path = Path("runs")
        runs_path.mkdir()
        return runs_path

    @pytest.fixture()
    def state_path(self) -> Path:
        """Mock internal.STATE_DIR."""
        state_path = Path(".state")
        state_path.mkdir()
        return state_path

    @pytest.fixture()
    def pbs_job_files(self) -> List[Path]:
        """Create sample files of the form benchmark_cable_qsub.sh*."""
        pbs_job_files = [
            Path("benchmark_cable_qsub.sh.o21871"),
            Path("benchmark_cable_qsub.sh"),
        ]
        self._create_files_in_cwd(pbs_job_files)
        return pbs_job_files

    @pytest.fixture()
    def local_cable_src_path(self, tmp_path) -> Path:
        """Local sample path for CABLE checkout."""
        # Temporary directory of CABLE unique to test invocation, independent of CWD
        local_cable_src_path = tmp_path / "CABLE"
        local_cable_src_path.mkdir()
        return local_cable_src_path

    @pytest.fixture()
    def src_path_with_local(self, src_path, local_cable_src_path) -> Path:
        """Local path where CABLE checkout is symlinked."""
        cable_symlink = src_path / "cable_local"
        cable_symlink.symlink_to(local_cable_src_path)
        return src_path

    @pytest.fixture()
    def src_path_with_git(self, src_path) -> Path:
        """Local path where CABLE checkout from git is present."""
        cable_git = src_path / "cable_git"
        cable_git.mkdir()
        return src_path

    def test_clean_realisation_files_local(
        self,
        local_cable_src_path: Path,
        src_path_with_local: Path,
    ):
        """Success case: Local realisation files created by benchcab are removed after clean."""
        clean_realisation_files()
        assert local_cable_src_path.exists()
        assert not src_path_with_local.exists()

    def test_clean_realisation_files_git(self, src_path_with_git: Path):
        """Success case: Git realisation files created by benchcab are removed after clean."""
        clean_realisation_files()
        assert not src_path_with_git.exists()

    def test_clean_submission_files(
        self, runs_path, state_path, pbs_job_files: List[Path]
    ):
        """Success case: Submission files created by benchcab are removed after clean."""
        clean_submission_files()
        assert not runs_path.exists()
        assert not state_path.exists()
        assert not self._check_if_any_files_exist(pbs_job_files)
