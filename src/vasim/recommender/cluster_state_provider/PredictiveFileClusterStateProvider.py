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
    capabilities to the original cluster state management. This class integrates time-series forecasting to predict
    future CPU utilization based on historical performance data. It utilizes preprocessed data from CSV files and
    time-series models to forecast the next `window_length` minutes of data.

    This class is designed for use in both production and simulated environments, where predictive decisions are
    made to manage cluster resources effectively.

Classes:
    PredictiveFileClusterStateProvider:
        Extends the `FileClusterStateProvider` class to add predictive capabilities using time-series
        forecasting models for CPU utilization.

Methods:
    __init__(data_dir, prediction_config, **kwargs):
        Initializes the predictive state provider with directories for data, a prediction configuration,
        and any additional keyword arguments. This includes setting up parameters for the frequency of data collection,
        prediction time windows, and the forecaster.

    get_predicted_cores(data):
        Returns the predicted number of CPU cores required based on the maximum CPU usage in the provided data.
        Uses a traditional rounding method.

    prediction_activated(data=None):
        Determines whether enough historical data has been collected to activate the prediction process,
        based on workload duration.

    _get_all_performance_data():
        Reads all available CSV performance data and processes it. Drops duplicates and sorts the data by time.

    get_next_recorded_data():
        Retrieves the current performance data for the defined time window and predicts future data if enough
        history is available. Joins the actual and predicted data to return a complete dataset.

    get_prediction(data):
        Processes and resamples the input data and uses the time-series forecaster to predict future CPU utilization
        for the next set of time points.
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

# This class adds predictive capabilities to FileClusterStateProvider. The algorithm is as
# follows:
# 1. Read the data from the csvs and preprocess it as originally done in FileClusterStateProvider without
# limiting data to the window. This data is used for time series
# 2. Get performance data from the csvs as in FileClusterStateProvider
# 3. Predict the next window_length minutes of data using the time series model
# 4. Return the performance data and the predicted data


class PredictiveFileClusterStateProvider(FileClusterStateProvider):
    # pylint: disable=too-many-instance-attributes
    def __init__(self, data_dir, prediction_config, **kwargs):
        super().__init__(data_dir=data_dir, **kwargs)

        # Set of parameters for data preprocessing
        # TODO: read from config
        self.frequency_minutes = prediction_config["frequency_minutes"]  # 30 seconds
        self.minutes_to_predict = prediction_config.get(
            "minutes_to_predict", int(self.config.general_config["window"] / 2)
        )  # we want to take half of the original window and predict the other half
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
            # keyword argument 'param_name' exists
            self.config = kwargs["config"]

        self.logger = logging.getLogger()

    def get_predicted_cores(self, data):
        def traditional_round(x):
            frac = x - math.floor(x)
            if frac < 0.5:
                return math.floor(x)
            return math.ceil(x)

        return max(traditional_round(data["cpu"].max()), self.cores)

    def prediction_activated(self, data=None):
        all_history_data = data
        if not self._prediction_activated and all_history_data is not None:
            self._prediction_activated = DataProcessor.get_workload_duration(all_history_data).total_seconds() > (
                self.waiting_time * 60
            )
        return self._prediction_activated

    def _get_all_performance_data(self):  # Verify that csvs exist in the data_dir
        csv_paths = list_perf_event_log_files(self.data_dir)
        if not csv_paths:
            self.logger.error("Error reading csvs in %s", self.data_dir)
            return None, None

        # Process data
        recorded_data = self.process_data(csv_paths)
        self.logger.debug("len recorded_data: %d", len(recorded_data))
        # Drop duplicates from data
        recorded_data = self.drop_duplicates(recorded_data)

        # Ensure data is sorted by time
        recorded_data = self.sort_data(recorded_data)
        return recorded_data

    # we read updated file every time
    def get_next_recorded_data(self):
        """
        Returns the performance data inside the window and the last time in the data.

        :return: performance data, end_time
        performance data: DataFrame
        end_time: Timestamp
        """
        data = self._get_all_performance_data()  # we take all history to build prediction
        perf_data, end_time = super().get_next_recorded_data()

        # TODO document this. We are building a prediction only if we have enough data,
        # but we need to document and explain what this means and how it is used.
        if self.prediction_activated(data):  # we have enough data to build prediction
            y_pred = self.get_prediction(data)

            # change cores value to max in the predicted data
            self.logger.debug("y_pred: %s", y_pred)

            # join actual and predicted data
            entire_segment = pd.concat([perf_data, y_pred], ignore_index=True).tail(
                int(self.predictive_window / self.frequency_minutes)
            )
        else:
            self.logger.debug("We don't have enough data to build prediction yet")
            entire_segment = perf_data

        return entire_segment, end_time

    def get_prediction(self, data):

        self.logger.debug(
            "total number of observations: %s. We want to predict next %s minutes = %s points.",
            len(data),
            self.minutes_to_predict,
            self.number_of_points_to_predict,
        )
        data = DataProcessor.resample_dataframe(data, self.freq)
        return self.data_forecaster.get_prediction(data, self.number_of_points_to_predict)
