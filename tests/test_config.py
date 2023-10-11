"""`pytest` tests for `config.py`.

Note: explicit teardown for generated files and directories are not required as
the working directory used for testing is cleaned up in the `_run_around_tests`
pytest autouse fixture.
"""

from pathlib import Path

import pytest
import yaml

from benchcab import internal
from benchcab.config import check_config, read_config


class TestCheckConfig:
    """Tests for `check_config()`."""

    def test_config_is_valid(self, config):
        """Success case: test barebones config is valid."""
        check_config(config)

    def test_branch_configuration_with_missing_name_key(self, config):
        """Success case: branch configuration with missing name key."""
        config["realisations"][0].pop("name")
        check_config(config)

    def test_branch_configuration_with_missing_revision_key(self, config):
        """Success case: branch configuration with missing revision key."""
        config["realisations"][0].pop("revision")
        check_config(config)

    def test_branch_configuration_with_missing_patch_key(self, config):
        """Success case: branch configuration with missing patch key."""
        config["realisations"][0].pop("patch")
        check_config(config)

    def test_branch_configuration_with_missing_patch_remove_key(self, config):
        """Success case: branch configuration with missing patch_remove key."""
        config["realisations"][0].pop("patch_remove")
        check_config(config)

    def test_config_when_realisations_contains_more_than_two_keys(self, config):
        """Success case: test config when realisations contains more than two keys."""
        config["realisations"].append({"path": "path/to/my_new_branch"})
        check_config(config)

    def test_config_when_realisations_contains_less_than_two_keys(self, config):
        """Success case: test config when realisations contains less than two keys."""
        config["realisations"].pop()
        check_config(config)

    def test_experiment_from_five_site_test(self, config):
        """Success case: test experiment with site id from the five-site-test is valid."""
        config["experiment"] = "AU-Tum"
        check_config(config)

    def test_config_without_science_configurations_is_valid(self, config):
        """Success case: test config without science_configurations is valid."""
        config.pop("science_configurations")
        check_config(config)

    def test_config_without_fluxsite_key_is_valid(self, config):
        """Success case: test config without fluxsite key is valid."""
        config.pop("fluxsite")
        check_config(config)

    def test_config_without_multiprocessing_key_is_valid(self, config):
        """Success case: test config without multiprocessing key is valid."""
        config["fluxsite"].pop("multiprocessing")
        check_config(config)

    def test_config_without_pbs_key_is_valid(self, config):
        """Success case: test config without pbs key is valid."""
        config["fluxsite"].pop("pbs")
        check_config(config)

    def test_config_without_ncpus_key_is_valid(self, config):
        """Success case: test config without ncpus key is valid."""
        config["fluxsite"]["pbs"].pop("ncpus")
        check_config(config)

    def test_config_without_mem_key_is_valid(self, config):
        """Success case: test config without mem key is valid."""
        config["fluxsite"]["pbs"].pop("mem")
        check_config(config)

    def test_config_without_walltime_key_is_valid(self, config):
        """Success case: test config without walltime key is valid."""
        config["fluxsite"]["pbs"].pop("walltime")
        check_config(config)

    def test_config_without_storage_key_is_valid(self, config):
        """Success case: test config without storage key is valid."""
        config["fluxsite"]["pbs"].pop("storage")
        check_config(config)

    def test_missing_required_keys_raises_an_exception(self, config):
        """Failure case: test missing required keys raises an exception."""
        config.pop("project")
        config.pop("experiment")
        with pytest.raises(
            ValueError,
            match="Keys are missing from the config file: project, experiment",
        ):
            check_config(config)

    def test_config_with_empty_realisations_key_raises_an_exception(self, config):
        """Failure case: test config with empty realisations key raises an exception."""
        config["realisations"] = []
        with pytest.raises(ValueError, match="The 'realisations' key cannot be empty."):
            check_config(config)

    def test_config_with_invalid_experiment_key_raises_an_exception(self, config):
        """Failure case: test config with invalid experiment key raises an exception."""
        config["experiment"] = "foo"
        with pytest.raises(
            ValueError,
            match="The 'experiment' key is invalid.\n"
            "Valid experiments are: "
            + ", ".join(
                list(internal.MEORG_EXPERIMENTS)
                + internal.MEORG_EXPERIMENTS["five-site-test"]
            ),
        ):
            check_config(config)

    def test_invlid_experiment_key_raises_exception(self, config):
        """Failure case: test invalid experiment key (not a subset of -site-test)."""
        config["experiment"] = "CH-Dav"
        with pytest.raises(
            ValueError,
            match="The 'experiment' key is invalid.\n"
            "Valid experiments are: "
            + ", ".join(
                list(internal.MEORG_EXPERIMENTS)
                + internal.MEORG_EXPERIMENTS["five-site-test"]
            ),
        ):
            check_config(config)

    def test_missing_path_key_raises_exception(self, config):
        """Failure case: 'path' key is missing in branch configuration."""
        config["realisations"][1].pop("path")
        with pytest.raises(
            ValueError, match="Realisation '1' must specify the `path` field."
        ):
            check_config(config)

    def test_empty_science_configurations_raises_exception(self, config):
        """Failure case: test empty science_configurations key raises an exception."""
        config["science_configurations"] = []
        with pytest.raises(
            ValueError, match="The 'science_configurations' key cannot be empty."
        ):
            check_config(config)

    def test_project_key_type_error(self, config):
        """Failure case: project key is not a string."""
        config["project"] = 123
        with pytest.raises(TypeError, match="The 'project' key must be a string."):
            check_config(config)

    def test_realisations_key_type_error(self, config):
        """Failure case: realisations key is not a list."""
        config["realisations"] = {"foo": "bar"}
        with pytest.raises(TypeError, match="The 'realisations' key must be a list."):
            check_config(config)

    def test_realisations_element_type_error(self, config):
        """Failure case: realisations key is not a list of dict."""
        config["realisations"] = ["foo"]
        with pytest.raises(
            TypeError, match="Realisation '0' must be a dictionary object."
        ):
            check_config(config)

    def test_name_key_type_error(self, config):
        """Failure case: type of name is not a string."""
        config["realisations"][1]["name"] = 1234
        with pytest.raises(
            TypeError, match="The 'name' field in realisation '1' must be a string."
        ):
            check_config(config)

    def test_path_key_type_error(self, config):
        """Failure case: type of path is not a string."""
        config["realisations"][1]["path"] = 1234
        with pytest.raises(
            TypeError, match="The 'path' field in realisation '1' must be a string."
        ):
            check_config(config)

    def test_revision_key_type_error(self, config):
        """Failure case: type of revision key is not an integer."""
        config["realisations"][1]["revision"] = "-1"
        with pytest.raises(
            TypeError,
            match="The 'revision' field in realisation '1' must be an integer.",
        ):
            check_config(config)

    def test_patch_key_type_error(self, config):
        """Failure case: type of patch key is not a dictionary."""
        config["realisations"][1]["patch"] = r"cable_user%ENABLE_SOME_FEATURE = .FALSE."
        with pytest.raises(
            TypeError,
            match="The 'patch' field in realisation '1' must be a dictionary that is "
            "compatible with the f90nml python package.",
        ):
            check_config(config)

    def test_patch_remove_key_type_error(self, config):
        """Failure case: type of patch_remove key is not a dictionary."""
        config["realisations"][1]["patch_remove"] = r"cable_user%ENABLE_SOME_FEATURE"
        with pytest.raises(
            TypeError,
            match="The 'patch_remove' field in realisation '1' must be a dictionary that is "
            "compatible with the f90nml python package.",
        ):
            check_config(config)

    def test_build_script_type_error(self, config):
        """Failure case: type of build_script key is not a string."""
        config["realisations"][1]["build_script"] = ["echo", "hello"]
        with pytest.raises(
            TypeError,
            match="The 'build_script' field in realisation '1' must be a string.",
        ):
            check_config(config)

    def test_modules_key_type_error(self, config):
        """Failure case: modules key is not a list."""
        config["modules"] = "netcdf"
        with pytest.raises(TypeError, match="The 'modules' key must be a list."):
            check_config(config)

    def test_experiment_key_type_error(self, config):
        """Failure case: experiment key is not a string."""
        config["experiment"] = 0
        with pytest.raises(TypeError, match="The 'experiment' key must be a string."):
            check_config(config)

    def test_science_configurations_key_type_error(self, config):
        """Failure case: type of config["science_configurations"] is not a list."""
        config["science_configurations"] = r"cable_user%GS_SWITCH = 'medlyn'"
        with pytest.raises(
            TypeError, match="The 'science_configurations' key must be a list."
        ):
            check_config(config)

    def test_science_configurations_element_type_error(self, config):
        """Failure case: type of config["science_configurations"] is not a list of dict."""
        config["science_configurations"] = [r"cable_user%GS_SWITCH = 'medlyn'"]
        with pytest.raises(
            TypeError,
            match="Science config settings must be specified using a dictionary "
            "that is compatible with the f90nml python package.",
        ):
            check_config(config)

    def test_fluxsite_key_type_error(self, config):
        """Failure case: type of config["fluxsite"] is not a dict."""
        config["fluxsite"] = ["ncpus: 16\nmem: 64GB\n"]
        with pytest.raises(TypeError, match="The 'fluxsite' key must be a dictionary."):
            check_config(config)

    def test_pbs_key_type_error(self, config):
        """Failure case: type of config["pbs"] is not a dict."""
        config["fluxsite"]["pbs"] = "-l ncpus=16"
        with pytest.raises(TypeError, match="The 'pbs' key must be a dictionary."):
            check_config(config)

    def test_ncpus_key_type_error(self, config):
        """Failure case: type of config["pbs"]["ncpus"] is not an int."""
        config["fluxsite"]["pbs"]["ncpus"] = "16"
        with pytest.raises(TypeError, match="The 'ncpus' key must be an integer."):
            check_config(config)

    def test_mem_key_type_error(self, config):
        """Failure case: type of config["pbs"]["mem"] is not a string."""
        config["fluxsite"]["pbs"]["mem"] = 64
        with pytest.raises(TypeError, match="The 'mem' key must be a string."):
            check_config(config)

    def test_walltime_key_type_error(self, config):
        """Failure case: type of config["pbs"]["walltime"] is not a string."""
        config["fluxsite"]["pbs"]["walltime"] = 60
        with pytest.raises(TypeError, match="The 'walltime' key must be a string."):
            check_config(config)

    def test_storage_key_type_error(self, config):
        """Failure case: type of config["pbs"]["storage"] is not a list."""
        config["fluxsite"]["pbs"]["storage"] = "gdata/foo+gdata/bar"
        with pytest.raises(
            TypeError, match="The 'storage' key must be a list of strings."
        ):
            check_config(config)

    def test_storage_element_type_error(self, config):
        """Failure case: type of config["pbs"]["storage"] is not a list of strings."""
        config["fluxsite"]["pbs"]["storage"] = [1, 2, 3]
        with pytest.raises(
            TypeError, match="The 'storage' key must be a list of strings."
        ):
            check_config(config)

    def test_multiprocessing_key_type_error(self, config):
        """Failure case: type of config["multiprocessing"] is not a bool."""
        config["fluxsite"]["multiprocessing"] = 1
        with pytest.raises(
            TypeError, match="The 'multiprocessing' key must be a boolean."
        ):
            check_config(config)


class TestReadConfig:
    """Tests for `read_config()`."""

    def test_read_config(self, config):
        """Success case: write config to file, then read config from file."""
        filename = Path("config-barebones.yaml")

        with filename.open("w", encoding="utf-8") as file:
            yaml.dump(config, file)

        res = read_config(filename)
        filename.unlink()
        assert config == res
