#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#

"""
Module Name: SimulatedInfraScaler.

Description:
    The `SimulatedInfraScaler` class simulates the process of scaling infrastructure in a cluster environment.
    It introduces a delay (recovery time) after each scaling event to mimic the time taken by real systems to
    provision and warm up new resources. This ensures that the simulation reflects real-world scaling behavior,
    preventing frequent and costly scaling events.

Classes:
    SimulatedInfraScaler:
        Provides methods to scale a simulated cluster based on system decisions, while adhering to recovery
        periods and core limits.

Attributes:
    cluster_state_provider (ClusterStateProvider):
        The cluster state provider that manages the current CPU limit and scaling decisions.
    last_scaling_time (datetime):
        Timestamp of the last scaling event.
    start_time (datetime):
        The starting time of the simulation.
    recovery_time (int):
        The time in minutes it takes for the system to recover after a scaling event.
    logger (Logger):
        A logger object for logging scaling decisions and events.

Methods:
    __init__(cluster_state_provider, start_timestamp, recovery_time):
        Initializes the `SimulatedInfraScaler` with a cluster state provider, the start timestamp, and a recovery time.

    scale(new_limit, time_now):
        Attempts to scale the cluster to a new CPU limit. This method only performs the scaling if the
        recovery time has passed since the last scaling event and ensures that the new limit does not exceed
        minimum or maximum core limits.

        Parameters:
            new_limit (int): The new number of cores to scale to.
            time_now (datetime): The current timestamp.

        Returns:
            bool: Returns True if scaling was successful, otherwise False.
"""
import logging
from pathlib import Path


class SimulatedInfraScaler:
    # pylint: disable=too-few-public-methods
    """
    Simulates the infrastructure scaling process in a cluster.

    The `SimulatedInfraScaler` class introduces a recovery time after each scaling event to simulate
    the delay in provisioning and warming up new resources, making the simulation more realistic. The class
    ensures that scaling only happens if the required recovery time has passed, and it enforces minimum
    and maximum core limits for scaling decisions.

    Attributes:
        cluster_state_provider (ClusterStateProvider): The cluster state provider that manages the CPU limit.
        last_scaling_time (datetime): Timestamp of the last scaling event.
        start_time (datetime): The starting time of the simulation.
        recovery_time (int): Time in minutes required for recovery after a scaling event.
        logger (Logger): A logger object to log scaling decisions and events.
    """

    def __init__(self, cluster_state_provider, start_timestamp, recovery_time):
        """
        Initialize the SimulatedInfraScaler.

        This method sets up the simulated infra scaler with the cluster state provider, starting
        timestamp, and the recovery time. It configures the logger to store logs in the simulation's
        output directory.

        Args:
            cluster_state_provider (ClusterStateProvider): The cluster state provider managing CPU limits.
            start_timestamp (datetime): The starting time of the simulation.
            recovery_time (int): The recovery time in minutes after each scaling event.
        """
        self.cluster_state_provider = cluster_state_provider
        self.last_scaling_time = None
        self.start_time = start_timestamp
        self.recovery_time = recovery_time

        # Set up logging in the target path, so it will be stored with the simulation data
        log_file = Path(self.cluster_state_provider.decision_file_path).parent.joinpath("updatelog.txt")
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(logging.FileHandler(log_file))

        # Write a test message to confirm logger is initialized
        self.logger.info(">>>SimulatedInfraScaler initialized")

    def scale(self, new_limit, time_now):
        """
        Scale the simulated cluster to a new CPU limit.

        This method performs the scaling operation if the recovery time has passed since the last
        scaling event. It checks if the new limit exceeds the minimum or maximum CPU limits and adjusts
        accordingly. If scaling is successful, it logs the event and updates the last scaling time.

        Args:
            new_limit (int): The new number of cores to scale to.
            time_now (datetime): The current time.

        Returns:
            bool: Returns True if scaling was performed, False if no scaling occurred due to the recovery time.
        """
        minutes = time_now.minute
        current_cpu_limit = self.cluster_state_provider.get_current_cpu_limit()

        # Only scale if the new limit differs from the current CPU limit
        if new_limit != current_cpu_limit:
            # Perform scaling if enough recovery time has passed since the last scaling event
            if self.last_scaling_time is None or (time_now - self.last_scaling_time).seconds > self.recovery_time * 60:
                self.logger.info(">>>attempting to scale to %f cores from %f", new_limit, current_cpu_limit)

                # Check if new_limit goes below minimum or above maximum CPU limits
                if new_limit < self.cluster_state_provider.config.general_config["min_cpu_limit"]:
                    self.logger.info(">>>not scaling, would go below min cores")
                    self.cluster_state_provider.set_cpu_limit(
                        self.cluster_state_provider.config.general_config["min_cpu_limit"]
                    )
                    self.logger.info(">>>corrected to min cores")
                elif new_limit > self.cluster_state_provider.config.general_config["max_cpu_limit"]:
                    self.cluster_state_provider.set_cpu_limit(
                        self.cluster_state_provider.config.general_config["max_cpu_limit"]
                    )
                    self.logger.info(">>>corrected to max cores")
                else:
                    self.cluster_state_provider.set_cpu_limit(new_limit)

                # Update last scaling time and log the scaling event
                self.last_scaling_time = time_now
                self.logger.info(">>>updated to %f cores", new_limit)
                self.logger.info("Having a post-scaling %d minute nap.", self.recovery_time)
                return True

            # If recovery time has not passed, log the remaining time
            elif self.last_scaling_time is not None:
                self.logger.info(
                    "Waiting to scale %d minutes, current minutes %d, new_limit: %f",
                    self.recovery_time * 60 - (time_now - self.last_scaling_time).seconds // 60,
                    minutes,
                    new_limit,
                )
        else:
            # Log if no scaling action is necessary
            self.logger.info(
                "Waiting to scale %d minutes, current minutes %d, decision of cores to add or subtract: %f",
                0,
                minutes,
                new_limit,
            )
        return False
