#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#

"""
Module Name: TestDataProcessor.

Description:
    This module contains unit tests for the `DataProcessor` class, testing its functionality
    for data preparation, smoothing, resampling, train-test splitting, and workload duration
    calculations on time series data.

Classes:
    TestDataProcessor:
        A test class that extends `unittest.TestCase` and includes multiple test methods to
        validate the behavior of `DataProcessor` methods like `smooth_max`, `train_test_split`,
        `prepare_data`, `resample_dataframe`, and `get_workload_duration`.

Test Methods:
    setUp():
        Sets up a sample DataFrame with time and value columns, used across multiple tests.

    test_smooth_max():
        Tests that the `smooth_max` method applies the correct rolling maximum to the data.

    test_train_test_split():
        Tests the `train_test_split` method to ensure that data is correctly split into training
        and testing sets based on the provided test size.

    test_prepare_data_smooth():
        Tests that the `prepare_data` method properly applies smoothing and returns
        correctly split training and testing sets.

    test_prepare_data_no_smooth():
        Tests the `prepare_data` method without applying smoothing, ensuring correct
        train-test splitting of the data.

    test_resample_dataframe():
        Tests the `resample_dataframe` method to ensure data is resampled to the correct frequency.

    test_get_workload_duration():
        Tests the `get_workload_duration` method to calculate the duration of a workload based
        on the input DataFrame's time range.

Usage:
    These tests can be run using `unittest.main()` to verify that the `DataProcessor` class's
    data processing and time series methods work as expected.
"""
import unittest
from datetime import timedelta

import pandas as pd

from vasim.recommender.forecasting.utils.helpers import DataProcessor


class TestDataProcessor(unittest.TestCase):

    def setUp(self):
        self.data = pd.DataFrame(
            {"time": pd.date_range(start="2023-01-01", periods=5, freq="T"), "value": [10.0, 20.0, 30.0, 25.0, 15.0]}
        )

    def test_smooth_max(self):
        smoothed = DataProcessor.smooth_max(self.data["value"], window=2)
        expected = pd.Series([10.0, 20.0, 30.0, 30.0, 25.0], name="value")
        pd.testing.assert_series_equal(expected, smoothed)

    def test_train_test_split(self):
        y_train, y_test = DataProcessor.train_test_split(self.data["value"], test_size=0.2)
        self.assertEqual(4, len(y_train))
        self.assertEqual(10.0, y_train.iloc[0])
        self.assertEqual(20.0, y_train.iloc[1])
        self.assertEqual(30.0, y_train.iloc[2])
        self.assertEqual(25.0, y_train.iloc[3])
        self.assertEqual(1, len(y_test))
        self.assertEqual(15.0, y_test.iloc[0])

    def test_prepare_data_smooth(self):
        y_train, y_test = DataProcessor.prepare_data(self.data["value"], smooth_window=2, smooth=True, test_size=0.2)
        self.assertEqual(4, len(y_train))
        self.assertEqual(10.0, y_train.iloc[0])
        self.assertEqual(20.0, y_train.iloc[1])
        self.assertEqual(30.0, y_train.iloc[2])
        self.assertEqual(30.0, y_train.iloc[3])
        self.assertEqual(1, len(y_test))
        self.assertEqual(15.0, y_test.iloc[0])

    def test_prepare_data_no_smooth(self):
        y_train, y_test = DataProcessor.prepare_data(self.data["value"], smooth_window=2, smooth=False, test_size=0.2)
        self.assertEqual(4, len(y_train))
        self.assertEqual(10.0, y_train.iloc[0])
        self.assertEqual(20.0, y_train.iloc[1])
        self.assertEqual(30.0, y_train.iloc[2])
        self.assertEqual(25.0, y_train.iloc[3])
        self.assertEqual(1, len(y_test))
        self.assertEqual(15.0, y_test.iloc[0])

    def test_resample_dataframe(self):
        resampled = DataProcessor.resample_dataframe(self.data, freq="2T")
        self.assertEqual(3, len(resampled))
        self.assertEqual(15.0, resampled["value"].iloc[0])
        self.assertEqual(27.5, resampled["value"].iloc[1])
        self.assertEqual(15.0, resampled["value"].iloc[2])

    def test_get_workload_duration(self):
        duration = DataProcessor.get_workload_duration(self.data)
        expected_duration = timedelta(minutes=4)
        self.assertEqual(duration, expected_duration)


if __name__ == "__main__":
    unittest.main()
