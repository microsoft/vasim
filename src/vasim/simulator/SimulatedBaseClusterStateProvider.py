#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#

"""
Module Name: SimulatedBaseClusterStateProvider.

Description:
    The `SimulatedBaseClusterStateProvider` class is a base class designed for simulating a cluster state provider
    that reads performance data from CSV files and manages CPU limits in a simulated environment. It handles time
    advancement, data processing, and scaling decisions in a simulation setting.

Classes:
    SimulatedBaseClusterStateProvider:
        Provides methods for managing simulated cluster performance data, setting CPU limits, advancing time,
        and flushing metrics to CSV files. This class is used in simulations to replicate real-world
        scenarios for testing recommender system policies.

Attributes:
    data_dir (Path): Directory where the performance log CSV files are stored.
    decision_file_path (Path): Path to the file where decisions are logged.
    curr_cpu_limit (int): Current CPU limit set during scaling operations.
    max_cpu_limit (int): Maximum allowable CPU limit.
    lag (int): Time lag used in decision-making.
    window (int): Window of time used to evaluate cluster performance data.
    recorded_data (pd.DataFrame): DataFrame containing the recorded performance data.
    start_time (Timestamp): Start time of the recorded data.
    end_time (Timestamp): End time of the recorded data.
    current_time (Timestamp): Current simulated time.
    last_scaling_time (Timestamp): Last time a scaling operation was performed.

Methods:
    __init__(data_dir="data/performance_log", window=40, decision_file_path=None, max_cpu_limit=None, lag=None, **kwargs):
        Initializes the `SimulatedBaseClusterStateProvider` with specified parameters like the data directory,
        window size, and maximum CPU limit. Loads performance data from CSV files in the `data_dir`.

    get_next_recorded_data():
        Abstract method to be implemented by subclasses to fetch the next set of recorded data.

    set_cpu_limit(new_cpu_limit):
        Sets a new CPU limit for the cluster. Updates the scaling time if the CPU limit changes.

    get_index_pod_creation_timestamp():
        Returns the timestamp of the last scaling operation.

    print_properties():
        Prints the properties of the instance for debugging and testing purposes.

    get_current_cpu_limit():
        Returns the current CPU limit.

    get_total_cpu():
        Returns the total maximum CPU limit for the cluster.

    flush_metrics_data(filename):
        Writes the recorded data to a CSV file with a custom header.

    get_last_decision_time(recorded_data):
        Returns the last decision time, calculated using the current time and lag.

    advance_time():
        Advances the current simulated time by the specified lag value.
"""

import logging
from pathlib import Path

import pandas as pd

from vasim.commons.utils import list_perf_event_log_files
from vasim.recommender.cluster_state_provider.ClusterStateProvider import (
    ClusterStateProvider,
)


class SimulatedBaseClusterStateProvider(ClusterStateProvider):
    """
    SimulatedBaseClusterStateProvider simulates a cluster state provider by reading performance.

    data from CSV files and managing CPU limits in a simulated environment. It provides methods
    for advancing time, processing data, and making scaling decisions based on the data.

    Attributes:
        data_dir (Path): Directory where the performance log CSV files are stored.
        decision_file_path (Path): Path to the file where decisions are logged.
        curr_cpu_limit (int): Current CPU limit set during scaling operations.
        max_cpu_limit (int): Maximum allowable CPU limit.
        lag (int): Time lag used in decision-making.
        window (int): Window of time used to evaluate cluster performance data.
        recorded_data (pd.DataFrame): DataFrame containing the recorded performance data.
        start_time (Timestamp): Start time of the recorded data.
        end_time (Timestamp): End time of the recorded data.
        current_time (Timestamp): Current simulated time.
        last_scaling_time (Timestamp): Last time a scaling operation was performed.
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
        Initialize the `SimulatedBaseClusterStateProvider`.

        Args:
            data_dir (str): Directory where performance log CSV files are stored.
            window (int): Window size for evaluating cluster performance data.
            decision_file_path (str): Path to the decision log file.
            max_cpu_limit (int): Maximum allowable CPU limit.
            lag (int): Time lag used in decision-making.
            **kwargs: Additional configuration options.
        """
        # pylint: disable=too-many-arguments

        self.logger = logging.getLogger()
        self.logger.info("SimulatedBaseClusterStateProvider init")

        self.data_dir = (Path().absolute() / data_dir).absolute()
        self.decision_file_path = (Path().absolute() / decision_file_path).absolute()
        self.curr_cpu_limit = None  # set by initial_cores_count during the first scaling
        self.print_properties()
        self.config = kwargs.get("config")
        self.max_cpu_limit = max_cpu_limit
        self.lag = lag
        self.window = window

        csv_paths = list_perf_event_log_files(self.data_dir)
        if not csv_paths:
            self.logger.error("Error reading csvs from %s. Your csv_paths are empty.", self.data_dir)
            raise FileNotFoundError(f"Error reading csvs from {self.data_dir}. Your csv_paths are empty.")

        self.recorded_data = self.process_data(csv_paths)
        self.start_time = pd.Timestamp(self.recorded_data["time"].iloc[0])
        self.end_time = pd.Timestamp(self.recorded_data["time"].iloc[-1])

        self.recorded_data["time"] = pd.to_datetime(self.recorded_data["time"])
        self.recorded_data["timeindex"] = self.recorded_data["time"]

        self.recorded_data.set_index("timeindex", inplace=True)
        self.current_time = self.start_time
        self.last_scaling_time = self.start_time

    def get_next_recorded_data(self):
        """
        Abstract method to fetch the next set of recorded data from the performance logs.

        This method needs to be implemented in subclasses.

        Raises:
            NotImplementedError: If the method is not implemented in a subclass.
        """
        raise NotImplementedError()

    def set_cpu_limit(self, new_cpu_limit):
        """
        Set a new CPU limit for the cluster.

        Args:
            new_cpu_limit (int): The new CPU limit to set.

        If the new CPU limit differs from the current CPU limit, the `last_scaling_time`
        is updated to the current simulated time.
        """
        if new_cpu_limit != self.curr_cpu_limit:
            self.last_scaling_time = self.current_time
        self.curr_cpu_limit = new_cpu_limit

    def get_index_pod_creation_timestamp(self):
        """
        Retrieve the timestamp of the last scaling operation.

        Returns:
            Timestamp: The time of the last scaling operation.
        """
        return self.last_scaling_time

    def print_properties(self):
        """Print the properties of the SimulatedBaseClusterStateProvider instance for debugging."""
        for key, value in vars(self).items():
            print(f"{key}: {value}")

    def get_current_cpu_limit(self):
        """
        Retrieve the current CPU limit for the cluster.

        Returns:
            int: The current CPU limit.
        """
        return self.curr_cpu_limit

    def get_total_cpu(self):
        """
        Retrieve the total maximum CPU limit for the cluster.

        Returns:
            int: The maximum CPU limit.
        """
        return self.max_cpu_limit

    def flush_metrics_data(self, filename):
        """
        Write the recorded performance data to a CSV file with a custom header.

        Args:
            filename (str): The path to the file where metrics will be saved.
        """
        custom_header = "TIMESTAMP,CPU_USAGE_ACTUAL"

        with open(filename, "w", encoding="utf-8") as file:
            file.write(custom_header + "\n")
            self.recorded_data.to_csv(file, index=False, date_format="%Y.%m.%d-%H:%M:%S:%f", header=False)

    def get_last_decision_time(self, recorded_data=None):  # pylint: disable=unused-argument
        """
        Calculate the last decision time based on the current time and lag.

        Args:
            recorded_data (pd.DataFrame): DataFrame containing the recorded performance data (currently unused).

        Returns:
            Timestamp: The last decision time.
        """
        return pd.Timestamp(self.current_time) - pd.Timedelta(minutes=self.lag)

    def advance_time(self):
        """Advance the current simulated time by the lag value."""
        self.current_time = pd.Timestamp(self.current_time) + pd.Timedelta(minutes=self.lag)
