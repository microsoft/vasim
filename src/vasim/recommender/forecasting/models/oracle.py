#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#
"""
Module Name: Oracle.

Description:
    The `Oracle` class is responsible for loading, processing, and evaluating performance data from CSV files.
    It simulates an ideal predictor for assessing recommender system policies. By comparing the recommender system's
    predictions to the theoretically ideal predictions, errors can be attributed either to the prediction method or
    to the recommender system itself.

Classes:
    Oracle:
        Loads CSV files from a specified directory, processes the data, and provides methods for fitting
        and predicting future performance data.

Attributes:
    all_performance_data (pd.DataFrame):
        A DataFrame containing all the loaded performance data sorted by timestamp.

Methods:
    __init__(data_dir):
        Initializes the `Oracle` by loading CSV files from the provided directory, processing the data,
        and storing it in a DataFrame.

    fit(data):
        Placeholder method for fitting a model on the provided data.

    predict(data, forecast_horizon):
        Predicts future performance data points based on the provided data and the forecast horizon.
        Returns a DataFrame containing the predicted values.

Parameters:
    data_dir (str):
        The directory containing the CSV files to load.

Returns:
    pd.DataFrame:
        The `predict` method returns a DataFrame with the predicted performance data points, indexed by timestamp.
"""
import os
from datetime import datetime

import pandas as pd


class Oracle:
    """
    Oracle class for loading, processing, and evaluating performance data from CSV files.

    This class is designed to assess recommender system policies by comparing them against
    an ideal theoretical predictor, allowing for the separation of errors attributable to
    prediction and the recommender itself.

    Attributes:
        all_performance_data (pd.DataFrame): DataFrame containing all loaded performance data.
    """

    def __init__(self, data_dir):
        """
        Initializes the Oracle class by loading CSV files from the specified directory.

        Args:
            data_dir (str): Directory containing the CSV files to load.
        """
        dfs = []
        for file_name in os.listdir(data_dir):
            if file_name.endswith(".csv"):
                # Construct the full file path
                file_path = os.path.join(data_dir, file_name)

                # Load the CSV file into a pandas DataFrame
                df = pd.read_csv(file_path)
                # Append the DataFrame to the list
                dfs.append(df)
        # Concatenate all DataFrames into a single DataFrame
        temp_data = pd.concat(dfs, ignore_index=True)
        temp_data["cpu"] = temp_data["CPU_USAGE_ACTUAL"]
        temp_data["time"] = temp_data["TIMESTAMP"].apply(lambda x: datetime.strptime(x, "%Y.%m.%d-%H:%M:%S:%f"))
        temp_data = temp_data.sort_values("time", ascending=True)
        self.all_performance_data = temp_data

    def fit(self, data):
        """
        Placeholder method for fitting a model to the data.

        Args:
            data (pd.DataFrame): Data to fit the model on.
        """

    def predict(self, data, forecast_horizon):
        """
        Predicts future data points based on the provided data.

        Args:
            data (pd.DataFrame): DataFrame containing the input data for prediction.
            forecast_horizon (int): Number of future data points to predict.

        Returns:
            pd.DataFrame: DataFrame containing the predicted data points.
        """
        temp_data = self.all_performance_data
        latest_timestamp = data.index.max()

        # Get the forecast_horizon data points immediately after the latest timestamp from data
        data_after_latest = temp_data[temp_data["time"] > latest_timestamp].head(forecast_horizon)
        data_after_latest = data_after_latest[["time", "cpu"]]

        data_after_latest["timeindex"] = data_after_latest["time"]
        data_after_latest.set_index("timeindex", inplace=True)
        return data_after_latest
