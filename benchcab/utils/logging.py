# Copyright 2022 ACCESS-NRI and contributors. See the top-level COPYRIGHT file for details.
# SPDX-License-Identifier: Apache-2.0

"""Contains helper functions for logging."""

from pathlib import Path


def next_path(path: Path, path_pattern: str, sep: str = "-"):
    """Finds the next free path in a sequentially named list of
    files with the following pattern in the `path` directory:

    path_pattern = 'file{sep}*.suf':

    file-1.txt
    file-2.txt
    file-3.txt
    """

    loc_pattern = Path(path_pattern)
    new_file_index = 1
    common_filename, _ = loc_pattern.stem.split(sep)

    pattern_files_sorted = sorted(path.glob(path_pattern))
    if pattern_files_sorted != []:
        common_filename, last_file_index = pattern_files_sorted[-1].stem.split(sep)
        new_file_index = int(last_file_index) + 1

    return f"{common_filename}{sep}{new_file_index}{loc_pattern.suffix}"
