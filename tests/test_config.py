"""`pytest` tests for config.py."""

import os
from contextlib import nullcontext as does_not_raise
from pathlib import Path
from pprint import pformat
from unittest import mock

import pytest

import benchcab.config as bc
import benchcab.internal as bi
import benchcab.utils as bu
from benchcab import internal

NO_OPTIONAL_CONFIG_PROJECT = "xp65"
OPTIONAL_CONFIG_PROJECT = "ks32"


# Temporarily set $PROJECT for testing module
@pytest.fixture(autouse=True)
def _set_project_env_variable(monkeypatch):
    # Clear existing environment variables first
    with mock.patch.dict(os.environ, clear=True):
        monkeypatch.setenv("PROJECT", OPTIONAL_CONFIG_PROJECT)
        yield


@pytest.fixture()
def config_str(request) -> str:
    """Provide relative YAML path string of data files."""
    return f"test/{request.param}"


@pytest.fixture()
def config_path(config_str: str) -> Path:
    """Provide absolute YAML Path object of data files."""
    return bu.get_installed_root() / "data" / config_str


@pytest.fixture()
def empty_config() -> dict:
    """Empty dict Configuration."""
    return {}


@pytest.fixture()
def no_optional_config() -> dict:
    """Config with no optional parameters.

    Expected value after reading from config-basic.yml
    """
    return {
        "modules": ["intel-compiler/2021.1.1", "netcdf/4.7.4", "openmpi/4.1.0"],
        "realisations": [
            {"repo": {"svn": {"branch_path": "trunk"}}},
            {
                "repo": {
                    "svn": {"branch_path": "branches/Users/ccc561/v3.0-YP-changes"}
                },
            },
        ],
    }


@pytest.fixture()
def all_optional_default_config(no_optional_config) -> dict:
    """Populate all keys in config with default optional values.

    Expected value after reading from config-basic.yml
    """
    config = no_optional_config | {
        "project": OPTIONAL_CONFIG_PROJECT,
        "fluxsite": {
            "experiment": bi.FLUXSITE_DEFAULT_EXPERIMENT,
            "multiprocess": bi.FLUXSITE_DEFAULT_MULTIPROCESS,
            "pbs": bi.FLUXSITE_DEFAULT_PBS,
            "meorg_model_output_id": bi.FLUXSITE_DEFAULT_MEORG_MODEL_OUTPUT_ID,
        },
        "science_configurations": bi.DEFAULT_SCIENCE_CONFIGURATIONS,
        "spatial": {
            "payu": {"config": {}, "args": None},
            "met_forcings": internal.SPATIAL_DEFAULT_MET_FORCINGS,
        },
        "codecov": False,
    }
    for c_r in config["realisations"]:
        c_r["name"] = None

    return config


@pytest.fixture()
def all_optional_custom_config(no_optional_config) -> dict:
    """Populate all keys in config with custom optional values.

    Expected value after reading from config-optional.yml
    """
    config = no_optional_config | {
        "project": NO_OPTIONAL_CONFIG_PROJECT,
        "fluxsite": {
            "experiment": "AU-Tum",
            "multiprocess": False,
            "pbs": {
                "ncpus": 6,
                "mem": "10GB",
                "walltime": "10:00:00",
                "storage": ["scratch/$PROJECT"],
            },
            "meorg_model_output_id": False,
        },
        "science_configurations": [
            {
                "cable": {
                    "cable_user": {"FWSOIL_SWITCH": "test_fw", "GS_SWITCH": "test_gs"}
                }
            }
        ],
        "spatial": {
            "payu": {"config": {"walltime": "1:00:00"}, "args": "-n 2"},
            "met_forcings": {
                "crujra_access": "https://github.com/CABLE-LSM/cable_example.git"
            },
        },
        "codecov": True,
    }
    branch_names = ["svn_trunk", "git_branch"]

    for c_r, b_n in zip(config["realisations"], branch_names):
        c_r["name"] = b_n

    return config


@pytest.mark.parametrize(
    ("config_str", "output_config", "pytest_error"),
    [
        ("config-basic.yml", "no_optional_config", does_not_raise()),
        ("config-optional.yml", "all_optional_custom_config", does_not_raise()),
        ("config-missing.yml", "empty_config", pytest.raises(FileNotFoundError)),
    ],
    indirect=["config_str"],
)
def test_read_config_file(config_path, output_config, pytest_error, request):
    """Test reading config for a file that may/may not exist."""
    with pytest_error:
        config = bc.read_config_file(config_path)
        assert pformat(config) == pformat(request.getfixturevalue(output_config))


@pytest.mark.parametrize(
    ("config_str", "pytest_error"),
    [
        ("config-basic.yml", does_not_raise()),
        ("config-optional.yml", does_not_raise()),
        ("config-invalid.yml", pytest.raises(bc.ConfigValidationError)),
    ],
    indirect=["config_str"],
)
def test_validate_config(config_str, pytest_error):
    """Test schema for a valid/invalid config file."""
    with pytest_error:
        config = bu.load_package_data(config_str)
        assert bc.validate_config(config)


class TestReadOptionalKey:
    """Tests related to adding optional keys in config."""

    @pytest.fixture()
    def all_optional_default_config_no_project(
        self, all_optional_default_config
    ) -> dict:
        """Set project keyword to None."""
        return all_optional_default_config | {"project": None}

    @pytest.mark.parametrize(
        ("input_config", "output_config"),
        [
            ("no_optional_config", "all_optional_default_config"),
            ("all_optional_default_config", "all_optional_default_config"),
            ("all_optional_custom_config", "all_optional_custom_config"),
        ],
    )
    def test_read_optional_key_add_data(self, input_config, output_config, request):
        """Test default key-values are added if not provided by config.yaml, and existing keys stay intact."""
        config = request.getfixturevalue(input_config)
        bc.read_optional_key(config)
        assert pformat(config) == pformat(request.getfixturevalue(output_config))

    def test_no_project_name(
        self, no_optional_config, all_optional_default_config_no_project, monkeypatch
    ):
        """If project key and $PROJECT are not provided, then raise error."""
        monkeypatch.delenv("PROJECT")
        bc.read_optional_key(no_optional_config)
        assert pformat(no_optional_config) == pformat(
            all_optional_default_config_no_project
        )


@pytest.mark.parametrize(
    ("config_str", "output_config"),
    [
        ("config-basic.yml", "all_optional_default_config"),
        ("config-optional.yml", "all_optional_custom_config"),
    ],
    indirect=["config_str"],
)
def test_read_config(config_path, output_config, request):
    """Test overall behaviour of read_config."""
    config = bc.read_config(config_path)
    assert pformat(config) == pformat(request.getfixturevalue(output_config))
