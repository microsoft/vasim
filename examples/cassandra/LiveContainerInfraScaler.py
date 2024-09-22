#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#

from vasim.simulator.SimulatedInfraScaler import SimulatedInfraScaler
import logging
from pathlib import Path


class LiveContainerInfraScaler(SimulatedInfraScaler):
    """
    In this system, we will both increment the cluster state provider, and also the live system.

    In this case, we will be doing in-place CPU updates to the container. This is a simple example of how to
    integrate the simulator with a live system. In this case, we will be using the docker-py library to update the
    CPU limit of a container.
    """

    def __init__(self, cluster_state_provider, start_timestamp, recovery_time, container, initial_cpu_limit=None):
        super().__init__(cluster_state_provider, start_timestamp, recovery_time)

        self.container = container

        # Write a test message
        self.logger.info(">>>LiveContainerInfraScaler initialized")
        self.logger.info(">>>Container: %s", self.container)
        self.logger.info(">>>Initial CPU limit: %s", initial_cpu_limit)

    def set_cpu_limit_live(self, new_cpu_limit):
        """
        Set the CPU limit of the container
        :param new_cpu_limit: The new CPU limit
        """
        # update the live container
        self.container.update(cpu_quota=(new_cpu_limit * 100000))

        self.logger.info(f"Updated CPU limit to {new_cpu_limit}")

    def scale(self, new_limit, time_now):
        """
        :param decision: The number of cores to add or subtract
        :param time_now: The current time

        """
        minutes = time_now.minute
        current_cpu_limit = self.cluster_state_provider.get_current_cpu_limit()
        if new_limit != current_cpu_limit:
            # We only want to scale if the recovery time has passed since the last scaling event
            # or if there was no previous scaling event
            if self.last_scaling_time is None or (time_now - self.last_scaling_time).seconds > self.recovery_time * 60:
                self.logger.info(">>>attempting to scale to %d cores from %d",
                                 new_limit, current_cpu_limit)
                if new_limit < self.cluster_state_provider.config.general_config["min_cpu_limit"]:
                    self.logger.info(">>>not scaling, would go below min cores")
                    self.set_cpu_limit_live(self.cluster_state_provider.config.general_config["min_cpu_limit"])
                    self.logger.info(">>>corrected to min cores")
                elif new_limit > self.cluster_state_provider.config.general_config["max_cpu_limit"]:
                    self.set_cpu_limit_live(self.cluster_state_provider.config.general_config["max_cpu_limit"])
                    self.logger.info(">>>corrected to max cores")
                else:
                    self.set_cpu_limit_live(new_limit)
                self.last_scaling_time = time_now
                self.logger.info(">>>updated to %d cores", new_limit)
                self.logger.info("Having a post-scaling %d minute nap.", self.recovery_time)
                return True
            elif self.last_scaling_time is not None:
                self.logger.info("Waiting to scale %d minutes, current minutes %d, new_limit: %d",
                                 self.recovery_time * 60 - (time_now - self.last_scaling_time).seconds // 60, minutes,
                                 new_limit)
        else:
            self.logger.info("Waiting to scale %d minutes, current minutes %d, decision of cores to add or subtract: %d",
                             0, minutes, new_limit)
        return False
