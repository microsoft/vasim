import warnings
import time

import numpy as np
from sktime.forecasting.model_selection import temporal_train_test_split
from sktime.forecasting.model_selection import SlidingWindowSplitter, ForecastingGridSearchCV
import pandas as pd
from sktime.forecasting.theta import ThetaForecaster


def timeit(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} execution time: {end - start:.5f} seconds")
        return result

    return wrapper


class DataProcessor:
    """
    A class for processing data with parameters.
    """

    def smooth_max(self, series, window, center=False):
        smoothed = series.rolling(window=window, min_periods=1, center=center).max()
        return smoothed

    def train_test_split(self, series, test_size):
        y_train, y_test = temporal_train_test_split(series, test_size=test_size)
        return y_train, y_test

    def prepare_data(self, y, smooth_window=1, smooth=True, test_size=0.2):
        """
        Prepare data for forecasting.
        """
        # Get target column
        y_train, y_test = temporal_train_test_split(y, test_size=test_size)
        if smooth:
            y_train = self.smooth_max(y_train, smooth_window, center=False)
            y_test = self.smooth_max(y_test, smooth_window, center=False)
        return y_train, y_test

    @staticmethod
    def resample_dataframe(df, freq):
        # set the index to the timestamp column
        df = df.set_index('time')
        # convert the index to a pandas datetime index
        df.index = pd.to_datetime(df.index)
        # resample the DataFrame to the desired frequency
        df = df.resample(freq).mean().ffill()
        # reset the index to a column
        # df = df.reset_index()
        return df

    def get_workload_duration(self, data):
        min_time = data["time"].min()
        max_time = data["time"].max()
        diff = max_time - min_time
        return diff
