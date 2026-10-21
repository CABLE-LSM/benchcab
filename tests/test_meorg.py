"""`pytest` tests for `utils/meorg.py`."""

import os
import re
from pathlib import Path

import hpcpy.constants
import pytest
from hpcpy.client.pbs import PBSClient

import benchcab.utils.meorg as bm
from benchcab.config import read_optional_key
from benchcab.utils import load_package_data

FLUXSITE_JOB_ID = "100.gadi-pbs"
OUTPUTS = "runs/fluxsite/outputs"


class InitialisedClient:
    """Stand-in for a `meorg_client` with credentials in `~/.meorg`."""

    def is_initialised(self):
        """Report the client as initialised."""
        return True


@pytest.fixture(autouse=True)
def _pbs(monkeypatch, mock_cwd):
    """Render job scripts for PBS into the test directory, with no shared cache.

    The shared cache points at a missing directory, so the tests give the same
    result on Gadi. Tests that need the shared cache create this directory.
    """
    monkeypatch.setenv("USER", "abc123")
    monkeypatch.setattr(hpcpy.constants, "JOB_SCRIPT_DIR", mock_cwd / "job_scripts")
    monkeypatch.setattr(bm, "get_client", PBSClient)
    monkeypatch.setitem(
        bm.internal.MEORG_ANALYSIS, "shared_cache", str(mock_cwd / "shared-cache")
    )


@pytest.fixture()
def meorg_bin(mock_cwd):
    """Return the path of an empty `meorg` executable."""
    path = mock_cwd / "bin" / "meorg"
    path.parent.mkdir()
    path.touch()
    return path


@pytest.fixture()
def meorg_config(meorg_bin):
    """Return a config with defaults, as `read_config` gives it."""
    return read_optional_key(
        {
            "project": "tm70",
            "modules": [],
            "realisations": [],
            "fluxsite": {"experiment": "AU-Tum"},
            "meorg_output_name": "123-my-branch_A1B2C3",
            "meorg_bin": str(meorg_bin),
        }
    )


def read_job_script(template: str, meorg_bin: Path) -> str:
    """Return the job script rendered from `template`, with fixed paths."""
    (path,) = hpcpy.constants.JOB_SCRIPT_DIR.glob(f"{template}_*")
    return (
        path.read_text()
        .replace(str(meorg_bin), "/opt/benchcab/bin/meorg")
        .replace(str(Path.cwd()), "/work")
    )


class TestGetRunId:
    """Tests for `get_run_id()`."""

    def test_run_id(self, mock_cwd, monkeypatch):
        """Success case: the run id names the experiment, the directory and the UTC time."""
        (mock_cwd / "bench_example").mkdir()
        monkeypatch.chdir(mock_cwd / "bench_example")
        run_id = bm.get_run_id("AU-Tum")
        assert re.fullmatch(r"benchcab-AU-Tum-bench_example-\d{8}T\d{6}Z", run_id)


class TestGetAnalysisCache:
    """Tests for `get_analysis_cache()`."""

    def test_shared_cache(self, mock_cwd):
        """Success case: a writable shared cache is used, with its storage."""
        shared = mock_cwd / "shared-cache"
        shared.mkdir()
        assert bm.get_analysis_cache("tm70") == (str(shared), ["gdata/dm8"])

    @pytest.mark.skipif(os.geteuid() == 0, reason="root can write to any directory")
    def test_shared_cache_not_writable(self, mock_cwd):
        """Success case: without write access, the cache is in the user's scratch."""
        (mock_cwd / "shared-cache").mkdir(mode=0o555)
        assert bm.get_analysis_cache("tm70") == ("/scratch/tm70/abc123/meorg-cache", [])


class TestDoMeorg:
    """Tests for `do_meorg()`."""

    @pytest.fixture(autouse=True)
    def _initialised_client(self, monkeypatch):
        """Use an initialised client and a fixed run id."""
        monkeypatch.setattr(bm, "MeorgClient", InitialisedClient)
        monkeypatch.setattr(
            bm, "get_run_id", lambda experiment: f"benchcab-{experiment}"
        )

    def test_worker_job_script(self, meorg_config, meorg_bin, monkeypatch):
        """Success case: without `enabled`, one upload job is submitted for the worker."""
        # The worker path has no dry run, so `qsub` is mocked
        monkeypatch.setattr(
            PBSClient, "_shell", lambda self, cmd, env=None: "1.gadi-pbs"
        )
        assert bm.do_meorg(meorg_config, OUTPUTS, "")
        assert read_job_script("meorg_jobscript", meorg_bin) == load_package_data(
            "test/meorg_jobscript_worker.sh"
        )

    def test_gadi_job_scripts(self, meorg_config, meorg_bin):
        """Success case: with `enabled`, the inputs, analysis and result jobs are rendered."""
        meorg_config["fluxsite"]["meorg_analysis"]["enabled"] = True
        assert bm.do_meorg(meorg_config, OUTPUTS, "", dry_run=True)
        for template, expected in [
            ("meorg_jobscript", "meorg_jobscript_gadi.sh"),
            ("meorg_analysis_jobscript", "meorg_analysis_jobscript.sh"),
            ("meorg_result_jobscript", "meorg_result_jobscript.sh"),
        ]:
            assert read_job_script(template, meorg_bin) == load_package_data(
                f"test/{expected}"
            )

    def test_gadi_dry_run(self, meorg_config, mock_cwd, caplog):
        """Success case: a dry run reports the three `qsub` commands.

        The jobs are chained with `afterok`. Each job adds the fluxsite storage
        to its own, without duplicates. Only the inputs and analysis jobs read
        the shared cache, so only they get its storage.
        """
        (mock_cwd / "shared-cache").mkdir()
        meorg_config["fluxsite"]["pbs"]["storage"] = ["gdata/ab12", "gdata/vk83"]
        assert bm.do_meorg(
            meorg_config, OUTPUTS, "", FLUXSITE_JOB_ID, gadi=True, dry_run=True
        )
        commands = [
            message.split(": ", 1)[1]
            for message in caplog.messages
            if " job rendered, not submitted: " in message
        ]
        copyq = "gdata/ks32+gdata/xp65+gdata/wd9+gdata/rp23+gdata/ab12+gdata/vk83"
        # The last word of each command is the path of the rendered job script
        assert [cmd.rsplit(" ", 1)[0] for cmd in commands] == [
            f"qsub -W depend=afterok:{FLUXSITE_JOB_ID} -l walltime=01:00:00"
            f" -l storage={copyq}+gdata/dm8",
            "qsub -W depend=afterok:<job 1> -q normal -l walltime=00:30:00"
            " -l storage=gdata/vk83+gdata/dm8+gdata/ab12",
            f"qsub -W depend=afterok:<job 2> -l walltime=01:00:00 -l storage={copyq}",
        ]

    def test_gadi_replaces_files_after_analysis(self, meorg_config, meorg_bin):
        """Success case: only the result job replaces the model output files.

        So if the inputs or analysis job stops, the model output keeps its files.
        """
        bm.do_meorg(meorg_config, OUTPUTS, "", gadi=True, dry_run=True)
        inputs = read_job_script("meorg_jobscript", meorg_bin)
        result = read_job_script("meorg_result_jobscript", meorg_bin)
        assert "file delete_all" not in inputs
        assert (
            result.index("file delete_all")
            < result.index("analysis submit-result")
            < result.index("file upload")
        )
