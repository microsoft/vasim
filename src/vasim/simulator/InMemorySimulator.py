#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#

"""
This module contains the InMemoryRunnerSimulator class, which is designed to simulate.

the execution of autoscaling algorithms in a virtualized environment. The simulator
utilizes recorded cluster state data and runs autoscaling algorithms to determine the
optimal scaling decisions (e.g., adjusting CPU limits) based on the current workload.

Main Features:
- Simulated Cluster State: Load and simulate autoscaling decisions using predefined cluster data.
- Autoscaling Algorithms: Supports multiple autoscaling algorithms (e.g., additive, multiplicative).
- Metrics Calculation: Calculates performance metrics and outputs them to files.
- Visualization: Plots CPU usage and scaling decisions for analysis.
- Simulation Progress: Provides progress tracking and the ability to yield updates during long-running simulations.

Classes:
    InMemoryRunnerSimulator: The main class that manages the simulation, loads configuration,
    and runs the specified autoscaling algorithms.

Functions:
    main: A command-line interface for running the InMemoryRunnerSimulator.

Dependencies:
    argparse, json, logging, numpy, pandas, and other modules for cluster state simulation and analysis.
"""

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

    It simulates the cluster state using recorded data and runs the selected recommender algorithm
    (e.g., additive or multiplicative) to determine CPU scaling decisions based on current workload.

    Attributes:
        data_dir (str): Directory where the input data (e.g., workload metrics) is stored.
        config (ClusterStateConfig): Configuration object for the cluster state.
        initial_cpu_limit (int): Initial CPU limit for the simulation.
        recommender_algorithm (object): The selected autoscaling algorithm.
        infra_scaler (SimulatedInfraScaler): The infrastructure scaler responsible for applying CPU limit changes.
        target_simulation_dir (str): Directory to save the simulation output and logs.
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
        """
        Initializes the `InMemoryRunnerSimulator` with necessary parameters to simulate autoscaling decisions.

        Args:
            data_dir (str): Directory where the input workload data is stored.
            config_path (str, optional): Path to the configuration file. Defaults to None.
            initial_cpu_limit (int, optional): Initial CPU limit for the simulation. Defaults to None.
            algorithm (str, optional): The name of the scaling algorithm to use (additive, multiplicative). Defaults to "multiplicative".
            config (ClusterStateConfig, optional): A pre-loaded configuration object. Defaults to None.
            target_simulation_dir (str, optional): Directory to save simulation output. Defaults to None.
            if_resample (bool, optional): Flag to determine if data resampling is applied. Defaults to True.
        """
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
        """
        Sets up the logging system for the simulator, saving logs to a specified directory.

        Args:
            data_dir (str): Directory where logs will be stored.

        Returns:
            logger (logging.Logger): Configured logger for the simulation.
        """
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
        """
        Loads the simulation configuration from the provided config file path.

        Args:
            config_path (str): Path to the configuration file.

        Returns:
            ClusterStateConfig: The configuration object loaded from the file.
        """
        return ClusterStateConfig(filename=config_path)

    @staticmethod
    def _create_cluster_state_provider(data_dir, config, target_simulation_dir=None):
        """
        Creates and returns a cluster state provider responsible for managing cluster state data and decisions.

        Args:
            data_dir (str): Directory where input data is stored.
            config (ClusterStateConfig): The loaded configuration object.
            target_simulation_dir (str, optional): Directory to store output files. Defaults to None.

        Returns:
            SimulatedClusterStateProvider: A provider object responsible for managing cluster data.
        """
        out_filename = f"{target_simulation_dir or data_dir}/decisions.csv"  # TODO: remove hardcode.
        return SimulatedClusterStateProviderFactory(
            data_dir=data_dir,
            out_filename=out_filename,
            config=config,
        ).create_provider(predictive=config.prediction_config)

    def _get_experiment_time_range(self):
        """
        Retrieves the start and end times for the simulation based on the cluster state provider's data.

        Returns:
            Tuple[pd.Timestamp, pd.Timestamp]: Start and end times for the simulation.
        """
        return self.cluster_state_provider.start_time, self.cluster_state_provider.end_time

    def _create_infra_scaler(self):
        """
        Initializes and returns the infrastructure scaler responsible for adjusting CPU limits.

        Returns:
            SimulatedInfraScaler: The scaler object responsible for simulating CPU scaling.
        """
        return SimulatedInfraScaler(
            self.cluster_state_provider,
            self.experiment_start_time,
            self.config.general_config.get("recovery_time", 15),
        )

    def _create_recommender_algorithm(self, algorithm):
        """
        Initializes the scaling algorithm (additive or multiplicative) based on the user's selection.

        Args:
            algorithm (str): The name of the scaling algorithm ("additive" or "multiplicative").

        Returns:
            Recommender: The selected recommender algorithm for the simulation.

        Raises:
            ValueError: If an unknown algorithm is provided.
        """
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
        """
        Initializes the file where scaling decisions will be logged.

        Args:
            data_dir (str): Directory where the output decision file will be saved.

        Returns:
            file (File): The opened file object for logging scaling decisions.
        """
        out_filename = f"{data_dir}/decisions.csv"
        out_file = Path(out_filename)

        if not out_file.exists():
            f = open(out_file, "a", encoding="utf-8")
            f.write("LATEST_TIME,CURR_LIMIT,NEW_LIMIT\n")
            f.flush()
        else:
            f = open(out_file, "a", encoding="utf-8")

        return f

    def output_decision(self, latest_time, current_limit, new_limit):
        """
        Logs the current and new CPU limits after each autoscaling decision.

        Args:
            latest_time (pd.Timestamp): The most recent timestamp for the data.
            current_limit (float): The current CPU limit before the decision.
            new_limit (float): The new CPU limit after the decision.
        """
        if latest_time is not None:
            to_write = f"{latest_time},{current_limit},{new_limit}\n"
            self.out_file.write(to_write)
            self.out_file.flush()
        else:
            self.logger.info("Nothing written this time due to error or lack of data")

    def get_metrics(self, save_to_file=True):
        """
        Retrieves performance metrics from the simulation and saves them to a file if specified.

        Args:
            save_to_file (bool, optional): Flag to save the metrics to a file. Defaults to True.

        Returns:
            dict: The calculated metrics from the simulation.
        """
        metrics = calculate_and_return_metrics_to_target(self.cluster_state_provider.data_dir, self.target_simulation_dir)

        # Convert int64 to int
        for key, value in metrics.items():
            if isinstance(value, np.int64):
                metrics[key] = int(value)

        # Save metrics to file if required
        if save_to_file and metrics:
            with open(f"{self.target_simulation_dir}/calc_metrics.json", "w", encoding="utf-8") as f:
                json.dump(metrics, f)

                self.cluster_state_provider.config.to_json(f"{self.target_simulation_dir}/metadata.json")

            plot_cpu_usage_and_new_limit_plotnine(
                self.cluster_state_provider.data_dir,
                decision_file_path=f"{self.target_simulation_dir}/decisions.csv",
                if_resample=self.if_resample,
            )

        return metrics

    def run_simulation(self):
        """
        Runs the simulation to completion and returns the final performance metrics.

        Returns:
            dict: The final metrics calculated from the simulation.
        """
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
        """
        Runs the simulation, yielding progress updates during the simulation, followed by the final result.

        Yields:
            float: Progress as a percentage of the total simulation time.
        """
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
        """
        Executes a single simulation step, processing the next data window and updating the CPU limit.

        This function is called repeatedly during the simulation to process the data and adjust the CPU limits.
        """
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
    """
    Main entry point for the command-line interface for running the InMemoryRunnerSimulator.

    It accepts user inputs such as algorithm, data directory, and configuration file through command-line arguments.
    """
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
