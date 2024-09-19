#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#
import logging
from pathlib import Path

import pandas as pd

from vasim.recommender.cluster_state_provider.ClusterStateProvider import (
    ClusterStateProvider,
)


class SimulatedBaseClusterStateProvider(ClusterStateProvider):
    # pylint: disable=too-many-instance-attributes

    # TODO: I am not sure if this class is used? it is not tested if so.
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

        self.logger = logging.getLogger()
        self.logger.info("SimulatedBaseClusterStateProvider init")

        self.data_dir = (Path().absolute() / data_dir).absolute()
        self.decision_file_path = (Path().absolute() / decision_file_path).absolute()
        self.curr_cpu_limit = None  # set by initial_cores_count during the first scaling
        self.print_properties()
        self.config = kwargs.get("config")
        # TODO: these did not get updated to the new config format
        self.max_cpu_limit = max_cpu_limit
        self.lag = lag
        self.window = window

        # Read all data from file
        # TODO: This is a temporary solution. We will need to read data in chunks
        csv_paths = list(self.data_dir.glob("**/*.csv"))
        if not csv_paths:
            self.logger.error("Error reading csvs from %s. Your csv_paths are empty.", self.data_dir)
            print("Error reading csvs")
            raise FileNotFoundError(f"Error reading csvs from {self.data_dir}. Your csv_paths are empty.")

        # Process data
        self.recorded_data = self.process_data(csv_paths)
        self.start_time = pd.Timestamp(self.recorded_data["time"].iloc[0])
        self.end_time = pd.Timestamp(self.recorded_data["time"].iloc[-1])

        self.recorded_data["time"] = pd.to_datetime(self.recorded_data["time"])
        self.recorded_data["timeindex"] = self.recorded_data["time"]

        # self.recorded_data.set_index('time')  # Replace 'timestamp_column_name' with the actual column name of timestamps
        self.recorded_data.set_index("timeindex", inplace=True)
        self.current_time = self.start_time
        self.last_scaling_time = self.start_time

    def get_next_recorded_data(self):
        raise NotImplementedError()

    def set_cpu_limit(self, new_cpu_limit):
        if new_cpu_limit != self.curr_cpu_limit:
            self.last_scaling_time = self.current_time
        self.curr_cpu_limit = new_cpu_limit

    def get_index_pod_creation_timestamp(self):
        return self.last_scaling_time

    def print_properties(self):
        for key, value in vars(self).items():
            print(f"{key}: {value}")

    def get_current_cpu_limit(self):
        return self.curr_cpu_limit

    def get_total_cpu(self):
        return self.max_cpu_limit

    def flush_metrics_data(self, filename):
        # Create a custom header string
        custom_header = "TIMESTAMP,CPU_USAGE_ACTUAL"

        # Open the file for writing
        with open(filename, "w", encoding="utf-8") as file:
            # Write the custom header as the first line
            file.write(custom_header + "\n")

            # Use pandas to write the DataFrame data without a header
            self.recorded_data.to_csv(file, index=False, date_format="%Y.%m.%d-%H:%M:%S:%f", header=False)

    def get_last_decision_time(
        self,
        recorded_data,  # pylint: disable=unused-argument
    ):
        # check is redundant, but we keep it for now. This will speed up the simulation
        return pd.Timestamp(self.current_time) - pd.Timedelta(minutes=self.lag)

    def advance_time(self):
        self.current_time = pd.Timestamp(self.current_time) + pd.Timedelta(minutes=self.lag)
