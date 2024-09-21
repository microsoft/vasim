#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#
import time
import pandas as pd
from LiveContainerInfraScaler import LiveContainerInfraScaler

from vasim.simulator.InMemorySimulator import InMemoryRunnerSimulator
from vasim.recommender.cluster_state_provider.FileClusterStateProvider import FileClusterStateProvider


class InMemoryRunner(InMemoryRunnerSimulator):
    """
    This class is a simulator that runs the recommender algorithm on a simulated cluster state.

    It contains the run method that simulates the cluster state and runs the recommender algorithm.
    """

    # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        data_dir,
        config_path=None,
        initial_cpu_limit=None,
        algorithm="multiplicative",
        config=None,
        target_simulation_dir=None,
        if_resample=True,
        container=None
    ):

        self.container = container  # This must come first. It is used in the parent class's __init__ method
        super().__init__(data_dir, config_path=config_path, initial_cpu_limit=initial_cpu_limit, algorithm=algorithm,
                         config=config, target_simulation_dir=target_simulation_dir, if_resample=if_resample)

        # Here we'll use the FileClusterStateProvider to read the data from the live performance log
        self.cluster_state_provider = FileClusterStateProvider(data_dir=data_dir, config=self.config, features=['cpu'],
                                                               window=self.config.general_config['window'], lag=self.config.general_config['lag'],
                                                               min_cpu_limit=self.config.general_config['min_cpu_limit'],
                                                               max_cpu_limit=self.config.general_config['max_cpu_limit'], save_metadata=False)

    def _get_experiment_time_range(self):
        return self.cluster_state_provider.start_time, self.cluster_state_provider.end_time

    def _create_infra_scaler(self):
        return LiveContainerInfraScaler(
            self.cluster_state_provider,
            self.experiment_start_time,
            self.config.general_config['recovery_time'],
            self.container
        )

    def run_live(self):
        """Run the simulation to completion and return the final metrics."""

        print(f"Starting simulation at {self.experiment_start_time} and continuing till {self.experiment_end_time}")
        # print(f"Setting number of cores to {self.initial_cpu_limit}")
        # self.cluster_state_provider.set_cpu_limit(self.initial_cpu_limit)

        try:
            while True:
                # Core simulation logic (without yielding progress)
                self._execute_simulation_step()
                lag = self.cluster_state_provider.config.general_config["lag"]
                print(f"Now sleeping for {lag} minutes")
                # sleep(lag * 60)

                # We will loop until user hits Ctrl-C
        except KeyboardInterrupt:
            pass

        print(f"Simulation finished at {self.cluster_state_provider.current_time}")
        self.cluster_state_provider.flush_metrics_data(f"{self.target_simulation_dir}/perf_event_log.csv")

        # Return the final metrics
        return self.get_metrics()

    def _execute_simulation_step(self):
        """This function holds the core simulation logic shared by both run_simulation and run_simulation_with_progress."""
        # Get the next window of data to simulate
        recorded_data, latest_time = self.cluster_state_provider.get_next_recorded_data()

        if recorded_data is None:
            self.logger.info("Waiting for window to fill with data before running algorithm.")
            return

        # Run user-provided algorithm with the recorded data
        new_limit = self.recommender_algorithm.run(recorded_data)

        # Log current and new CPU limit decisions
        self.output_decision(latest_time, self.cluster_state_provider.get_current_cpu_limit(), new_limit)

        if new_limit is None:
            self.logger.info("No decision made")
            return

        # Get the current timestamp live but in the same format as the recorded data
        # time = self.cluster_state_provider.current_time
        # time_now = time.strftime('%Y-%m-%d %H:%M:%S', time.time())
        # use pd.Timestamp(
        time_now = pd.Timestamp(time.time())
        self.infra_scaler.scale(new_limit, time_now)

    def get_metrics(self):
        """Return the final metrics after simulation."""
        return self.cluster_state_provider.get_metrics()
