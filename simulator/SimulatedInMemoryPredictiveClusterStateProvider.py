import logging
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from recommender.cluster_state_provider.FileClusterStateProvider import FileClusterStateProvider
from recommender.cluster_state_provider.PredictiveFileClusterStateProvider import PredictiveFileClusterStateProvider
from simulator.SimulatedBaseClusterStateProvider import SimulatedBaseClusterStateProvider


class SimulatedInMemoryPredictiveClusterStateProvider(SimulatedBaseClusterStateProvider, PredictiveFileClusterStateProvider):
    def __init__(self, data_dir="data/performance_log", window=40, decision_file_path=None,
                 max_cpu_limit=None, granularity=None, lag=None, **kwargs):
        PredictiveFileClusterStateProvider.__init__(
            self, data_dir=data_dir, window=window, decision_file_path=decision_file_path, granularity=granularity, max_cpu_limit=max_cpu_limit, lag=lag, **kwargs)
        SimulatedBaseClusterStateProvider.__init__(
            self, data_dir=data_dir, window=window, decision_file_path=decision_file_path, granularity=granularity, max_cpu_limit=max_cpu_limit, lag=lag, **kwargs)

    # we read updated file every time
    def read_metrics_data(self):
        # Return data till current time
        if self.current_time > self.end_time:
            return None

        # Add lag to current time
        filtered_data = self.recorded_data.loc[self.current_time - timedelta(minutes=self.window + 5):self.current_time]

        # adjust last lag to cores
        self.recorded_data.loc[self.current_time - timedelta(minutes=self.lag):self.current_time,
                               'cpu'] = np.minimum(self.recorded_data['cpu'], self.curr_cpu_limit)

        self.logger.info(f"current_time: {self.current_time}; filtered_data length: {len(filtered_data)}")
        return filtered_data

    def _get_all_performance_data(self):
        # return data till current time
        if self.current_time > self.end_time:
            return None

        # add lag to current time
        filtered_data = self.recorded_data.loc[self.start_time:self.current_time]
        self.logger.info(f"current_time: {self.current_time}; filtered_data length: {len(filtered_data)}")

        return filtered_data

    def get_next_recorded_data(self):
        """
        Returns the performance data inside the window and the last time in the data
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
        with open(filename, 'w') as file:
            # Write the custom header as the first line
            file.write(custom_header + '\n')

            # Use pandas to write the DataFrame data without a header
            self.recorded_data.to_csv(file, index=False, date_format='%Y.%m.%d-%H:%M:%S:%f', header=False)
