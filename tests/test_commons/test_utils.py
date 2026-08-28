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
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from vasim.commons.utils import list_perf_event_log_files


class TestListPerfEventLogFiles(unittest.TestCase):

    @patch("vasim.commons.utils.Path.is_dir", return_value=True)
    @patch("vasim.commons.utils.Path.glob")
    def test_list_perf_event_log_files_returns_csv_files(self, mock_glob, _mock_is_dir):
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

    @patch("vasim.commons.utils.Path.is_dir", return_value=True)
    @patch("vasim.commons.utils.Path.glob")
    def test_list_perf_event_log_files_returns_empty_list_on_empty_dir(self, mock_glob, _mock_is_dir):
        # Mock the return value of Path.glob to simulate no CSV files
        mock_glob.return_value = []

        result = list_perf_event_log_files(Path("tests/tests_commons"))
        self.assertEqual(len(result), 0)

    @patch("vasim.commons.utils.Path.is_dir", return_value=True)
    @patch("vasim.commons.utils.Path.glob")
    def test_list_perf_event_log_files_returns_empty_list_on_non_perf_event_logs(self, mock_glob, _mock_is_dir):
        # Mock the return value of Path.glob to simulate non CSV file and non perf_event_log CSV file
        mock_glob.return_value = [
            MagicMock(spec=Path, stem="file1", suffix=".json"),
            MagicMock(spec=Path, stem="file2", suffix=".csv"),
        ]

        result = list_perf_event_log_files(Path("data/"))
        self.assertEqual(len(result), 0)


class TestListPerfEventLogFilesOnDisk(unittest.TestCase):
    """Filesystem-backed coverage for the input checks added for #18."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self._tmp.name) / "data"
        self.data_dir.mkdir()
        self.addCleanup(self._tmp.cleanup)

    def test_returns_matching_csv_from_a_real_directory(self):
        wanted = self.data_dir / "node_perf_event_log.csv"
        wanted.write_text("ts,cpu\n")
        (self.data_dir / "unrelated.csv").write_text("ts,cpu\n")

        result = list_perf_event_log_files(self.data_dir)

        self.assertEqual([p.name for p in result], ["node_perf_event_log.csv"])

    def test_missing_data_dir_returns_empty_list(self):
        self.assertEqual(list_perf_event_log_files(self.data_dir / "absent"), [])

    def test_file_passed_as_data_dir_returns_empty_list(self):
        not_a_dir = self.data_dir / "a_perf_event_log.csv"
        not_a_dir.write_text("ts,cpu\n")

        self.assertEqual(list_perf_event_log_files(not_a_dir), [])

    def test_symlink_escaping_data_dir_is_skipped(self):
        outside = Path(self._tmp.name) / "outside_perf_event_log.csv"
        outside.write_text("ts,cpu\n")
        link = self.data_dir / "linked_perf_event_log.csv"
        try:
            link.symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable on this platform")

        self.assertEqual(list_perf_event_log_files(self.data_dir), [])

    def test_symlink_staying_inside_data_dir_is_kept(self):
        target = self.data_dir / "real_perf_event_log.csv"
        target.write_text("ts,cpu\n")
        link = self.data_dir / "nested"
        link.mkdir()
        inner = link / "alias_perf_event_log.csv"
        try:
            inner.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable on this platform")

        result = sorted(p.name for p in list_perf_event_log_files(self.data_dir))

        self.assertEqual(result, ["alias_perf_event_log.csv", "real_perf_event_log.csv"])


if __name__ == "__main__":
    unittest.main()
