# Copyright 2022 ACCESS-NRI and contributors. See the top-level COPYRIGHT file for details.
# SPDX-License-Identifier: Apache-2.0

"""A module containing all *_config() functions."""

from pathlib import Path
import yaml

from benchcab import internal


def check_config(config: dict):
    """Performs input validation on config file.

    If the config is invalid, an exception is raised. Otherwise, do nothing.
    """

    if any(key not in config for key in internal.CONFIG_REQUIRED_KEYS):
        raise ValueError(
            "Keys are missing from the config file: "
            + ", ".join(
                key for key in internal.CONFIG_REQUIRED_KEYS if key not in config
            )
        )

    if not isinstance(config["project"], str):
        raise TypeError("The 'project' key must be a string.")

    if not isinstance(config["modules"], list):
        raise TypeError("The 'modules' key must be a list.")

    if not isinstance(config["experiment"], str):
        raise TypeError("The 'experiment' key must be a string.")

    # the "science_configurations" key is optional
    if "science_configurations" in config:
        if not isinstance(config["science_configurations"], list):
            raise TypeError("The 'science_configurations' key must be a list.")
        if config["science_configurations"] == []:
            raise ValueError("The 'science_configurations' key cannot be empty.")
        if not all(
            isinstance(value, dict) for value in config["science_configurations"]
        ):
            raise TypeError(
                "Science config settings must be specified using a dictionary "
                "that is compatible with the f90nml python package."
            )

    # the "fluxsite" key is optional
    if "fluxsite" in config:
        if not isinstance(config["fluxsite"], dict):
            raise TypeError("The 'fluxsite' key must be a dictionary.")
        # the "pbs" key is optional
        if "pbs" in config["fluxsite"]:
            if not isinstance(config["fluxsite"]["pbs"], dict):
                raise TypeError("The 'pbs' key must be a dictionary.")
            # the "ncpus" key is optional
            if "ncpus" in config["fluxsite"]["pbs"] and not isinstance(
                config["fluxsite"]["pbs"]["ncpus"], int
            ):
                raise TypeError("The 'ncpus' key must be an integer.")
            # the "mem" key is optional
            if "mem" in config["fluxsite"]["pbs"] and not isinstance(
                config["fluxsite"]["pbs"]["mem"], str
            ):
                raise TypeError("The 'mem' key must be a string.")
            # the "walltime" key is optional
            if "walltime" in config["fluxsite"]["pbs"] and not isinstance(
                config["fluxsite"]["pbs"]["walltime"], str
            ):
                raise TypeError("The 'walltime' key must be a string.")
            # the "storage" key is optional
            if "storage" in config["fluxsite"]["pbs"]:
                if not isinstance(config["fluxsite"]["pbs"]["storage"], list) or any(
                    not isinstance(val, str)
                    for val in config["fluxsite"]["pbs"]["storage"]
                ):
                    raise TypeError("The 'storage' key must be a list of strings.")
        # the "multiprocessing" key is optional
        if "multiprocessing" in config["fluxsite"] and not isinstance(
            config["fluxsite"]["multiprocessing"], bool
        ):
            raise TypeError("The 'multiprocessing' key must be a boolean.")

    valid_experiments = (
        list(internal.MEORG_EXPERIMENTS) + internal.MEORG_EXPERIMENTS["five-site-test"]
    )
    if config["experiment"] not in valid_experiments:
        raise ValueError(
            "The 'experiment' key is invalid.\n"
            "Valid experiments are: " + ", ".join(valid_experiments)
        )

    if not isinstance(config["realisations"], list):
        raise TypeError("The 'realisations' key must be a list.")

    if config["realisations"] == []:
        raise ValueError("The 'realisations' key cannot be empty.")

    for branch_id, branch_config in enumerate(config["realisations"]):
        if not isinstance(branch_config, dict):
            raise TypeError(f"Realisation '{branch_id}' must be a dictionary object.")
        if "path" not in branch_config:
            raise ValueError(
                f"Realisation '{branch_id}' must specify the `path` field."
            )
        if not isinstance(branch_config["path"], str):
            raise TypeError(
                f"The 'path' field in realisation '{branch_id}' must be a string."
            )
        # the "name" key is optional
        if "name" in branch_config and not isinstance(branch_config["name"], str):
            raise TypeError(
                f"The 'name' field in realisation '{branch_id}' must be a string."
            )
        # the "revision" key is optional
        if "revision" in branch_config and not isinstance(
            branch_config["revision"], int
        ):
            raise TypeError(
                f"The 'revision' field in realisation '{branch_id}' must be an "
                "integer."
            )
        # the "patch" key is optional
        if "patch" in branch_config and not isinstance(branch_config["patch"], dict):
            raise TypeError(
                f"The 'patch' field in realisation '{branch_id}' must be a "
                "dictionary that is compatible with the f90nml python package."
            )
        # the "patch_remove" key is optional
        if "patch_remove" in branch_config and not isinstance(
            branch_config["patch_remove"], dict
        ):
            raise TypeError(
                f"The 'patch_remove' field in realisation '{branch_id}' must be a "
                "dictionary that is compatible with the f90nml python package."
            )
        # the "build_script" key is optional
        if "build_script" in branch_config and not isinstance(
            branch_config["build_script"], str
        ):
            raise TypeError(
                f"The 'build_script' field in realisation '{branch_id}' must be a "
                "string."
            )


def read_config(config_path: str) -> dict:
    """Reads the config file and returns a dictionary containing the configurations."""

    with open(Path(config_path), "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    check_config(config)

    return config
