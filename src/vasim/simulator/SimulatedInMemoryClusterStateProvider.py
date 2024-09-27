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
        raise NotImplementedError()

    def read_metrics_data(self):
        # Return data till current time
        if self.current_time > self.end_time:
            return None

        # Get the data based on the window size and current time
        # TODO: sanity checks on 'window' user inputs
        td_window = timedelta(minutes=self.config.general_config["window"])
        filtered_data = self.recorded_data.loc[self.current_time - td_window : self.current_time]

        self.logger.info("current_time: %s; filtered_data length: %s", self.current_time, len(filtered_data))
        return filtered_data

    def flush_metrics_data(self, filename):
        # Create a custom header string
        custom_header = "TIMESTAMP,CPU_USAGE_ACTUAL"

        # Open the file for writing
        with open(filename, "w", encoding="utf-8") as file:
            # Write the custom header as the first line
            file.write(custom_header + "\n")

            # Use pandas to write the DataFrame data without a header
            self.recorded_data.to_csv(file, index=False, date_format="%Y.%m.%d-%H:%M:%S:%f", header=False)
