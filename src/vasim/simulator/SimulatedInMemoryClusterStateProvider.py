#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#

"""
Module Name: SimulatedInMemoryClusterStateProvider.

Description:
    The `SimulatedInMemoryClusterStateProvider` class is a hybrid implementation that combines both
    the `SimulatedBaseClusterStateProvider` and `FileClusterStateProvider`. It provides simulated cluster
    state management, allowing for in-memory simulation of scaling events based on performance data
    read from CSV files. The class manages time-based data filtering and allows the flushing of metrics to files.

Classes:
    SimulatedInMemoryClusterStateProvider:
        Extends both `SimulatedBaseClusterStateProvider` and `FileClusterStateProvider` to handle
        in-memory simulations of cluster state management.

Methods:
    __init__(data_dir="data/performance_log", window=40, decision_file_path=None, max_cpu_limit=None, lag=None, **kwargs):
        Initializes the class with parameters such as data directory, time window, and CPU limits.
        Calls the constructors of both `FileClusterStateProvider` and `SimulatedBaseClusterStateProvider`.

    get_next_recorded_data():
        Abstract method that should be implemented by subclasses to retrieve the next set of performance data.

    read_metrics_data():
        Reads and returns the recorded performance data filtered by the current time window.
        If the current time exceeds the end of the data, it returns None.

    flush_metrics_data(filename):
        Writes the recorded data to a CSV file with a custom header, allowing metrics to be stored
        for further analysis or auditing.

Parameters:
    data_dir (str):
        The directory where performance data CSV files are stored.
    window (int):
        The size of the time window for filtering data (in minutes).
    decision_file_path (str):
        The file path where decisions are recorded.
    max_cpu_limit (int):
        The maximum allowable CPU limit for scaling operations.
    lag (int):
        The time lag in minutes used for decision-making in the simulation.

Returns:
    The `read_metrics_data` method returns a filtered DataFrame containing the performance data
    for the current time window.
"""

from datetime import timedelta

from vasim.recommender.cluster_state_provider.FileClusterStateProvider import (
    FileClusterStateProvider,
)
from vasim.simulator.SimulatedBaseClusterStateProvider import (
    SimulatedBaseClusterStateProvider,
)


class SimulatedInMemoryClusterStateProvider(SimulatedBaseClusterStateProvider, FileClusterStateProvider):
    """
    A hybrid class combining `SimulatedBaseClusterStateProvider` and `FileClusterStateProvider` to manage.

    in-memory simulations of cluster state based on performance data read from CSV files. It supports
    scaling decisions and allows filtering of time-based performance data.

    Attributes:
        data_dir (str): Directory where performance data CSV files are stored.
        window (int): Time window size (in minutes) for filtering performance data.
        decision_file_path (str): Path where scaling decisions are logged.
        max_cpu_limit (int): Maximum CPU limit for scaling operations.
        lag (int): Time lag used in decision-making for simulation.
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
        Initialize the SimulatedInMemoryClusterStateProvider.

        This constructor initializes both the `FileClusterStateProvider` and `SimulatedBaseClusterStateProvider`
        to enable in-memory simulations of cluster state management.

        Args:
            data_dir (str): Directory where performance data CSV files are stored.
            window (int): Time window size (in minutes) for filtering performance data.
            decision_file_path (str): Path where scaling decisions are logged.
            max_cpu_limit (int): Maximum CPU limit for scaling operations.
            lag (int): Time lag used for decision-making in the simulation.
            **kwargs: Additional keyword arguments passed to the parent class constructors.
        """
        # pylint: disable=too-many-arguments

        FileClusterStateProvider.__init__(
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

    def get_next_recorded_data(self):
        """
        Abstract method to retrieve the next set of recorded performance data.

        This method should be implemented in subclasses to retrieve the next set of data
        for simulation purposes.

        Raises:
            NotImplementedError: If the method is not implemented in a subclass.
        """
        raise NotImplementedError()

    # pylint: disable=duplicate-code
    def read_metrics_data(self):
        """
        Read and return the recorded performance data filtered by the current time window.

        This method filters the recorded performance data based on the current time and window size.
        If the current time exceeds the end of the data, it returns None.

        Returns:
            pd.DataFrame: The filtered performance data for the current time window.
            None: If the current time exceeds the end of the data.
        """
        if self.current_time > self.end_time:
            return None

        td_window = timedelta(minutes=self.config.general_config["window"])
        filtered_data = self.recorded_data.loc[self.current_time - td_window : self.current_time]

        self.logger.info("current_time: %s; filtered_data length: %s", self.current_time, len(filtered_data))
        return filtered_data

    # pylint: disable=duplicate-code
    def flush_metrics_data(self, filename):
        """
        Write the recorded performance data to a CSV file with a custom header.

        This method writes the recorded performance data to a specified CSV file for auditing or analysis,
        with a custom header for easy identification of the data format.

        Args:
            filename (str): Path to the file where metrics will be saved.
        """
        custom_header = "TIMESTAMP,CPU_USAGE_ACTUAL"

        with open(filename, "w", encoding="utf-8") as file:
            file.write(custom_header + "\n")
            self.recorded_data.to_csv(file, index=False, date_format="%Y.%m.%d-%H:%M:%S:%f", header=False)
