#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#
import logging
from pathlib import Path


class SimulatedInfraScaler:
    """
    In any real system, performing the actual scaling introduces a big delay.

    This is because the system needs to
    provision the new resources, and then the new resources need to be warmed up. This is often a slow process, and
    failing to replicate it makes the simulator inaccurate. Therefore, we simulate the scaling process by introducing a
    recovery time. This recovery time is the time it takes for the system to recover after a scaling event. During
    this time, the system is not allowed to scale again. This is a very important aspect of the simulation, as it
    ensures that the system does not scale too frequently, which can be very expensive in a real system.
    """

    def __init__(self, cluster_state_provider, start_timestamp, recovery_time):
        self.cluster_state_provider = cluster_state_provider
        self.last_scaling_time = None
        self.start_time = start_timestamp
        self.recovery_time = recovery_time

        # Set up logging in the target path, so it will be stored with the simulation data
        log_file = Path(self.cluster_state_provider.decision_file_path).parent.joinpath("updatelog.txt")
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(logging.FileHandler(log_file))

        # Write a test message
        self.logger.info(">>>SimulatedInfraScaler initialized")

    def scale(self, new_limit, time_now):
        """
        This function scales the simulated cluster by the decision (amount_to_scale_by) amount.

        It will only scale if the recovery time has passed
        since the last scaling event. It will also not scale if the decision is 0, only log.

        This includes some safety checks to ensure that the system does not scale below the minimum number of
        cores or above the maximum number of cores.

        It will take self.recovery_time minutes to recover after a scaling event.

        TODO: Write unit tests for this.

        :param decision: The number of cores to add or subtract
        :param time_now: The current time
        """
        minutes = time_now.minute
        current_cpu_limit = self.cluster_state_provider.get_current_cpu_limit()
        if new_limit != current_cpu_limit:
            # We only want to scale if the recovery time has passed since the last scaling event
            # or if there was no previous scaling event
            if self.last_scaling_time is None or (time_now - self.last_scaling_time).seconds > self.recovery_time * 60:
                self.logger.info(">>>attempting to scale to %d cores from %d", new_limit, current_cpu_limit)
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
                self.last_scaling_time = time_now
                self.logger.info(">>>updated to %d cores", new_limit)
                self.logger.info("Having a post-scaling %d minute nap.", self.recovery_time)
                return True
            elif self.last_scaling_time is not None:
                self.logger.info(
                    "Waiting to scale %d minutes, current minutes %d, new_limit: %d",
                    self.recovery_time * 60 - (time_now - self.last_scaling_time).seconds // 60,
                    minutes,
                    new_limit,
                )
        else:
            self.logger.info(
                "Waiting to scale %d minutes, current minutes %d, decision of cores to add or subtract: %d",
                0,
                minutes,
                new_limit,
            )
        return False
