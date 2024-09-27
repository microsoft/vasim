#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#

"""
Module Name: SimulatedClusterStateProviderFactory.

Description:
    The `SimulatedClusterStateProviderFactory` class is responsible for creating instances of different
    simulated cluster state providers. Depending on the `predictive` flag, it can create either a
    predictive or non-predictive in-memory cluster state provider for use in simulations.

Classes:
    SimulatedClusterStateProviderFactory:
        A factory class for creating simulated cluster state providers, which can be either predictive
        or non-predictive depending on the configuration.

Attributes:
    config (ClusterStateConfig):
        The cluster state configuration containing general settings and prediction configurations.
    data_dir (str):
        Directory where performance data is stored.
    out_filename (str):
        Path to the output file where decisions will be logged.
    prediction_config (dict):
        Prediction-related configuration details extracted from the main config (if applicable).

Methods:
    __init__(data_dir: str, out_filename: str, config: ClusterStateConfig):
        Initializes the factory with the data directory, output filename, and cluster state configuration.

    create_provider(predictive: bool) -> SimulatedBaseClusterStateProvider:
        Creates and returns an instance of `SimulatedBaseClusterStateProvider`. If `predictive` is set to True,
        it creates a `SimulatedInMemoryPredictiveClusterStateProvider`, otherwise, it creates a
        `SimulatedInMemoryClusterStateProvider`.
"""

from vasim.recommender.cluster_state_provider.ClusterStateConfig import (
    ClusterStateConfig,
)
from vasim.simulator.SimulatedBaseClusterStateProvider import (
    SimulatedBaseClusterStateProvider,
)
from vasim.simulator.SimulatedInMemoryClusterStateProvider import (
    SimulatedInMemoryClusterStateProvider,
)
from vasim.simulator.SimulatedInMemoryPredictiveClusterStateProvider import (
    SimulatedInMemoryPredictiveClusterStateProvider,
)


class SimulatedClusterStateProviderFactory:
    """
    A factory class for creating simulated cluster state providers.

    Depending on the `predictive` flag, this factory can create either a predictive or
    non-predictive in-memory cluster state provider for simulations.

    Attributes:
        config (ClusterStateConfig): The configuration for the cluster state provider, containing
                                     general settings and prediction configurations.
        data_dir (str): Directory where performance data is stored.
        out_filename (str): Path to the output file where decisions are logged.
        prediction_config (dict): A dictionary containing prediction-related configuration details.
    """

    # pylint: disable=too-few-public-methods
    def __init__(self, data_dir: str, out_filename: str, config: ClusterStateConfig):
        """
        Initialize the SimulatedClusterStateProviderFactory.

        This method initializes the factory with the given data directory, output filename, and
        cluster state configuration. If prediction configuration is detected, it is stored for
        use in predictive simulations.

        Args:
            data_dir (str): Directory where performance data is stored.
            out_filename (str): Path to the output file where decisions will be logged.
            config (ClusterStateConfig): Cluster state configuration containing general and prediction
                                         settings.
        """
        self.config = config
        self.data_dir = data_dir
        self.out_filename = out_filename
        if config.prediction_config:
            self.prediction_config = config.prediction_config
            print(f"Prediction config was detected: {self.prediction_config}")

    def create_provider(self, predictive: bool) -> SimulatedBaseClusterStateProvider:
        """
        Create and return an instance of a simulated cluster state provider.

        If the `predictive` flag is True, this method creates an instance of
        `SimulatedInMemoryPredictiveClusterStateProvider`, otherwise it creates a
        `SimulatedInMemoryClusterStateProvider`.

        Args:
            predictive (bool): A flag indicating whether to create a predictive provider or a
                               non-predictive provider.

        Returns:
            SimulatedBaseClusterStateProvider: An instance of either a predictive or non-predictive
                                               cluster state provider.
        """
        if predictive:
            return SimulatedInMemoryPredictiveClusterStateProvider(
                data_dir=self.data_dir,
                prediction_config=self.prediction_config,
                max_cpu_limit=self.config.general_config["max_cpu_limit"],
                decision_file_path=self.out_filename,
                lag=self.config.general_config["lag"],
                window=self.config.general_config["window"],
                min_cpu_limit=self.config.general_config["min_cpu_limit"],
                config=self.config,
            )
        else:
            return SimulatedInMemoryClusterStateProvider(
                data_dir=self.data_dir,
                max_cpu_limit=self.config.general_config["max_cpu_limit"],
                decision_file_path=self.out_filename,
                lag=self.config.general_config["lag"],
                window=self.config.general_config["window"],
                min_cpu_limit=self.config.general_config["min_cpu_limit"],
                config=self.config,
            )
