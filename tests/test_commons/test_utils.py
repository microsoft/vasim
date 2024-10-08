#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#

"""
This module contains unit tests for the function `list_perf_event_log_files`, which is.

responsible for listing performance event log files in a specified directory. The tests
use mocking to simulate the behavior of the `Path.glob` method to return specific file
types for testing scenarios.

Test cases:
    - test_list_perf_event_log_files_returns_csv_files: Tests if the function correctly
      lists CSV files that match the "perf_event_log" pattern.
    - test_list_perf_event_log_files_returns_empty_list_on_empty_dir: Tests if the function
      returns an empty list when there are no files in the directory.
    - test_list_perf_event_log_files_returns_empty_list_on_non_perf_event_logs: Tests if the
      function returns an empty list when no "perf_event_log" files are present.

Classes:
    - TestListPerfEventLogFiles: Contains the test cases for `list_perf_event_log_files`.
"""
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from vasim.commons.utils import list_perf_event_log_files


class TestListPerfEventLogFiles(unittest.TestCase):

    @patch("vasim.commons.utils.Path.glob")
    def test_list_perf_event_log_files_returns_csv_files(self, mock_glob):
        # Mock the return value of Path.glob to simulate CSV files ending with "perf_event_log"
        mock_files = [
            MagicMock(spec=Path, stem="file1_perf_event_log", suffix=".csv"),
            MagicMock(spec=Path, stem="file2_perf_event_log", suffix=".csv"),
            MagicMock(spec=Path, stem="file3_perf_event_log", suffix=".csv"),
        ]
        mock_glob.return_value = mock_files

        result = list_perf_event_log_files(Path("tests/tests_commons"))
        self.assertEqual(len(result), 3)
        for file in result:
            self.assertTrue(file.stem.endswith("perf_event_log"))

    @patch("vasim.commons.utils.Path.glob")
    def test_list_perf_event_log_files_returns_empty_list_on_empty_dir(self, mock_glob):
        # Mock the return value of Path.glob to simulate no CSV files
        mock_glob.return_value = []

        result = list_perf_event_log_files(Path("tests/tests_commons"))
        self.assertEqual(len(result), 0)

    @patch("vasim.commons.utils.Path.glob")
    def test_list_perf_event_log_files_returns_empty_list_on_non_perf_event_logs(self, mock_glob):
        # Mock the return value of Path.glob to simulate non CSV file and non perf_event_log CSV file
        mock_glob.return_value = [
            MagicMock(spec=Path, stem="file1", suffix=".json"),
            MagicMock(spec=Path, stem="file2", suffix=".csv"),
        ]

        result = list_perf_event_log_files(Path("data/"))
        self.assertEqual(len(result), 0)


if __name__ == "__main__":
    unittest.main()
