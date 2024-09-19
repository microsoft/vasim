#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from vasim.recommender.cluster_state_provider.ClusterStateProvider import (
    ClusterStateProvider,
)


class FileClusterStateProvider(ClusterStateProvider):
    """
    This class requires a Kubernetes cluster to run.

    It reads data from the cluster and uses it to make decisions.

    It is not part of the simulator, but is used in the production environment.

    TODO: Remove this file from the simulator package, but some of the code here is used for the simulator.
    We need to separate the simulator code from the production code. Ideally, we still preserve the
    ability to run the simulator with a live k8s cluster.
    """

    def __init__(
        self,
        data_dir=None,
        features=None,
        window=40,
        decision_file_path=None,
        lag=5.0,
        min_cpu_limit=1,  # pylint: disable=unused-argument   # FIXME
        max_cpu_limit=None,  # pylint: disable=unused-argument   # FIXME
        save_metadata=True,
        **kwargs,
    ):
        # pylint: disable=too-many-arguments
        """
        Parameters:

            data_dir (str): The directory where the csvs are stored.
            features (list): The features to use for the model. Currently always ['cpu']. TODO: memory
            window (int): Window in minutes to capture VALID data in order to evaluate PP curve
            decision_file_path (str): The path to the file where Doppler will write decisions
            lag (float): Number of minutes to wait after making a decision
            min_cpu_limit (int): The minimum number of cores to recommend (When set to None it assumes 1)
            max_cpu_limit (int): The maximum number of cores to recommend. (When set to None, it assumes max on the machine)
            save_metadata (bool): Whether to save metadata to a file in the data_dir
        """
        if features is None:
            features = ["cpu"]

        if "config" in kwargs:
            # keyword argument 'param_name' exists
            self.config = kwargs["config"]

        self.logger = logging.getLogger()

        self.data_dir = Path(data_dir) or Path().absolute() / "data"
        if not list(self.data_dir.glob("**/*.csv")):
            self.logger.error("Error: no csvs found in data_dir %s", self.data_dir)
            raise SystemExit(f"Error: no csvs found in data_dir {self.data_dir}")
        # TODO: rename this, it's a bit confusing. It's not the features of the model, it's the features of the data.
        self.features = features or []
        # TODO: a lot of the code below needs testing
        self.decision_file_path = decision_file_path or "data/decisions.txt"
        self.save_metadata = save_metadata

    def get_current_cpu_limit(self):
        """
        ---

        cores : int
            The number of cores currently being used.
        """
        try:

            def get_current_cpu_limit_pods():
                # TODO: reimplement this to not be Azure-specific
                pass

            cores, _ = get_current_cpu_limit_pods()[0]
        except Exception as e:  # pylint: disable=broad-exception-caught  # FIXME
            self.logger.error("Error getting current cores. Retry later.", exc_info=e)
            print("Error getting current cores. Retry later.")
            print(e)
            return None

        return int(cores)

    def read_metrics_data(self):
        # Verify that csvs exist in the data_dir
        # TODO: This is not a scalable way to check for csvs
        # if the data is large, this will take a long time. Need to chunk.
        csv_paths = list(self.data_dir.glob("**/*.csv"))
        if not csv_paths:
            self.logger.error("Error reading csvs from %s", self.data_dir)

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
            # This is because sometimes the telemetry can be incorrect
            cores = self.get_current_cpu_limit()
            if cores is None:
                self.logger.error("Error getting current cores. Retry later.")
                return None, None
            recorded_data = recorded_data[recorded_data["cpu"] <= self.config.general_config["max_cpu_limit"]]

        return recorded_data, end_time

    def process_data(self, data=None):
        assert data is not None, "No data provided to process"
        assert isinstance(data, list), "Data must be a list"
        csv_paths = data
        recorded_data = pd.DataFrame()
        for _, csv_path in enumerate(csv_paths):
            path = str(csv_path)
            # The CSVs must have the word "perf_event_log" in them, else we ignore
            # This is to prevent accidentally reading other CSVs in the directory
            if "perf_event_log" in path:
                try:
                    temp_data = pd.read_csv(path)
                    temp_data["cpu"] = temp_data["CPU_USAGE_ACTUAL"]
                    temp_data["time"] = temp_data["TIMESTAMP"].apply(lambda x: datetime.strptime(x, "%Y.%m.%d-%H:%M:%S:%f"))
                    temp_data = temp_data[["time"] + self.features]
                    recorded_data = pd.concat([recorded_data, temp_data], axis=0)
                except Exception as e:  # pylint: disable=broad-exception-caught  # FIXME
                    self.logger.error("Error reading %s", path, exc_info=e)
                    continue
        return recorded_data

    def truncate_data(self, recorded_data, last_decision_time):
        end_time = recorded_data["time"].iloc[-1]

        num_observations = recorded_data.shape[0]
        if num_observations > 2:
            if last_decision_time > end_time:
                self.logger.warning("Last decision time is greater than end time so avoid making a decision")
                return None, None

        start_time = end_time - timedelta(minutes=self.config.general_config["window"])
        recorded_data = recorded_data[recorded_data["time"] >= start_time]
        recorded_data = recorded_data[recorded_data["time"] <= end_time]
        return recorded_data, end_time

    def get_last_decision_time(self, recorded_data):
        # Check if the decisions file exists
        if not os.path.exists(self.decision_file_path):
            self.logger.warning("No decisions file found!  Path was: %s", self.decision_file_path)
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
                new_limit_changes = decisions[decisions["CURR_LIMIT"].shift(1) != decisions["CURR_LIMIT"]]

                # Get the last time a decision was made
                last_decision_time = new_limit_changes["LATEST_TIME"].iloc[-1]
                # Add the lag to the last decision time
                last_decision_time = last_decision_time + timedelta(minutes=self.config.general_config["lag"])

        return last_decision_time

    def get_total_cpu(self):
        # TODO: this function makes less sense in the context of the simulator
        return self.config.general_config["max_cpu_limit"]
