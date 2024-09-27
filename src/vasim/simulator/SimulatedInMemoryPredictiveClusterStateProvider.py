#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#

"""
Module Name: SimulatedInMemoryPredictiveClusterStateProvider.

Description:
    The `SimulatedInMemoryPredictiveClusterStateProvider` class extends both `SimulatedBaseClusterStateProvider`
    and `PredictiveFileClusterStateProvider` to simulate predictive scaling decisions in an in-memory environment.
    It enables time-series forecasting and performance management based on historical data, simulating a
    predictive cluster scaling process in a controlled environment.

Classes:
    SimulatedInMemoryPredictiveClusterStateProvider:
        Combines the predictive capabilities of `PredictiveFileClusterStateProvider` with the in-memory
        simulation features of `SimulatedBaseClusterStateProvider` to provide a predictive cluster state
        management system.

Methods:
    __init__(data_dir="data/performance_log", window=40, decision_file_path=None, max_cpu_limit=None, lag=None, **kwargs):
        Initializes the predictive cluster state provider with the given data directory, window size,
        CPU limits, and lag. It sets up the in-memory simulation of predictive scaling.

    read_metrics_data():
        Reads and returns the recorded performance data until the current time, filtered by the window size.
        Returns None if the current time exceeds the data end time.

    _get_all_performance_data():
        Returns all performance data up to the current time, including a lag adjustment. If the current time
        exceeds the end time of the data, it returns None.

    get_next_recorded_data():
        Retrieves the next set of recorded performance data from the predictive file provider and returns
        it along with the end time.

    flush_metrics_data(filename):
        Writes the recorded data to a CSV file with a custom header. This allows the metrics to be
        saved for analysis or reporting.

Parameters:
    data_dir (str):
        The directory where performance log CSV files are stored.
    window (int):
        The size of the time window for filtering the data (in minutes).
    decision_file_path (str):
        The file path where scaling decisions are recorded.
    max_cpu_limit (int):
        The maximum CPU limit allowed for scaling operations.
    lag (int):
        The time lag in minutes used for predictive decision-making in the simulation.

Returns:
    The `read_metrics_data` and `_get_all_performance_data` methods return filtered DataFrames containing
    the performance data for the current window or up to the current time.
"""
from datetime import timedelta

from vasim.recommender.cluster_state_provider.PredictiveFileClusterStateProvider import (
    PredictiveFileClusterStateProvider,
)
from vasim.simulator.SimulatedBaseClusterStateProvider import (
    SimulatedBaseClusterStateProvider,
)


class SimulatedInMemoryPredictiveClusterStateProvider(SimulatedBaseClusterStateProvider, PredictiveFileClusterStateProvider):

    def __init__(
        self,
        data_dir="data/performance_log",
        window=40,
        decision_file_path=None,
        max_cpu_limit=None,
        lag=None,
        **kwargs,
    ):
        # pylint: disable=too-many-arguments
        PredictiveFileClusterStateProvider.__init__(
            self,
            data_dir=data_dir,
            window=window,
            decision_file_path=decision_file_path,
            max_cpu_limit=max_cpu_limit,
            lag=lag,
            **kwargs,
        )
        SimulatedBaseClusterStateProvider.__init__(
            self,
            data_dir=data_dir,
            window=window,
            decision_file_path=decision_file_path,
            max_cpu_limit=max_cpu_limit,
            lag=lag,
            **kwargs,
        )

    # we read updated file every time
    def read_metrics_data(self):
        # Return data till current time
        if self.current_time > self.end_time:
            return None

        # TODO: sanity checks on 'window' user inputs
        td_window = timedelta(minutes=self.config.general_config["window"])
        filtered_data = self.recorded_data.loc[self.current_time - td_window : self.current_time]

        self.logger.info("current_time: %s; filtered_data length: %s", self.current_time, len(filtered_data))
        return filtered_data

    def _get_all_performance_data(self):
        # return data till current time
        if self.current_time > self.end_time:
            return None

        # add lag to current time
        filtered_data = self.recorded_data.loc[self.start_time : self.current_time]
        self.logger.info("current_time: %s; filtered_data length: %s", self.current_time, len(filtered_data))

        return filtered_data

    def get_next_recorded_data(self):
        """
        Returns the performance data inside the window and the last time in the data.

        :return: performance data, end_time
        performance data: DataFrame
        end_time: Timestamp
        """
        perf_data, end_time = PredictiveFileClusterStateProvider.get_next_recorded_data(self)
        return perf_data, end_time

    def flush_metrics_data(self, filename):
        # Create a custom header string
        custom_header = "TIMESTAMP,CPU_USAGE_ACTUAL"

        # Open the file for writing
        with open(filename, "w", encoding="utf-8") as file:
            # Write the custom header as the first line
            file.write(custom_header + "\n")

            # Use pandas to write the DataFrame data without a header
            self.recorded_data.to_csv(file, index=False, date_format="%Y.%m.%d-%H:%M:%S:%f", header=False)
