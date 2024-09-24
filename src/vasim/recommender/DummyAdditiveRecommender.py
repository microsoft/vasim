#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#

"""
This module contains the SimpleAdditiveRecommender class, which implements.

a basic additive-based recommendation system for scaling decisions.

The recommender system processes recorded CPU usage data, calculates the
maximum usage, and adds a configurable buffer (addend) to compute a new
recommended CPU usage limit. The result is rounded to the nearest 0.5 cores
to ensure precise control over scaling decisions.

Classes:
    SimpleAdditiveRecommender: A class that applies an additive buffer to
    the maximum observed CPU usage to recommend scaling limits.
"""

import numpy as np

from vasim.recommender.Recommender import Recommender


class SimpleAdditiveRecommender(Recommender):
    # pylint: disable=too-few-public-methods
    """A recommender that scales CPU usage by adding a buffer to the maximum observed usage."""

    def __init__(self, cluster_state_provider, save_metadata=True):
        """
        Initialize the SimpleAdditiveRecommender class.

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
        Run the recommender algorithm and return the new number of cores to scale to (new limit).

        Parameters:
            recorded_data (pd.DataFrame): The recorded metrics data for the current time window to simulate.

        Returns:
            new_limit (float): The new number of cores to scale to.
        """

        # Calculate the smoothed maximum value from the CPU data.
        smoothed_max = recorded_data["cpu"].to_numpy().max()

        # Add the addend to the smoothed maximum to get the new number of cores.
        # The addend provides a buffer to the maximum value.
        new_limit = self.addend + smoothed_max

        # Round the new limit to the nearest 0.5 core, rounding up.
        new_limit = np.ceil(new_limit * 2) / 2

        self.logger.debug("Smoothed max: %s, New cpu limit: %s", smoothed_max, new_limit)

        return new_limit
