import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from recommender.cluster_state_provider.ClusterStateProvider import ClusterStateProvider


class FileClusterStateProvider(ClusterStateProvider):
    """
    This class requires a Kubernetes cluster to run.
    It reads data from the cluster and uses it to make decisions.

    It is not part of the simulator, but is used in the production environment.

    TODO: Remove this file from the simulator package, but some of the code here is useful for the simulator.
    """

    def __init__(self, data_dir=None, features=["cpu"], window=40, decision_file_path=None, lag=5.0,
                 granularity=1, min_cpu_limit=1, max_cpu_limit=None, save_metadata=True, **kwargs):
        """
        Parameters:
            data_dir (str): The directory where the csvs are stored.
            features (list): The features to use for the model. Currently always ['cpu']. TODO: memory
            window (int): Window in minutes to capture VALID data in order to evaluate PP curve
            decision_file_path (str): The path to the file where Doppler will write decisions
            lag (float): Number of minutes to wait after making a decision
            granularity (int): Granularity desired for the price-performance curve, formerly "coredelta"
            min_cpu_limit (int): The minimum number of cores to recommend (When set to None it assumes 1)
            max_cpu_limit (int): The maximum number of cores to recommend. (When set to None, it assumes max on the machine)
            save_metadata (bool): Whether to save metadata to a file in the data_dir
        """

        if 'config' in kwargs and 'uuid' in kwargs['config']:
            # keyword argument 'param_name' exists
            self.config = kwargs['config']
            self.logger = logging.getLogger(f'{self.config.uuid}')
        else:
            self.logger = logging.getLogger()

        self.max_cpu_limit = max_cpu_limit
        if self.max_cpu_limit is None:
            # TODO: reimplement this to not be Azure-specific
            # self.max_cpu_limit = self.get_total_cpu()
            raise SystemExit('Must set max_cpu_limit to a value')

        self.data_dir = Path(data_dir) or Path().absolute() / "data"
        if list(self.data_dir.glob("**/*.csv")) == []:
            self.logger.error('Error: no csvs found in data_dir {}'.format(self.data_dir))
            raise SystemExit('Error: no csvs found in data_dir {}'.format(self.data_dir))
        self.features = features or []
        self.window = window
        self.decision_file_path = decision_file_path or "data/decisions.txt"
        self.lag = lag
        self.granularity = granularity
        self.min_cpu_limit = min_cpu_limit

        if save_metadata:
            meta_out_file = self.data_dir / "metadata.txt"
            meta = open(meta_out_file, "a")
            meta.write("max_cpu_limit: " + str(self.max_cpu_limit) + "\n")
            meta.write("features: " + str(self.features) + "\n")
            meta.write("window: " + str(self.window) + "\n")
            meta.write("lag: " + str(self.lag) + "\n")
            meta.write("granularity: " + str(self.granularity) + "\n")
            meta.write("min_cpu_limit: " + str(self.min_cpu_limit) + "\n")
            meta.close()
        self.save_metadata = save_metadata

    def get_current_cpu_limit(self):
        """
        Returns
        -------
        cores : int
            The number of cores currently being used.
        """
        try:

            def get_current_cpu_limit_pods():
                # TODO: reimplement this to not be Azure-specific
                pass
            cores, _ = get_current_cpu_limit_pods()[0]
        except Exception as e:
            self.logger.error(f'Error getting current cores. Retry later. {e}')
            print("Error getting current cores. Retry later.")
            print(e)
            return None

        return int(cores)

    def read_metrics_data(self):
        # Verify that csvs exist in the data_dir
        # TODO: This is not a scalable way to check for csvs
        # if the data is large, this will take a long time. Need to chunk.
        csv_paths = list(self.data_dir.glob("**/*.csv"))
        if csv_paths == []:
            self.logger.error(f'Error reading csvs from {self.data_dir}')

            print("Error reading csvs")
            return None, None

        # Process data
        recorded_data = self.process_data(csv_paths)
        return recorded_data

    def get_next_recorded_data(self):
        """
        Returns the performance data for the current time window.

        Returns
        -------
        recorded_data : pd.DataFrame
            The performance data for the current time window.
        end_time : datetime
            The end time of the current time window.
        """
        # Process data
        recorded_data = self.read_metrics_data()

        # Drop duplicates from data
        recorded_data = self.drop_duplicates(recorded_data)

        # Ensure data is sorted by time
        recorded_data = self.sort_data(recorded_data)

        # Check if the decisions file exists
        last_decision_time = self.get_last_decision_time(recorded_data)

        # Limit the data to a specified time window
        recorded_data, end_time = self.truncate_data(recorded_data, last_decision_time)

        # Validate recorded data
        if recorded_data is None or recorded_data.empty:
            self.logger.error("Error getting data. Exiting.")
            return None, None

        if recorded_data.shape[0] < 2:
            self.logger.error("Not enough data to make a decision. (May be due to warmup time).")
            return None, None

        # Additional guardrails to ensure valid telemetry
        if recorded_data.shape[0] > 2:
            # Filter out any data points that are greater than the machine max
            cores = self.get_current_cpu_limit()
            if cores is None:
                self.logger.error("Error getting current cores. Retry later.")
                return None, None
            recorded_data = recorded_data[recorded_data["cpu"] <= self.max_cpu_limit]

        return recorded_data, end_time

    def process_data(self, csv_paths):
        recorded_data = pd.DataFrame()
        for i, path in enumerate(csv_paths):
            path = str(path)
            # The CSVs must have the word "perf_event_log" in them, else we ignore
            # This is to prevent accidentally reading other CSVs in the directory
            if "perf_event_log" in path:
                try:
                    temp_data = pd.read_csv(path)
                    temp_data["cpu"] = temp_data["CPU_USAGE_ACTUAL"]
                    temp_data["time"] = temp_data["TIMESTAMP"].apply(
                        lambda x: datetime.strptime(x, "%Y.%m.%d-%H:%M:%S:%f"))
                    temp_data = temp_data[["time"] + self.features]
                    recorded_data = pd.concat([recorded_data, temp_data], axis=0)
                except Exception as e:
                    self.logger.error(f"Error reading {path} {e}")
                    continue
        return recorded_data

    def drop_duplicates(self, recorded_data):
        recorded_data = recorded_data.drop_duplicates()
        return recorded_data

    def sort_data(self, recorded_data):
        recorded_data["time"] = pd.to_datetime(recorded_data["time"])
        recorded_data = recorded_data.sort_values(by="time")
        return recorded_data

    def truncate_data(self, recorded_data, last_decision_time):
        end_time = recorded_data["time"].iloc[-1]

        num_observations = recorded_data.shape[0]
        if num_observations > 2:
            if last_decision_time > end_time:
                self.logger.warning(
                    "Last decision time is greater than end time so avoid making a decision"
                )
                return None, None

        start_time = end_time - timedelta(minutes=self.window)
        recorded_data = recorded_data[recorded_data["time"] >= start_time]
        recorded_data = recorded_data[recorded_data["time"] <= end_time]
        return recorded_data, end_time

    def create_resource_limits(self):
        # Infact I think we need to remove most of this file, as it won't be used in the simulator.
        vcpus_increments = self.max_cpu_limit * self.granularity + 1
        new_resource_limits = pd.DataFrame(
            data={"cpu": np.linspace(0, self.max_cpu_limit, num=vcpus_increments)})
        new_resource_limits[
            "new_price"] = new_resource_limits["cpu"]  # we removed price from the model
        # TODO: where is this used?
        new_resource_limits["sku"] = new_resource_limits["cpu"].apply(
            lambda x: str(round(x, 2)) + "vcpu")
        return new_resource_limits

    def get_last_decision_time(self, recorded_data):
        # Check if the decisions file exists
        if not os.path.exists(self.decision_file_path):
            self.logger.warning("No decisions file found!  Path was: {}".format(self.decision_file_path))
            last_decision_time = recorded_data["time"].iloc[0]
        else:
            # Read in the decisions txt file to see when the last decision was made
            decisions = pd.read_csv(self.decision_file_path)
            # Convert the LATEST_TIME into timestamps
            decisions["LATEST_TIME"] = pd.to_datetime(decisions["LATEST_TIME"])
            # Sort the LATEST_TIME column
            decisions = decisions.sort_values(by="LATEST_TIME")
            # Validate decisions by filtering out times greater than the end time
            decisions = decisions[decisions["LATEST_TIME"] < recorded_data["time"].iloc[-1]]

            if decisions.shape[0] < 1:
                self.logger.debug("No decisions made yet")
                last_decision_time = recorded_data["time"].iloc[0]
            else:
                # Identify the time point when the CURR_LIMIT changes (when a decision was enforced)
                new_limit_changes = decisions[
                    decisions["CURR_LIMIT"].shift(1) != decisions["CURR_LIMIT"]]

                # Get the last time a decision was made
                last_decision_time = new_limit_changes["LATEST_TIME"].iloc[-1]
                # Add the lag to the last decision time
                last_decision_time = last_decision_time + timedelta(minutes=self.lag)

        return last_decision_time

    def get_total_cpu(self):
        return self.max_cpu_limit
