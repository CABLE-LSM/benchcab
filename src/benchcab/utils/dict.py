# Copyright 2022 ACCESS-NRI and contributors. See the top-level COPYRIGHT file for details.
# SPDX-License-Identifier: Apache-2.0

"""Utility functions for manipulating nested dictionaries."""

from typing import Any, Dict, TypeVar

# fmt: off
# ======================================================
# Copyright (c) 2017 - 2022 Samuel Colvin and other contributors
# from https://github.com/pydantic/pydantic/blob/fd2991fe6a73819b48c906e3c3274e8e47d0f761/pydantic/utils.py#L200

KeyType = TypeVar('KeyType')


def deep_update(mapping: Dict[KeyType, Any], *updating_mappings: Dict[KeyType, Any]) -> Dict[KeyType, Any]: # noqa
    updated_mapping = mapping.copy()
    for updating_mapping in updating_mappings:
        for k, v in updating_mapping.items():
            if k in updated_mapping and isinstance(updated_mapping[k], dict) and isinstance(v, dict):
                updated_mapping[k] = deep_update(updated_mapping[k], v)
            else:
                updated_mapping[k] = v
    return updated_mapping

# ======================================================
# fmt: on


def deep_del(
    mapping: Dict[KeyType, Any], *updating_mappings: Dict[KeyType, Any]
) -> Dict[KeyType, Any]:
    """Deletes all key-value 'leaf nodes' in `mapping` specified by `updating_mappings`."""
    updated_mapping = mapping.copy()
    for updating_mapping in updating_mappings:
        for key, value in updating_mapping.items():
            if isinstance(updated_mapping[key], dict) and isinstance(value, dict):
                updated_mapping[key] = deep_del(updated_mapping[key], value)
            else:
                del updated_mapping[key]
    return updated_mapping
