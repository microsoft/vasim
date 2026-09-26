#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#

"""
Module Name: Perf Event Log File Utility.

Description:
    This module contains a utility function for listing performance event log files within a given directory.
    It scans the directory for CSV files that end with "perf_event_log" in their file name.

Functions:
    list_perf_event_log_files(data_dir: Path):
        Scans the provided `data_dir` for CSV files whose names end with "perf_event_log".
        Returns a list of matching files. If no files are found, prints an error message.

Parameters:
    data_dir (Path):
        The directory path where the CSV files are located.

Returns:
    List[Path]:
        A list of file paths that match the "perf_event_log" pattern. If no files are found, an empty list is returned.
"""

from pathlib import Path


def list_perf_event_log_files(data_dir: Path):
    """
    Scans the provided directory for CSV files whose names end with "perf_event_log".

    This function searches through the specified directory and its subdirectories for CSV files. It then filters
    the list to include only those files that have "perf_event_log" at the end of their file names.

    Files reached through a symlink that points outside ``data_dir`` are skipped, as is
    a ``data_dir`` that does not exist or is not a directory.

    Args:
        data_dir (Path): The directory path where the CSV files are located.

    Returns:
        List[Path]: A list of file paths that match the "perf_event_log" pattern. If no files are found,
                    an empty list is returned. Additionally, an error message is printed if no matching
                    files are found in the directory, or if `data_dir` is not a usable directory.
    """
    data_dir = Path(data_dir)
    if not data_dir.is_dir():
        print(f"Error: data_dir is not an existing directory: {data_dir}")
        return []

    root = data_dir.resolve()
    perf_event_log_files = []
    for file in data_dir.glob("**/*.csv"):
        if not file.stem.endswith("perf_event_log"):
            continue
        # glob follows symlinks, so a link under data_dir can resolve anywhere
        # on the filesystem; keep only what really lives under the directory.
        if not file.is_file() or not file.resolve().is_relative_to(root):
            continue
        perf_event_log_files.append(file)

    if not perf_event_log_files:
        print(f"Error: no csvs ending in perf_event_log found in data_dir: {data_dir}")

    return perf_event_log_files
