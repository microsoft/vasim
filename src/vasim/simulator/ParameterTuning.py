#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#
import copy
import itertools
import logging
import multiprocessing
import os
import random
import sys
import uuid
from typing import Dict, List

from vasim.recommender.cluster_state_provider.ClusterStateConfig import (
    ClusterStateConfig,
)

random.seed(1234)

"""
This module contains functions to tune the simulator parameters.

The primary function is `tune_with_strategy`, which uses a base configuration and tuning parameters.
It generates modified configurations based on a specified tuning strategy and runs the simulator for each configuration.

The tuning strategies include:

- **Grid Search**: This strategy evaluates every possible combination of the provided parameter values.
  It generates a Cartesian product of all parameter ranges, ensuring that all combinations are tested.
  While this method guarantees that the entire parameter space is explored, it can be computationally expensive,
  especially when the number of parameters or the range of values is large.

- **Random Search**: Instead of exhaustively testing all combinations, random search selects a specified number
  of random combinations from the parameter values. This approach reduces the computational cost compared to
  grid search but may miss the optimal configuration if the search space is large and too few samples are taken.

Helper functions are also provided to modify configurations, create unique worker IDs, and run the simulator.
"""


def _create_modified_configs(
    baseconfig: ClusterStateConfig,
    algo_specific_params_to_tune: Dict[str, List[any]],
    general_params_to_tune: Dict[str, List[any]],
    predictive_params_to_tune: Dict[str, List[any]],
    strategy: str,
    num_combinations: int,
) -> List[ClusterStateConfig]:
    """
    Generates modified configurations based on the specified tuning strategy, initial configuration,.

    and a set of allowed parameters and values to tune.

    Args:
        baseconfig (ClusterStateConfig): The base configuration to modify.
        algo_specific_params_to_tune (Dict[str, List[any]]): Algorithm-specific parameters and their possible values to tune.
        general_params_to_tune (Dict[str, List[any]]): General configuration parameters and their possible values to tune.
        predictive_params_to_tune (Dict[str, List[any]]): Predictive configuration parameters and their possible values to tune.
        strategy (str): The tuning strategy to use ('grid' or 'random').
        num_combinations (int): The number of random combinations to generate for the 'random' strategy.
            This parameter is ignored for the 'grid' strategy.

    Returns:
        List[ClusterStateConfig]: A list of modified configurations based on the specified tuning strategy and parameters for tuning.
    """

    def evaluate_config(
        algo_config_params: Dict[str, any], general_config_params: Dict[str, any], predictive_params: Dict[str, any]
    ) -> ClusterStateConfig:
        """
        Creates a modified configuration with updated parameter values.

        Args:
            algo_config_params (Dict[str, any]): The algorithm-specific parameters.
            general_config_params (Dict[str, any]): The general configuration parameters.
            predictive_params (Dict[str, any]): The predictive configuration parameters.

        Returns:
            ClusterStateConfig: A modified configuration.
        """
        modified_config = copy.deepcopy(baseconfig)
        for param, value in algo_config_params.items():
            modified_config["algo_specific_config"][param] = value
        for param, value in general_config_params.items():
            modified_config["general_config"][param] = value
        for param, value in predictive_params.items():
            modified_config["prediction_config"][param] = value
        return modified_config

    def generate_random_configs(algo_params_to_tune, general_params_to_tune, predictive_params_to_tune, num_combinations):
        """
        Generates random configurations based on provided parameters.

        Args:
            algo_params_to_tune (Dict[str, List[any]]): Algorithm-specific parameters to tune.
            general_params_to_tune (Dict[str, List[any]]): General configuration parameters to tune.
            predictive_params_to_tune (Dict[str, List[any]]): Predictive configuration parameters to tune.
            num_combinations (int): Number of random combinations to generate.

        Returns:
            List[ClusterStateConfig]: A list of randomly generated configurations.
        """
        modified_configs = []
        for _ in range(num_combinations):
            algo_config = {config_param: random.choice(values) for config_param, values in algo_params_to_tune.items()}
            general_config = {config_param: random.choice(values) for config_param, values in general_params_to_tune.items()}
            predictive_params = {
                predictive_param: random.choice(values) for predictive_param, values in predictive_params_to_tune.items()
            }
            modified_configs.append(evaluate_config(algo_config, general_config, predictive_params))
        return modified_configs

    if strategy == "grid":
        algo_specific_params_combinations = list(itertools.product(*algo_specific_params_to_tune.values()))
        general_config_param_combinations = list(itertools.product(*general_params_to_tune.values()))
        predictive_param_combinations = list(itertools.product(*predictive_params_to_tune.values()))
        modified_configs = [
            evaluate_config(
                dict(zip(algo_specific_params_to_tune.keys(), algo_config_combination)),
                dict(zip(general_params_to_tune.keys(), general_config_combination)),
                dict(zip(predictive_params_to_tune.keys(), predictive_combination)),
            )
            for algo_config_combination in algo_specific_params_combinations
            for general_config_combination in general_config_param_combinations
            for predictive_combination in predictive_param_combinations
        ]
    elif strategy == "random":
        modified_configs = generate_random_configs(
            algo_specific_params_to_tune,
            general_params_to_tune,
            predictive_params_to_tune,
            num_combinations,
        )
    # TODO: Implement other strategies, such as MLOS.
    else:
        raise ValueError(f"Invalid strategy: {strategy}")

    return modified_configs


def create_uuid():
    """
    Generates a unique identifier to be used as a worker ID.

    Returns:
        str: A unique identifier string in the format 'cfg-xxxxxxxx-xxxx'.
    """
    uid = uuid.uuid4()
    uid = uid.hex
    return "cfg-" + uid[:8] + "-" + uid[9:13]


def _tune_parameters(config, data_dir=None, algorithm=None, initial_cpu_limit=None):
    """
    Runs the simulator with the provided configuration and returns the resulting metrics.

    Args:
        config (ClusterStateConfig): The configuration to use for the simulation.
        data_dir (str): The directory containing simulation data.
        algorithm (str): The algorithm to use for the simulation.
        initial_cpu_limit (int): Initial CPU core limit before scaling.

    Returns:
        Tuple[ClusterStateConfig, Any]: The configuration and the resulting metrics.
    """
    worker_id = create_uuid()
    setattr(config, "uuid", worker_id)
    target_dir = f"{data_dir}_tuning/target_{worker_id}"
    os.makedirs(f"{data_dir}_tuning", exist_ok=True)
    os.makedirs(target_dir, exist_ok=True)
    logger = logging.getLogger(f"{config.uuid}")
    logger.setLevel(logging.ERROR)
    log_file = f"{target_dir}/error_log.txt"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.ERROR)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    original_stdout = sys.stdout
    logger.info(f"Starting tuning for configuration {config.uuid}")
    try:
        from vasim.simulator.InMemorySimulator import InMemoryRunnerSimulator

        runner = InMemoryRunnerSimulator(
            data_dir=data_dir,
            algorithm=algorithm,
            initial_cpu_limit=initial_cpu_limit,
            target_simulation_dir=target_dir,
            config=config,
        )
        metrics = runner.run_simulation()
        return config, metrics
    except Exception as e:
        import traceback

        traceback.print_exc()
        sys.stdout = original_stdout
        print(e)
        logger.error(f"Error in tuning parameters: {e}")
        logger.error(traceback.format_exc())
    sys.stdout = original_stdout
    return config, None


def tune_with_strategy(
    config_path: str,
    strategy: str,
    num_combinations: int = 10,
    num_workers: int = 1,
    data_dir=None,
    algorithm=None,
    initial_cpu_limit=None,
    algo_specific_params_to_tune: Dict[str, List[any]] = [],
    general_params_to_tune: Dict[str, List[any]] = [],
    predictive_params_to_tune: Dict[str, List[any]] = [],
):
    """
    Tunes the simulator parameters based on a strategy and configuration file.

    This function is the main entry point for tuning the simulator parameters.

    Args:
        config_path (str): The path to the base configuration file.
        strategy (str): The tuning strategy ('grid' or 'random').
        num_combinations (int): Number of parameter combinations to generate for random strategy. Ignored for grid strategy
        num_workers (int): Number of worker processes to use for parallel execution.
        data_dir (str): The directory containing simulation data.
        algorithm (str): The algorithm for the simulation.
        initial_cpu_limit (int): The initial number of CPU cores before scaling.
        algo_specific_params_to_tune (Dict[str, List[any]]): Algorithm-specific parameters to tune.
        general_params_to_tune (Dict[str, List[any]]): General parameters to tune.
        predictive_params_to_tune (Dict[str, List[any]]): Predictive parameters to tune.

    Returns:
        List[Tuple[ClusterStateConfig, Any]]: A list of tuples with the configuration and resulting metrics.
    """
    baseconfig = ClusterStateConfig(filename=config_path)

    # if any of the 3 lists are none, replace them with empty lists
    algo_specific_params_to_tune = algo_specific_params_to_tune or {}
    general_params_to_tune = general_params_to_tune or {}
    predictive_params_to_tune = predictive_params_to_tune or {}

    # Next, assert that the keys in the dictionaries are valid. We'll compare them to the keys in the baseconfig
    # to make sure they are valid parameters to tune.
    # TODO: add unit tests for this
    for key in algo_specific_params_to_tune.keys():
        assert key in baseconfig["algo_specific_config"], f"Invalid algorithm specific parameter: {key}"
    for key in general_params_to_tune.keys():
        assert key in baseconfig["general_config"], f"Invalid general parameter: {key}"
    for key in predictive_params_to_tune.keys():
        assert key in baseconfig["prediction_config"], f"Invalid predictive parameter: {key}"

    # Generate the modified configs based on the specified strategy
    modified_configs = _create_modified_configs(
        baseconfig,
        algo_specific_params_to_tune,
        general_params_to_tune,
        predictive_params_to_tune,
        strategy,
        num_combinations,
    )

    # Initialize the pool of worker processes
    with multiprocessing.Pool(processes=num_workers) as pool:
        # Map the tuning function to the modified configs
        param_combinations = [
            (modified_config, data_dir, algorithm, initial_cpu_limit) for modified_config in modified_configs
        ]
        print(f"Running {len(param_combinations)} configurations...")
        results = pool.starmap(_tune_parameters, param_combinations)

    # For debugging, you can just call one directly for now, using the first modified config
    # TODO: the starmap isn't showing up in codecov. Write a unit test for the code above that looks like this
    # (only not in a loop, maybe just for ONE modified config)
    # #  results = _tune_parameters(modified_config[0], data_dir, lag, algorithm, initial_cpu_limit)

    # The results will be a list of tuples, where each tuple contains the modified config and the resulting metrics
    return results
