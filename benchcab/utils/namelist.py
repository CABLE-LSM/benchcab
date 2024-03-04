# Copyright 2022 ACCESS-NRI and contributors. See the top-level COPYRIGHT file for details.
# SPDX-License-Identifier: Apache-2.0

"""Contains utility functions for manipulating Fortran namelist files."""

from pathlib import Path

import f90nml

from benchcab.utils.dict import deep_del, deep_update


def patch_namelist(nml_path: Path, patch: dict):
    """Writes a namelist patch specified by `patch` to `nml_path`.

    The `patch` dictionary must comply with the `f90nml` api.
    """
    if not nml_path.exists():
        f90nml.write(patch, nml_path)
        return

    nml = f90nml.read(nml_path)
    f90nml.write(deep_update(nml, patch), nml_path, force=True)


def patch_remove_namelist(nml_path: Path, patch_remove: dict):
    """Removes a subset of namelist parameters specified by `patch_remove` from `nml_path`.

    The `patch_remove` dictionary must comply with the `f90nml` api.
    """
    nml = f90nml.read(nml_path)
    try:
        f90nml.write(deep_del(nml, patch_remove), nml_path, force=True)
    except KeyError as exc:
        msg = f"Namelist parameters specified in `patch_remove` do not exist in {nml_path.name}."
        raise KeyError(msg) from exc
