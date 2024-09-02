import logging
import numpy as np
import pandas as pd
from recommender.Recommender import Recommender


class SimpleMultiplierRecommender(Recommender):
    def __init__(self, cluster_state_provider, config, save_metadata=True):
        """
        Parameters:
            cluster_state_provider (ClusterStateProvider): The cluster state provider such as FileClusterStateProvider.
            config (dict): Configuration dictionary with parameters for the recommender.
            save_metadata (bool): Whether to save metadata to a file.
        """
        super().__init__(cluster_state_provider, config, save_metadata)

        # For now, we are just passing the cluster_state_provider and config for logging purposes.
        # TODO: Consider refactoring the logging to be more consistent across all classes.
        self.cluster_state_provider = cluster_state_provider
        if hasattr(self.cluster_state_provider, 'config') and self.cluster_state_provider.config is not None \
                and hasattr(self.cluster_state_provider.config, "uuid"):
            self.logger = logging.getLogger(f'{self.cluster_state_provider.config.uuid}')
        else:
            self.logger = logging.getLogger()

        # User parameters go here
        # Default smoothing window is 5. This is the number of data points to consider for smoothing.
        self.smoothing_window = config.get("smoothing_window", config.get("general_config", {}).get("window", 5))
        # TODO: this isn't in json for now. make a new json separetely for this test
        self.multiplier = config.get("general_config", {}).get("multiplier", 2)  # Default multiplier is 2

    def run(self, recorded_data):
        """
        This method runs the recommender algorithm and returns the new number of cores to scale to (new limit).

        Inputs:
            recorded_data (pd.DataFrame): The recorded metrics data for the current time window to simulate
        Returns:
            latest_time (datetime): The latest time of the performance data.
            new_limit (int): The new number of cores to scale to.
        """

        # Calculate the smoothed maximum value
        smoothed_max = self.calculate_smoothed_max(recorded_data)

        # Multiply the smoothed max by multiplier to get the desired CPU usage
        new_limit = self.multiplier * smoothed_max

        # Now round the new_limit (2* the used cores) to the nearest 0.5 core. Always round up.
        new_limit = np.ceil(new_limit * 2) / 2

        self.logger.debug(f"Smoothed max: {smoothed_max}, Scaling factor: {new_limit}")

        return new_limit

    def calculate_smoothed_max(self, recorded_data):
        # Smooth the data by applying a rolling mean
        smoothed_data = recorded_data['cpu'].rolling(window=self.smoothing_window, min_periods=1).mean()

        # Get the maximum value from the smoothed data
        smoothed_max = smoothed_data.max()

        self.logger.debug(f"Calculated smoothed max: {smoothed_max}")

        return smoothed_max
