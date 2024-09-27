#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#

"""
Module Name: TestOracle.

Description:
    This module contains unit tests for the `Oracle` class, which loads and processes
    time series performance data from CSV files and makes predictions. The tests validate
    that data is loaded correctly, predictions are generated, and ensure the core functionality
    of the `Oracle` class works as expected.

Classes:
    TestOracle:
        A test class that extends `unittest.TestCase` and runs tests on the `Oracle` class.
        It ensures proper initialization, data loading, and the ability to make predictions
        based on historical data.

Test Methods:
    setUp():
        Creates a temporary directory and CSV file with performance data for testing.
        The test dataset simulates CPU usage over time.

    tearDown():
        Cleans up the temporary directory and CSV files after the test execution.

    test_oracle():
        Tests the initialization of the `Oracle` class, ensures the `fit` method runs without errors,
        and validates that predictions are generated correctly based on historical data.

Usage:
    These tests can be run using `unittest.main()` to execute the unit tests for the
    `Oracle` class, verifying its functionality and behavior with time series data.
"""

import os
import shutil
import unittest
from datetime import datetime
from pathlib import Path

import pandas as pd

from vasim.recommender.forecasting.models.oracle import Oracle


class TestOracle(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory and CSV files for testing
        root_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        self.test_dir = root_dir / "test_data/oracle"
        os.makedirs(self.test_dir, exist_ok=True)
        self.csv_file_path = os.path.join(self.test_dir, "test_data.csv")
        data = {
            "CPU_USAGE_ACTUAL": [10, 20, 30, 40, 50],
            "TIMESTAMP": [
                "2023.01.01-00:00:00:000000",
                "2023.01.01-00:01:00:000000",
                "2023.01.01-00:02:00:000000",
                "2023.01.01-00:03:00:000000",
                "2023.01.01-00:04:00:000000",
            ],
        }
        df = pd.DataFrame(data)
        df.to_csv(self.csv_file_path, index=False)
        self.oracle = Oracle(self.test_dir)

    def tearDown(self):
        # Remove the temporary directory and files after tests
        shutil.rmtree(self.test_dir)

    def test_oracle(self):
        # Initialization
        self.assertIsInstance(self.oracle.all_performance_data, pd.DataFrame)
        self.assertEqual(5, len(self.oracle.all_performance_data))
        # Fit method is a placeholder, so just ensure it runs without error
        self.oracle.fit(None)
        # Prediction
        data = pd.DataFrame(
            {
                "cpu": [10, 20, 30],
                "time": [
                    datetime.strptime("2023.01.01-00:00:00:000000", "%Y.%m.%d-%H:%M:%S:%f"),
                    datetime.strptime("2023.01.01-00:01:00:000000", "%Y.%m.%d-%H:%M:%S:%f"),
                    datetime.strptime("2023.01.01-00:02:00:000000", "%Y.%m.%d-%H:%M:%S:%f"),
                ],
            }
        )
        data.set_index("time", inplace=True)
        predictions = self.oracle.predict(data, 2)
        self.assertEqual(2, len(predictions))
        self.assertIn("cpu", predictions.columns)
        self.assertIn("time", predictions.columns)
        self.assertEqual([40, 50], predictions["cpu"].tolist())
        self.assertEqual(
            [
                datetime.strptime("2023.01.01-00:03:00:000000", "%Y.%m.%d-%H:%M:%S:%f"),
                datetime.strptime("2023.01.01-00:04:00:000000", "%Y.%m.%d-%H:%M:%S:%f"),
            ],
            predictions["time"].tolist(),
        )


if __name__ == "__main__":
    unittest.main()
