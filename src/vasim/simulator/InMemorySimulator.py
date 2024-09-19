#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#
import argparse
import json
import logging
import os
from pathlib import Path

import numpy as np
import pandas as pd

from vasim.recommender.cluster_state_provider.ClusterStateConfig import (
    ClusterStateConfig,
)
from vasim.recommender.DummyAdditiveRecommender import SimpleAdditiveRecommender
from vasim.recommender.DummyMultiplierRecommender import SimpleMultiplierRecommender
from vasim.simulator.analysis.plot_utils import (
    calculate_and_return_metrics_to_target,
    plot_cpu_usage_and_new_limit_plotnine,
)
from vasim.simulator.ParameterTuning import create_uuid
from vasim.simulator.SimulatedClusterStateProviderFactory import (
    SimulatedClusterStateProviderFactory,
)
from vasim.simulator.SimulatedInfraScaler import SimulatedInfraScaler


class InMemoryRunnerSimulator:
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
    ):
        # pylint: disable=too-many-arguments
        worker_id = create_uuid()
        target_simulation_dir = target_simulation_dir or os.path.join(
            f"{data_dir}_simulations",
            f"target_{worker_id}",
        )  # TODO: remove hardcode
        # Create the directory if it doesn't exist
        os.makedirs(target_simulation_dir, exist_ok=True)

        self.logger = self._setup_logger(target_simulation_dir or data_dir)
        if config is not None:
            self.config = config
        else:
            config_path = config_path or f"{data_dir}/metadata.json"
            self.config = self._load_config(config_path)

        self.initial_cpu_limit = initial_cpu_limit or self.config.general_config["max_cpu_limit"]
        self.cluster_state_provider = self._create_cluster_state_provider(data_dir, self.config, target_simulation_dir)
        self.experiment_start_time, self.experiment_end_time = self._get_experiment_time_range()
        self.infra_scaler = self._create_infra_scaler()
        self.target_simulation_dir = target_simulation_dir or data_dir
        self.if_resample = if_resample
        self.recommender_algorithm = self._create_recommender_algorithm(algorithm)

        self.out_file = self._initialize_output_file(target_simulation_dir or data_dir)

        self.sleep_interval_minutes = self.config.general_config["lag"]

    @staticmethod
    def _setup_logger(data_dir):
        logger = logging.getLogger()
        logger.setLevel(logging.ERROR)

        log_file = os.path.join(f"{data_dir}/InMemorySim.log")  # TODO: remove hardcode
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.WARNING)

        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        return logger

    @staticmethod
    def _load_config(config_path):
        return ClusterStateConfig(filename=config_path)

    @staticmethod
    def _create_cluster_state_provider(data_dir, config, target_simulation_dir=None):
        out_filename = f"{target_simulation_dir or data_dir}/decisions.txt"  # TODO: remove hardcode. ALSO: todo, this is csv
        return SimulatedClusterStateProviderFactory(
            data_dir=data_dir,
            out_filename=out_filename,
            config=config,
        ).create_provider(predictive=config.prediction_config)

    def _get_experiment_time_range(self):
        return self.cluster_state_provider.start_time, self.cluster_state_provider.end_time

    def _create_infra_scaler(self):
        return SimulatedInfraScaler(
            self.cluster_state_provider,
            self.experiment_start_time,
            self.config.general_config.get("recovery_time", 15),
        )

    def _create_recommender_algorithm(self, algorithm):
        if algorithm == "multiplicative":
            return SimpleMultiplierRecommender(self.cluster_state_provider)
        elif algorithm == "additive":
            return SimpleAdditiveRecommender(self.cluster_state_provider)
        # Add your own algorithm here!!!
        # TODO: Make this more dynamic
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")

    @staticmethod
    def _initialize_output_file(data_dir):
        out_filename = f"{data_dir}/decisions.txt"
        out_file = Path(out_filename)

        if not out_file.exists():
            f = open(out_file, "a", encoding="utf-8")
            f.write("LATEST_TIME,CURR_LIMIT,NEW_LIMIT\n")
            f.flush()
        else:
            f = open(out_file, "a", encoding="utf-8")

        return f

    def output_decision(self, latest_time, current_limit, new_limit):
        if latest_time is not None:
            to_write = f"{latest_time},{current_limit},{new_limit}\n"
            self.out_file.write(to_write)
            self.out_file.flush()
        else:
            self.logger.info("Nothing written this time due to error or lack of data")

    def get_metrics(self, save_to_file=True):
        metrics = calculate_and_return_metrics_to_target(self.cluster_state_provider.data_dir, self.target_simulation_dir)

        # Convert int64 to int
        for key, value in metrics.items():
            if isinstance(value, np.int64):
                metrics[key] = int(value)

        #        save metrics to file
        if save_to_file and metrics:
            with open(f"{self.target_simulation_dir}/calc_metrics.json", "w", encoding="utf-8") as f:
                json.dump(metrics, f)
            self.cluster_state_provider.config.to_json(f"{self.target_simulation_dir}/metadata.json")
            plot_cpu_usage_and_new_limit_plotnine(
                self.cluster_state_provider.data_dir,
                decision_file_path=f"{self.target_simulation_dir}/decisions.txt",
                if_resample=self.if_resample,
            )
        return metrics

    def run_simulation(self):
        """Run the simulation to completion and return the final metrics."""

        print(f"Starting simulation at {self.experiment_start_time} and continuing till {self.experiment_end_time}")
        print(f"Setting number of cores to {self.initial_cpu_limit}")
        self.cluster_state_provider.set_cpu_limit(self.initial_cpu_limit)

        while (
            self.cluster_state_provider.current_time + pd.Timedelta(minutes=self.sleep_interval_minutes)
            < self.cluster_state_provider.end_time
        ):

            # Core simulation logic (without yielding progress)
            self._execute_simulation_step()

        print(f"Simulation finished at {self.cluster_state_provider.current_time}")
        self.cluster_state_provider.flush_metrics_data(f"{self.target_simulation_dir}/perf_event_log.csv")

        # Return the final metrics
        return self.get_metrics()

    def run_simulation_with_progress(self):
        """Run the simulation, yielding progress updates as the simulation progresses, followed by the final result."""
        print(f"Starting simulation at {self.experiment_start_time} and continuing till {self.experiment_end_time}")
        print(f"Setting number of cores to {self.initial_cpu_limit}")
        self.cluster_state_provider.set_cpu_limit(self.initial_cpu_limit)

        total_time = self.cluster_state_provider.end_time - self.cluster_state_provider.current_time
        time_elapsed = pd.Timedelta(minutes=0)

        while (
            self.cluster_state_provider.current_time + pd.Timedelta(minutes=self.sleep_interval_minutes)
            < self.cluster_state_provider.end_time
        ):

            # Core simulation logic (with progress tracking)
            self._execute_simulation_step()

            # Yield the progress
            time_elapsed += pd.Timedelta(minutes=self.sleep_interval_minutes)
            progress = time_elapsed / total_time
            yield progress

        print(f"Simulation finished at {self.cluster_state_provider.current_time}")
        self.cluster_state_provider.flush_metrics_data(f"{self.target_simulation_dir}/perf_event_log.csv")

    def _execute_simulation_step(self):
        """This function holds the core simulation logic shared by both run_simulation and run_simulation_with_progress."""
        # Get the next window of data to simulate
        recorded_data, latest_time = self.cluster_state_provider.get_next_recorded_data()

        if recorded_data is None:
            self.logger.info("Waiting for window to fill with data before running simulation.")
            self.cluster_state_provider.advance_time()
            return

        # Run user-provided algorithm with the recorded data
        new_limit = self.recommender_algorithm.run(recorded_data)

        # Log current and new CPU limit decisions
        self.output_decision(latest_time, self.cluster_state_provider.get_current_cpu_limit(), new_limit)

        # Advance time by the lag parameter
        self.cluster_state_provider.advance_time()

        if new_limit is None:
            self.logger.info("No decision made")
            return

        self.infra_scaler.scale(new_limit, self.cluster_state_provider.current_time)


def main():
    """TODO: Do we want to remove main here? It might confuse users, but might be useful for testing."""
    parser = argparse.ArgumentParser(description="InMemoryRunnerSimulator Command Line Interface")
    parser.add_argument(
        "--algorithm",
        choices=["oracle", "multiplicative", "additive"],
        default="multiplicative",
        help='Name of the algorithm (e.g., "oracle", "multiplicative")',
    )
    parser.add_argument("--data_dir", help="Path to the data directory")
    parser.add_argument("--config_path", help="Path to the config file")
    parser.add_argument("--lag", type=int, default=10, help="Lag value (default: 10)")

    args = parser.parse_args()

    runner = InMemoryRunnerSimulator(data_dir=args.data_dir, algorithm=args.algorithm, config_path=args.config_path)
    runner.run_simulation()


if __name__ == "__main__":
    main()
