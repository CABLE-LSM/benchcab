# Copyright 2022 ACCESS-NRI and contributors. See the top-level COPYRIGHT file for details.
# SPDX-License-Identifier: Apache-2.0

# ruff: noqa: PTH118

"""Top-level utilities."""
import json
import logging
import os
import pkgutil
import sys
from importlib import resources
from pathlib import Path
from typing import Union

import yaml
from jinja2 import BaseLoader, Environment

# List of one-argument decoding functions.
PACKAGE_DATA_DECODERS = dict(json=json.loads, yml=yaml.safe_load)


def get_installed_root() -> Path:
    """Get the installed root of the benchcab installation.

    Returns
    -------
    Path
        Path to the installed root.

    """
    return Path(resources.files("benchcab"))


def load_package_data(filename: str) -> Union[str, dict]:
    """Load data out of the installed package data directory.

    Parameters
    ----------
    filename : str
        Filename of the file to load out of the data directory.

    Returns
    -------
    str or dict
        String or dictionary, depending on format of data read.

    """
    # Work out the encoding of requested file.
    ext = filename.split(".")[-1]

    # Alias yaml and yml.
    ext = ext if ext != "yaml" else "yml"

    # Extract from the installations data directory.
    raw = pkgutil.get_data("benchcab", os.path.join("data", filename)).decode("utf-8")

    # If there is no explicit decoder, just return the raw text
    if ext not in PACKAGE_DATA_DECODERS.keys():
        return raw

    # Decode and return.
    return PACKAGE_DATA_DECODERS[ext](raw)


def interpolate_string_template(template, **kwargs):
    """Interpolate a string template with kwargs.

    Parameters
    ----------
    template : str
        Template string to interpolate over.
    **kwargs :
        Keyword arguments to interpolate into the string.

    Returns
    -------
    str
        Interpolated string.

    """
    _template = Environment(loader=BaseLoader()).from_string(template)
    return _template.render(**kwargs)


def interpolate_file_template(template_file, **kwargs):
    """Interpolate kwargs directly into a j2 template file from the data directory.

    Parameters
    ----------
    template_file : str
        Filepath slug in the benchcab data directory.
    **kwargs :
        Keyword arguments to interpolate into the file.

    Returns
    -------
    str
        Interpolated template string.

    """
    template = load_package_data(template_file)
    return interpolate_string_template(template, **kwargs)


def get_logger(name="benchcab", level="debug"):
    """Get a logger instance.

    Parameters
    ----------
    name : str, optional
        Name, by default 'benchcab'
    level : str, optional
        Level, by default 'debug'

    Returns
    -------
    logging.Logger
        A logger instance guaranteed to be singleton if called with the same params.

    """
    # Get or create a logger
    logger = logging.getLogger(name)

    # Workaround for native singleton property.
    # NOTE: This will ignore the provided level and give you whatever was first set.
    if logger.level != logging.NOTSET:
        return logger

    # Set the level
    level = getattr(logging, level.upper())
    logger.setLevel(level)

    # Create the formatter
    log_format = (
        "%(asctime)s - %(levelname)s - %(module)s.%(filename)s:%(lineno)s - %(message)s"
    )
    formatter = logging.Formatter(log_format)

    # Create/set the handler to point to stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def is_verbose():
    """Return True if verbose output is enabled, False otherwise."""
    return get_logger().getEffectiveLevel() == logging.DEBUG
