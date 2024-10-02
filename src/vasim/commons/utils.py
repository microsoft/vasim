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

    Args:
        data_dir (Path): The directory path where the CSV files are located.

    Returns:
        List[Path]: A list of file paths that match the "perf_event_log" pattern. If no files are found,
                    an empty list is returned. Additionally, an error message is printed if no matching
                    files are found in the directory.
    """
    csv_files = list(data_dir.glob("**/*.csv"))

    # Filter CSV files that end with "perf_event_log"
    perf_event_log_files = [file for file in csv_files if file.stem.endswith("perf_event_log")]

    if not perf_event_log_files:
        print(f"Error: no csvs ending in perf_event_log found in data_dir: {data_dir}")

    return perf_event_log_files
