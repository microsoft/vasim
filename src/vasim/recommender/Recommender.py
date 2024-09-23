#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#
import logging
import os
from abc import abstractmethod


class Recommender:
    # pylint: disable=too-few-public-methods
    def __init__(self, cluster_state_provider, save_metadata=True):
        """
        This is the base class for all recommender algorithms.

        Parameters:
            cluster_state_provider (ClusterStateProvider): The cluster state provider such as FileClusterStateProvider.
            save_metadata (bool): Whether to save metadata to a file. For tuning this makes tracking easier.
        """

        # For now, we are just passing the cluster_state_provider and config for logging purposes.
        #       Ex: we need the path in self.cluster_state_provider.config.uuid to save the logging/metadata during tuning
        self.cluster_state_provider = cluster_state_provider
        self.config = self.cluster_state_provider.config

        # This is for user convenience. They can pass the parameters in the config file. But maybe it's confusing/redundant.
        self.algo_params = self.config.algo_specific_config

        self.logger = self._setup_logger()

        if save_metadata:
            self._save_metadata()

    def _setup_logger(self):
        # TODO: I think we can simplify this by just using the config.uuid as the logger name
        if (
            hasattr(self.cluster_state_provider, "config")
            and self.cluster_state_provider.config is not None
            and hasattr(self.cluster_state_provider.config, "uuid")
        ):
            return logging.getLogger(f"{self.cluster_state_provider.config.uuid}")
        else:
            return logging.getLogger()

    def _save_metadata(self):
        # Save metadata to a JSON file

        # We need to save it close to decision file, which would be target file.
        # We need to refactor it, but we will detect the decision file path and save it there to avoid changing interfaces
        target_dir = os.path.dirname(self.cluster_state_provider.decision_file_path)
        self.config.to_json(f"{target_dir}/metadata.json")

    @abstractmethod
    def run(self, recorded_data):
        """
        This function is not intended to be called directly.

        It is an example of the method that should be implemented.

        This method runs the recommender algorithm and returns the new number of cores to scale to.

        Inputs:
            recorded_data (pd.DataFrame): The recorded metrics data for the current time window to simulate
        Returns:
            latest_time (datetime): The latest time of the performance data.
            new_limit (float): The new number of cores to scale to.
        """
        # # Do something here with the recorded_data to determine the new limit.
        # # The recorded_data is a pandas DataFrame with columns like timestamp, cpu_usage, etc.
        # # For example, you could use a machine learning model to predict the new limit.

        # # new_limit = some_ml_algorithm(recorded_data)

        # # We also need to return the latest time for a sanity check.
        # # return new_limit

        # This is an abstract method and should be implemented in a subclass
        raise NotImplementedError("Implement run() method in a subclass")
