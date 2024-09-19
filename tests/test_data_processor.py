#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#
import unittest
from datetime import timedelta

import pandas as pd

from vasim.recommender.forecasting.utils import DataProcessor


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
