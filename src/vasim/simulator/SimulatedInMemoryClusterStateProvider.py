#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#
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
