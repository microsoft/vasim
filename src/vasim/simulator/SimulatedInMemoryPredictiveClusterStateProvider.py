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
    """
    A class that simulates predictive scaling decisions in an in-memory environment, combining the.

    features of both `SimulatedBaseClusterStateProvider` and `PredictiveFileClusterStateProvider`.
    This class manages time-series forecasting and performance data to simulate predictive cluster
    scaling in a controlled environment.

    Attributes:
        data_dir (str): Directory where performance log CSV files are stored.
        window (int): The size of the time window for filtering data (in minutes).
        decision_file_path (str): Path where scaling decisions are logged.
        max_cpu_limit (int): The maximum CPU limit allowed for scaling.
        lag (int): The time lag used for predictive decision-making.

    Methods:
        read_metrics_data(): Returns performance data filtered by the window.
        _get_all_performance_data(): Returns all performance data up to the current time.
        get_next_recorded_data(): Retrieves the next set of recorded performance data.
        flush_metrics_data(filename): Saves the recorded performance data to a CSV file.
    """

    # pylint: disable=too-many-instance-attributes disable=too-many-positional-arguments
    def __init__(
        self,
        data_dir="data/performance_log",
        window=40,
        decision_file_path=None,
        max_cpu_limit=None,
        lag=None,
        **kwargs,
    ):
        """
        Initialize the `SimulatedInMemoryPredictiveClusterStateProvider`.

        This constructor initializes both `SimulatedBaseClusterStateProvider` and
        `PredictiveFileClusterStateProvider`, setting up the in-memory simulation environment
        with predictive capabilities.

        Args:
            data_dir (str): Directory where performance log CSV files are stored.
            window (int): The size of the time window for filtering performance data (in minutes).
            decision_file_path (str): Path where scaling decisions are logged.
            max_cpu_limit (int): The maximum CPU limit allowed for scaling operations.
            lag (int): The time lag used for predictive decision-making.
            **kwargs: Additional arguments passed to the base providers.
        """
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

    def read_metrics_data(self):
        """
        Reads performance data filtered by the current time and window size.

        This method returns the recorded performance data for the current time window, filtering
        based on the `window` size defined in the configuration. If the current time exceeds the
        data end time, it returns None.

        Returns:
            pd.DataFrame: The filtered performance data for the current time window.
            None: If the current time exceeds the end time of the data.
        """
        if self.current_time > self.end_time:
            return None

        td_window = timedelta(minutes=self.config.general_config["window"])
        filtered_data = self.recorded_data.loc[self.current_time - td_window : self.current_time]

        self.logger.info("current_time: %s; filtered_data length: %s", self.current_time, len(filtered_data))
        return filtered_data

    def _get_all_performance_data(self):
        """
        Returns all performance data up to the current time.

        This method returns all available performance data until the current time, adjusting for any
        lag. If the current time exceeds the end time of the data, it returns None.

        Returns:
            pd.DataFrame: All performance data up to the current time.
            None: If the current time exceeds the end time of the data.
        """
        if self.current_time > self.end_time:
            return None

        filtered_data = self.recorded_data.loc[self.start_time : self.current_time]
        self.logger.info("current_time: %s; filtered_data length: %s", self.current_time, len(filtered_data))

        return filtered_data

    def get_next_recorded_data(self):
        """
        Retrieves the next set of recorded performance data.

        This method fetches the next available performance data from the predictive file provider
        and returns it along with the end time of the data.

        Returns:
            pd.DataFrame: The performance data within the window.
            pd.Timestamp: The end time of the performance data.
        """
        perf_data, end_time = PredictiveFileClusterStateProvider.get_next_recorded_data(self)
        return perf_data, end_time

    # pylint: disable=duplicate-code
    def flush_metrics_data(self, filename):
        """
        Writes the recorded performance data to a CSV file with a custom header.

        This method allows saving the performance metrics data to a specified CSV file for further
        analysis or reporting.

        Args:
            filename (str): The path to the CSV file where the metrics will be saved.
        """
        custom_header = "TIMESTAMP,CPU_USAGE_ACTUAL"

        with open(filename, "w", encoding="utf-8") as file:
            file.write(custom_header + "\n")
            self.recorded_data.to_csv(file, index=False, date_format="%Y.%m.%d-%H:%M:%S:%f", header=False)
