#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#

import numpy as np

from vasim.recommender.Recommender import Recommender


class SimpleMultiplierRecommender(Recommender):
    def __init__(self, cluster_state_provider, save_metadata=True):
        """
        Parameters:

            cluster_state_provider (ClusterStateProvider): The cluster state provider such as FileClusterStateProvider.
            save_metadata (bool): Whether to save metadata to a file.
        """
        super().__init__(cluster_state_provider, save_metadata)

        # User parameters go here. They are available in self.algo_params
        self.multiplier = self.algo_params.get("multiplier", 1.5)  # Default multiplier is 1.5
        # Here is an example of accessing the general config in addition to the algo
        # specific config/user params.
        # (In this case, we didn't add smoothing_window to the algo specific
        # config), so we use the general config as a fallback.
        self.smoothing_window = self.algo_params.get(
            "smoothing_window",
            self.config.get("general_config", {}).get("window", 5),
        )

    def run(self, recorded_data):
        """
        This method runs the recommender algorithm and returns the new number of cores to scale to (new limit).

        Inputs:
            recorded_data (pd.DataFrame): The recorded metrics data for the current time window to simulate
        Returns:
            latest_time (datetime): The latest time of the performance data.
            new_limit (float): The new number of cores to scale to.
        """

        # Calculate the smoothed maximum value
        smoothed_max = self.calculate_smoothed_max(recorded_data)

        # Multiply the smoothed max by multiplier to get the desired CPU usage
        new_limit = self.multiplier * smoothed_max

        # Now round the new_limit (2* the used cores) to the nearest 0.5 core. Always round up.
        new_limit = np.ceil(new_limit * 2) / 2

        self.logger.debug("Smoothed max: %s, Scaling factor: %s", smoothed_max, new_limit)

        return new_limit

    def calculate_smoothed_max(self, recorded_data):
        # Smooth the data by applying a rolling mean
        smoothed_data = recorded_data["cpu"].rolling(window=self.smoothing_window, min_periods=1).mean()

        # Get the maximum value from the smoothed data
        smoothed_max = smoothed_data.max()

        self.logger.debug("Calculated smoothed max: %s", smoothed_max)

        return smoothed_max
