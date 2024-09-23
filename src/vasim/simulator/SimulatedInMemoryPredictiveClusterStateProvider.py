#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#
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
