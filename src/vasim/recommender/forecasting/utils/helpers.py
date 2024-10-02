#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#

"""
Module Name: DataProcessor Utilities.

Description:
    This module provides utility functions and classes for data preprocessing and performance evaluation.
    It includes methods for smoothing time series data, splitting data into training and test sets,
    resampling time series data, and measuring execution time of functions.

Decorators:
    timeit(func):
        A decorator to measure the execution time of a function. Outputs the duration in seconds
        after the function has completed execution.

Classes:
    DataProcessor:
        Provides static methods for preparing and processing time series data, including smoothing,
        train/test splitting, resampling, and calculating workload duration.

Methods:
    timeit(func):
        Decorator function that measures the execution time of the wrapped function.

    DataProcessor.smooth_max(series, window, center=False):
        Applies a rolling maximum to smooth the input time series data.

    DataProcessor.train_test_split(series, test_size):
        Splits the input series into training and testing sets based on the specified test size.

    DataProcessor.prepare_data(y, smooth_window=1, smooth=True, test_size=0.2):
        Prepares time series data for forecasting by applying optional smoothing and performing train/test splits.

    DataProcessor.resample_dataframe(df, freq):
        Resamples the input DataFrame to a specified frequency, applying forward-filling to handle missing data.

    DataProcessor.get_workload_duration(data):
        Calculates the total duration of a workload based on the time range in the input DataFrame.

Parameters:
    series (pd.Series):
        The input time series data.

    df (pd.DataFrame):
        The input DataFrame, typically containing a 'time' column.

    window (int):
        The size of the moving window for smoothing.

    center (bool):
        Whether to set labels at the center of the window during smoothing.

    test_size (float):
        The proportion of the data to include in the test split.

    smooth_window (int):
        The window size for smoothing data.

    smooth (bool):
        Whether to apply smoothing to the data.

    freq (str):
        The frequency for resampling the data.

    data (pd.DataFrame):
        Input DataFrame containing a 'time' column for calculating the workload duration.

Returns:
    The respective methods return either the processed time series or train/test data,
    resampled DataFrame, or workload duration.
"""

import time

import pandas as pd
from sktime.forecasting.model_selection import temporal_train_test_split


def timeit(func):
    """
    Decorator to measure the execution time of a function.

    Args:
        func (function): The function to be measured.

    Returns:
        function: The wrapped function with execution time measurement.
    """

    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} execution time: {end - start:.5f} seconds")
        return result

    return wrapper


class DataProcessor:
    """
    A class that provides utility functions for time series data processing.

    The `DataProcessor` class contains static methods for performing common data preprocessing tasks
    such as smoothing time series data, splitting data into training and testing sets, resampling
    time series data, and calculating workload durations.

    Methods:
        smooth_max(series, window, center=False):
            Applies a rolling maximum to smooth the input time series data.

        train_test_split(series, test_size):
            Splits the input time series data into training and testing sets.

        prepare_data(y, smooth_window=1, smooth=True, test_size=0.2):
            Prepares the time series data by applying optional smoothing and splitting it into
            training and testing sets.

        resample_dataframe(df, freq):
            Resamples the input DataFrame to the specified frequency and forward-fills missing data.

        get_workload_duration(data):
            Calculates the total duration of a workload based on the time range in the input DataFrame.
    """

    @staticmethod
    def smooth_max(series, window, center=False):
        """
        Smooths the series by applying a rolling maximum.

        This method applies a rolling maximum function to smooth the input time series data
        using a specified window size. Optionally, it can set the labels at the center of the window.

        Args:
            series (pd.Series): The input data series.
            window (int): The size of the moving window.
            center (bool): Whether to set the labels at the center of the window (default is False).

        Returns:
            pd.Series: The smoothed series.
        """
        smoothed = series.rolling(window=window, min_periods=1, center=center).max()
        return smoothed

    @staticmethod
    def train_test_split(series, test_size):
        """
        Splits the time series into training and testing sets.

        This method splits the input time series data into training and testing sets
        using a specified test size proportion.

        Args:
            series (pd.Series): The input data series to be split.
            test_size (float): The proportion of the data to include in the test set.

        Returns:
            tuple: A tuple containing the training and testing sets.
        """
        y_train, y_test = temporal_train_test_split(series, test_size=test_size)
        return y_train, y_test

    @staticmethod
    def prepare_data(y, smooth_window=1, smooth=True, test_size=0.2):
        """
        Prepares the time series data for forecasting.

        This method applies optional smoothing to the input time series data and splits it
        into training and testing sets based on the specified test size.

        Args:
            y (pd.Series): The input time series data.
            smooth_window (int): The size of the smoothing window (default is 1).
            smooth (bool): Whether to apply smoothing to the data (default is True).
            test_size (float): The proportion of the data to include in the test set (default is 0.2).

        Returns:
            tuple: A tuple containing the smoothed training and testing sets.
        """
        y_train, y_test = DataProcessor.train_test_split(y, test_size=test_size)
        if smooth:
            y_train = DataProcessor.smooth_max(y_train, smooth_window, center=False)
            y_test = DataProcessor.smooth_max(y_test, smooth_window, center=False)
        return y_train, y_test

    @staticmethod
    def resample_dataframe(df, freq):
        """
        Resamples the DataFrame to the specified frequency.

        This method resamples the input DataFrame based on a specified frequency, such as "1T" for 1-minute
        intervals, and forward-fills missing data to maintain continuity.

        Args:
            df (pd.DataFrame): The input DataFrame to be resampled.
            freq (str): The new frequency to resample to (e.g., '1T' for 1-minute intervals).

        Returns:
            pd.DataFrame: The resampled DataFrame with missing data forward-filled.
        """
        df = df.set_index("time")
        df.index = pd.to_datetime(df.index)
        df = df.resample(freq).mean().ffill()
        return df

    @staticmethod
    def get_workload_duration(data):
        """
        Calculates the duration of the workload.

        This method calculates the total duration of the workload based on the time range
        in the input DataFrame. It computes the difference between the earliest and latest
        timestamps in the data.

        Args:
            data (pd.DataFrame): The input DataFrame containing a 'time' column.

        Returns:
            timedelta: The total duration of the workload.
        """
        min_time = data["time"].min()
        max_time = data["time"].max()
        diff = max_time - min_time
        return diff
