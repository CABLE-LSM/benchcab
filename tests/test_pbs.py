"""`pytest` tests for `utils/pbs.py`."""

from benchcab import internal
from benchcab.utils import load_package_data
from benchcab.utils.pbs import render_job_script


class TestRenderJobScript:
    """Tests for `render_job_script()`."""

    def test_default_job_script(self):
        """Success case: test default job script generated is correct."""
        assert render_job_script(
            project="tm70",
            config_path="/path/to/config.yaml",
            pbs_config=internal.FLUXSITE_DEFAULT_PBS,
            benchcab_path="/absolute/path/to/benchcab",
        ) == load_package_data("test/pbs_jobscript_default.sh")

    def test_verbose_flag_added_to_command_line_arguments(self):
        """Success case: test verbose flag is added to command line arguments."""
        assert render_job_script(
            project="tm70",
            config_path="/path/to/config.yaml",
            pbs_config=internal.FLUXSITE_DEFAULT_PBS,
            verbose=True,
            benchcab_path="/absolute/path/to/benchcab",
        ) == load_package_data("test/pbs_jobscript_verbose.sh")

    def test_skip_optional(self):
        """Success case: skip optional steps."""
        assert render_job_script(
            project="tm70",
            config_path="/path/to/config.yaml",
            pbs_config=internal.FLUXSITE_DEFAULT_PBS,
            skip_bitwise_cmp=True,
            benchcab_path="/absolute/path/to/benchcab",
        ) == load_package_data("test/pbs_jobscript_skip_optional.sh")

    def test_no_skip_coverage_step(self):
        """Success case: not skip coverage step."""
        assert render_job_script(
            project="tm70",
            config_path="/path/to/config.yaml",
            pbs_config=internal.FLUXSITE_DEFAULT_PBS,
            skip_codecov=False,
            benchcab_path="/absolute/path/to/benchcab",
        ) == load_package_data("test/pbs_jobscript_no_skip_codecov.sh")
