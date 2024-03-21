# Copyright 2022 ACCESS-NRI and contributors. See the top-level COPYRIGHT file for details.
# SPDX-License-Identifier: Apache-2.0

"""A module containing all *_config() functions."""
import os
from pathlib import Path

import yaml
from cerberus import Validator

import benchcab.utils as bu
from benchcab import internal


class ConfigValidationError(Exception):
    """When config doesn't match with the defined schema."""

    def __init__(self, validator: Validator):
        """.

        Parameters
        ----------
        validator: cerberus.Validator
            A validation object that has been used and has the errors attribute.

        """
        # Nicely format the errors.
        errors = [f"{k} = {v}" for k, v in validator.errors.items()]

        # Assemble the error message and
        msg = "\n\nThe following errors were raised when validating the config file.\n"
        msg += "\n".join(errors) + "\n"

        # Raise to super.
        super().__init__(msg)


def validate_config(config: dict) -> bool:
    """Validate the configuration dictionary.

    Parameters
    ----------
    config : dict
        Dictionary of configuration loaded from the yaml file.

    Returns
    -------
    bool
        True if valid, exception raised otherwise.

    Raises
    ------
    ConfigValidationError
        Raised when the configuration file fails validation.

    """
    # Load the schema
    schema = bu.load_package_data("config-schema.yml")

    # Create a validator
    v = Validator(schema)

    # Validate
    is_valid = v.validate(config)

    # Valid
    if is_valid:
        return True

    # Invalid
    raise ConfigValidationError(v)


def read_optional_key(config: dict):
    """Fills all optional keys in config if not already defined.

    The default values for most optional keys are loaded from `internal.py`
    Note: We need to ensure that the `name` key for realisations exists for
    other modules, but it doesn't have a default value.  So we set it to
    `None` by default.

    Parameters
    ----------
    config : dict
        The configuration file with with/without optional keys

    """
    if "project" not in config:
        config["project"] = os.environ.get("PROJECT", None)

    if "realisations" in config:
        for r in config["realisations"]:
            r["name"] = r.get("name")

    config["science_configurations"] = config.get(
        "science_configurations", internal.DEFAULT_SCIENCE_CONFIGURATIONS
    )

    # Default values for spatial
    config["spatial"] = config.get("spatial", {})

    config["spatial"]["met_forcings"] = config["spatial"].get(
        "met_forcings", internal.SPATIAL_DEFAULT_MET_FORCINGS
    )

    config["spatial"]["payu"] = config["spatial"].get("payu", {})
    config["spatial"]["payu"]["config"] = config["spatial"]["payu"].get("config", {})
    config["spatial"]["payu"]["args"] = config["spatial"]["payu"].get("args")

    # Default values for fluxsite
    config["fluxsite"] = config.get("fluxsite", {})

    config["fluxsite"]["multiprocess"] = config["fluxsite"].get(
        "multiprocess", internal.FLUXSITE_DEFAULT_MULTIPROCESS
    )
    config["fluxsite"]["experiment"] = config["fluxsite"].get(
        "experiment", internal.FLUXSITE_DEFAULT_EXPERIMENT
    )
    config["fluxsite"]["pbs"] = internal.FLUXSITE_DEFAULT_PBS | config["fluxsite"].get(
        "pbs", {}
    )


def read_config_file(config_path: str) -> dict:
    """Load the config file in a dict.

    Parameters
    ----------
    config_path : str
        Path to the configuration file.

    Returns
    -------
    dict
        Configuration dict

    """
    # Load the configuration file.
    with Path.open(Path(config_path), "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    return config


def read_config(config_path: str) -> dict:
    """Reads the config file and returns a dictionary containing the configurations.

    Parameters
    ----------
    config_path : str
        Path to the configuration file.

    Returns
    -------
    dict
        Validated configuration dict, with default optional parameters if not specified in file.

    Raises
    ------
    ConfigValidationError
        Raised when the configuration file fails validation.

    """
    # Read configuration file
    config = read_config_file(config_path)
    # Populate configuration dict with optional keys
    read_optional_key(config)
    # Validate and return.
    validate_config(config)
    return config
