import logging
import numpy as np
import pandas as pd
from recommender.Recommender import Recommender


class SimpleAdditiveRecommender(Recommender):
    def __init__(self, cluster_state_provider, config, save_metadata=True):
        super().__init__(cluster_state_provider, config, save_metadata)
        """
        Parameters:
            cluster_state_provider (ClusterStateProvider): The cluster state provider such as FileClusterStateProvider.
            config (dict): Configuration dictionary with parameters for the recommender.
            save_metadata (bool): Whether to save metadata to a file.
        """

        # For now, we are just passing the cluster_state_provider and config for logging purposes.
        # TODO: Consider refactoring the logging to be more consistent across all classes.
        self.cluster_state_provider = cluster_state_provider
        if hasattr(self.cluster_state_provider, 'config') and self.cluster_state_provider.config is not None \
                and hasattr(self.cluster_state_provider.config, "uuid"):
            self.logger = logging.getLogger(f'{self.cluster_state_provider.config.uuid}')
        else:
            self.logger = logging.getLogger()

        # User parameters go here
        self.addend = config.get("addend", 2)  # Default addend is 2. This is the buffer to the maximum value.

    def run(self, recorded_data):
        """
        This method runs the recommender algorithm and returns the new number of cores to scale to (new limit).

        Inputs:
            recorded_data (pd.DataFrame): The recorded metrics data for the current time window to simulate
        Returns:
            latest_time (datetime): The latest time of the performance data.
            new_limit (int): The new number of cores to scale to.
        """

        # Calculate the smoothed maximum value. This will look at all the cores in the
        # performance data window and take the maximum value.
        smoothed_max = recorded_data['cpu'].to_numpy().max()

        # Add the addend to the smoothed maximum to get the new number of cores
        # The Addend provides a buffer to the maximum value.
        new_limit = self.addend + smoothed_max

        # Now round the scaling factor to the nearest 0.5 core. Always round up.
        new_limit = np.ceil(new_limit * 2) / 2

        self.logger.debug(f"Smoothed max: {smoothed_max}, New cpu limit: {new_limit}")

        return new_limit
