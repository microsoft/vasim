#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#

import numpy as np

from vasim.recommender.Recommender import Recommender


class SimpleAdditiveRecommender(Recommender):
    """Simple Additive Recommender class."""

    # pylint: disable=too-few-public-methods

    def __init__(self, cluster_state_provider, save_metadata=True):
        """
        Parameters:

            cluster_state_provider (ClusterStateProvider): The cluster state provider such as FileClusterStateProvider.
            save_metadata (bool): Whether to save metadata to a file.
        """
        super().__init__(cluster_state_provider, save_metadata)

        # User parameters go here. They are available in self.algo_params
        # Default addend is 2. This is the buffer to the maximum value.
        self.addend = self.algo_params.get("addend", 2)

    def run(self, recorded_data):
        """
        This method runs the recommender algorithm and returns the new number of cores to scale to (new limit).

        Inputs:
            recorded_data (pd.DataFrame): The recorded metrics data for the current time window to simulate
        Returns:
            latest_time (datetime): The latest time of the performance data.
            new_limit (float): The new number of cores to scale to.
        """

        # Calculate the smoothed maximum value. This will look at all the cores in the
        # performance data window and take the maximum value.
        smoothed_max = recorded_data["cpu"].to_numpy().max()

        # Add the addend to the smoothed maximum to get the new number of cores
        # The Addend provides a buffer to the maximum value.
        new_limit = self.addend + smoothed_max

        # Now round the scaling factor to the nearest 0.5 core. Always round up.
        new_limit = np.ceil(new_limit * 2) / 2

        self.logger.debug("Smoothed max: %s, New cpu limit: %s", smoothed_max, new_limit)

        return new_limit
