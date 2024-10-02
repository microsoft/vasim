#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#

"""
Module Name: PredictiveFileClusterStateProvider.

Description:
    The `PredictiveFileClusterStateProvider` class extends `FileClusterStateProvider` and adds predictive
    capabilities for managing cluster state. It uses time-series forecasting to predict future CPU utilization
    based on historical performance data, leveraging CSV files and forecasting models to estimate the
    number of CPU cores required for the next time window.

    This class is designed for both production and simulated environments, allowing for proactive decision-making
    in cluster resource management by predicting workload demands.

Classes:
    PredictiveFileClusterStateProvider:
        Extends the `FileClusterStateProvider` class by adding predictive capabilities
        using time-series forecasting models for CPU utilization.

Methods:
    __init__(data_dir, prediction_config, **kwargs):
        Initializes the `PredictiveFileClusterStateProvider` with the directory for CSV data, prediction configuration,
        and additional parameters such as frequency of data collection, waiting time before prediction, and forecaster setup.

    get_predicted_cores(data):
        Returns the predicted number of CPU cores based on the provided data, applying rounding rules.

    prediction_activated(data=None):
        Determines if prediction mode is activated by evaluating whether enough historical data has been collected.

    _get_all_performance_data():
        Retrieves and processes all available performance data from CSV files,
        dropping duplicates and sorting the data by time.

    get_next_recorded_data():
        Retrieves the current performance data within the defined time window
        and predicts future data if enough history is available.

    get_prediction(data):
        Processes and resamples the input data and uses the time-series forecaster
        to predict future CPU utilization for the next time window.
"""

import logging
import math

import pandas as pd

from vasim.commons.utils import list_perf_event_log_files
from vasim.recommender.cluster_state_provider.FileClusterStateProvider import (
    FileClusterStateProvider,
)
from vasim.recommender.forecasting.TimeSeriesForecaster import TimeSeriesForecaster
from vasim.recommender.forecasting.utils.helpers import DataProcessor


class PredictiveFileClusterStateProvider(FileClusterStateProvider):
    """
    A class that adds predictive capabilities to `FileClusterStateProvider` by using time-series forecasting.

    to estimate future CPU utilization.

    This class enhances the original `FileClusterStateProvider` by forecasting future CPU demand based on historical
    performance data, making it useful for proactively managing cluster resources. It reads and processes CSV files,
    predicts future CPU needs, and combines the actual and predicted data for more informed decision-making.

    Attributes:
        frequency_minutes (int): The frequency in minutes at which performance data is sampled.
        minutes_to_predict (int): The number of minutes to predict in the future.
        freq (str): The resampling frequency for time-series data.
        waiting_time (int): The time in minutes to wait before making a prediction.
        data_processor (DataProcessor): An object that handles preprocessing of data.
        data_forecaster (TimeSeriesForecaster): The forecasting model used for predicting future CPU utilization.
        cores (int): The current CPU limit of the cluster.
        predicted_cores (int): The predicted CPU limit based on forecasting.
        _prediction_activated (bool): A flag indicating whether prediction mode is active.
        number_of_points_to_predict (int): The number of data points to predict, based on the prediction window.
        predictive_window (int): The total predictive window combining actual and predicted data.
    """

    # pylint: disable=too-many-instance-attributes
    def __init__(self, data_dir, prediction_config, **kwargs):
        """
        Initialize the PredictiveFileClusterStateProvider with predictive capabilities.

        This constructor sets up the necessary parameters for time-series forecasting, including
        frequency of data collection, waiting time before prediction, and prediction window size.

        Args:
            data_dir (str): The directory where performance CSV files are stored.
            prediction_config (dict): Configuration for prediction settings such as frequency, models, and window sizes.
            **kwargs: Additional arguments passed to the parent class for configuration.
        """
        super().__init__(data_dir=data_dir, **kwargs)

        # Set up predictive parameters from the configuration
        self.frequency_minutes = prediction_config["frequency_minutes"]
        self.minutes_to_predict = prediction_config.get("minutes_to_predict", int(self.config.general_config["window"] / 2))
        self.freq = f"{self.frequency_minutes}T"
        self.waiting_time = prediction_config["waiting_before_predict"]
        self.data_processor = DataProcessor()
        self.data_forecaster = TimeSeriesForecaster(
            sp=int(prediction_config["waiting_before_predict"] / self.frequency_minutes),
            selected_forecaster=prediction_config["forecasting_models"],
            data_dir=data_dir,
        )
        self.cores = 0
        self.predicted_cores = 0
        self._prediction_activated = False
        self.number_of_points_to_predict = int(self.minutes_to_predict / self.frequency_minutes)
        self.predictive_window = prediction_config.get(
            "total_predictive_window", self.number_of_points_to_predict + int(self.config.general_config["window"])
        )
        if "config" in kwargs:
            self.config = kwargs["config"]

        self.logger = logging.getLogger()

    def get_predicted_cores(self, data):
        """
        Calculate the predicted number of CPU cores based on the maximum observed CPU usage.

        This method applies a rounding function to the predicted CPU usage to ensure appropriate
        scaling decisions are made.

        Args:
            data (pd.DataFrame): The performance data used for making CPU predictions.

        Returns:
            int: The predicted number of CPU cores required.
        """

        def traditional_round(x):
            frac = x - math.floor(x)
            return math.floor(x) if frac < 0.5 else math.ceil(x)

        return max(traditional_round(data["cpu"].max()), self.cores)

    def prediction_activated(self, data=None):
        """
        Determines if prediction mode should be activated based on the collected historical data.

        Prediction is activated when enough historical data has been collected to make accurate forecasts.

        Args:
            data (pd.DataFrame, optional): The historical performance data to evaluate.

        Returns:
            bool: True if prediction mode is activated, False otherwise.
        """
        all_history_data = data
        if not self._prediction_activated and all_history_data is not None:
            self._prediction_activated = DataProcessor.get_workload_duration(all_history_data).total_seconds() > (
                self.waiting_time * 60
            )
        return self._prediction_activated

    def _get_all_performance_data(self):
        """
        Retrieves all available performance data from the CSV files.

        This method processes all CSV files in the data directory, dropping duplicates
        and sorting the data by time.

        Returns:
            pd.DataFrame: The recorded performance data.
        """
        csv_paths = list_perf_event_log_files(self.data_dir)
        if not csv_paths:
            self.logger.error("Error reading CSV files from %s", self.data_dir)
            return None

        recorded_data = self.process_data(csv_paths)
        recorded_data = self.drop_duplicates(recorded_data)
        recorded_data = self.sort_data(recorded_data)

        return recorded_data

    def get_next_recorded_data(self):
        """
        Retrieves the performance data for the current time window and predicts future data.

        This method retrieves the current performance data and predicts the next set of data if
        enough historical data is available. It combines actual and predicted data to return a
        complete dataset for decision-making.

        Returns:
            tuple: A tuple containing the performance data (pd.DataFrame) and the end time (datetime).
        """
        data = self._get_all_performance_data()  # Get historical data for prediction
        perf_data, end_time = super().get_next_recorded_data()

        if self.prediction_activated(data):  # Predict future data if we have enough history
            y_pred = self.get_prediction(data)

            # Combine actual and predicted data
            self.logger.debug("Predicted data: %s", y_pred)
            entire_segment = pd.concat([perf_data, y_pred], ignore_index=True).tail(
                int(self.predictive_window / self.frequency_minutes)
            )
        else:
            self.logger.debug("Not enough data for prediction yet")
            entire_segment = perf_data

        return entire_segment, end_time

    def get_prediction(self, data):
        """
        Generates a prediction for future CPU usage based on the historical data.

        This method processes and resamples the input data and uses the time-series forecaster to
        predict future CPU usage for the next time window.

        Args:
            data (pd.DataFrame): The historical performance data used for prediction.

        Returns:
            pd.DataFrame: A DataFrame containing the predicted CPU usage for the next set of time points.
        """
        self.logger.debug(
            "Number of observations: %d. Predicting for the next %d minutes = %d points.",
            len(data),
            self.minutes_to_predict,
            self.number_of_points_to_predict,
        )
        data = DataProcessor.resample_dataframe(data, self.freq)
        return self.data_forecaster.get_prediction(data, self.number_of_points_to_predict)
