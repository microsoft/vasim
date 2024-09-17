#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#
import copy
import multiprocessing
import sys
import random
from typing import Dict, List
import logging
import uuid
import os
import itertools

from vasim.recommender.cluster_state_provider.ClusterStateConfig import ClusterStateConfig

random.seed(1234)

"""
This file contains functions for tuning the simulator parameters.

The key function is tune_with_strategy, which takes a base configuration and a set of parameters to tune.
It generates modified configurations based on the specified tuning strategy and runs the simulator with each one.
Finally, it returns the best configuration and its metric value.

Some helper functions are also included for generating modified configurations and running the simulator with a given configuration.

"""


def _create_modified_configs(baseconfig: ClusterStateConfig,
                             algo_specific_params_to_tune: Dict[str, List[any]],
                             general_params_to_tune: Dict[str, List[any]],
                             predictive_params_to_tune: Dict[str, List[any]],
                             strategy: str,
                             num_combinations: int) -> List[ClusterStateConfig]:
    """
    This is a helper function that generates modified configurations based on the specified tuning strategy.

    """
    def evaluate_config(algo_config_params: Dict[str, any],
                        general_config_params: Dict[str, any], predictive_params: Dict[str, any]) -> ClusterStateConfig:
        # Create a copy of the config with the updated parameter values
        modified_config = copy.deepcopy(baseconfig)
        for param, value in algo_config_params.items():
            modified_config["algo_specific_config"][param] = value
        for param, value in general_config_params.items():
            modified_config["general_config"][param] = value
        for param, value in predictive_params.items():
            modified_config["prediction_config"][param] = value
        # Return the modified config and the metric value
        return modified_config

    def generate_random_configs(algo_params_to_tune, general_params_to_tune, predictive_params_to_tune, num_combinations):
        modified_configs = []
        for _ in range(num_combinations):
            algo_config = {}
            for config_param, values in algo_params_to_tune.items():
                algo_config[config_param] = random.choice(values)
            general_config = {}
            for config_param, values in general_params_to_tune.items():
                general_config[config_param] = random.choice(values)
            predictive_params = {}
            for predictive_param, values in predictive_params_to_tune.items():
                predictive_params[predictive_param] = random.choice(values)
            modified_configs.append(evaluate_config(algo_config, general_config, predictive_params))
        return modified_configs

    if strategy == "grid":
        algo_specific_params_combinations = list(itertools.product(*algo_specific_params_to_tune.values()))
        general_config_param_combinations = list(itertools.product(*general_params_to_tune.values()))
        predictive_param_combinations = list(itertools.product(*predictive_params_to_tune.values()))
        modified_configs = [
            evaluate_config(dict(zip(algo_specific_params_to_tune.keys(), algo_config_combination)),
                            dict(zip(general_params_to_tune.keys(), general_config_combination)),
                            dict(zip(predictive_params_to_tune.keys(), predictive_combination)))

            for algo_config_combination in algo_specific_params_combinations
            for general_config_combination in general_config_param_combinations
            for predictive_combination in predictive_param_combinations
        ]
    elif strategy == "random":
        modified_configs = generate_random_configs(algo_specific_params_to_tune, general_params_to_tune,
                                                   predictive_params_to_tune, num_combinations)
    # TODO: Implement other strategies, such as MLOS.

    else:
        raise ValueError(f"Invalid strategy: {strategy}")

    return modified_configs


def create_uuid():
    """
    This function creates a unique identifier to be used as a worker ID.
    We return a slightly shorter version of the uuid for manageability.

    It will be of the format: cfg-368079f0-9164 for example.
    """

    uid = uuid.uuid4()
    uid = uid.hex
    return 'cfg-' + uid[:8] + '-' + uid[9:13]


def _tune_parameters(config, data_dir=None, lag=None, algorithm=None, initial_cpu_limit=None):
    """
    This is a helper function that runs the simulator with a given configuration and returns the resulting metrics.
    It is intended to be used with the multiprocessing.Pool.starmap method.
    It is called by the tune_with_strategy function.
    """
    # Include a unique worker ID in the directory path
    worker_id = create_uuid()
    setattr(config, "uuid", worker_id)
    target_dir = f'{data_dir}_tuning/target_{worker_id}'  # TODO: remove hardcode
    # Create the directory if it doesn't exist
    os.makedirs(f'{data_dir}_tuning', exist_ok=True)
    os.makedirs(target_dir, exist_ok=True)
    lag = lag or config["general_config"]["lag"]
    logger = logging.getLogger(f'{config.uuid}')
    logger.setLevel(logging.ERROR)
    log_file = f'{target_dir}/error_log.txt'
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.ERROR)
    # Create a formatter for the log messages
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    # Add the file handler to the logger
    logger.addHandler(file_handler)

    # Redirect stdout to the null device and log messages to the file
    original_stdout = sys.stdout
    logger.info(f'Starting tuning for configuration {config.uuid}')
    # Run the simulator
    try:
        from vasim.simulator.InMemorySimulator import InMemoryRunnerSimulator
        runner = InMemoryRunnerSimulator(data_dir=data_dir, lag=lag, algorithm=algorithm, initial_cpu_limit=initial_cpu_limit, target_simulation_dir=target_dir,
                                         config=config)
        metrics = runner.run_simulation()
        return config, metrics
    except Exception as e:  # TODO: what do we need to catch here?
        import traceback
        traceback.print_exc()
        sys.stdout = original_stdout
        print(e)
        print("Error in tuning parameters")
        print(config)
        logger.error(f'Error in tuning parameters: {e}')
        # dump the stack trace to the log file
        logger.error(traceback.format_exc())
    sys.stdout = original_stdout

    return config, None


def tune_with_strategy(config_path: str,
                       strategy: str,
                       num_combinations: int = 10,
                       num_workers: int = 1,
                       data_dir=None, lag=None, algorithm=None, initial_cpu_limit=None,
                       algo_specific_params_to_tune: Dict[str, List[any]] = [],
                       general_params_to_tune: Dict[str, List[any]] = [],
                       predictive_params_to_tune: Dict[str, List[any]] = []):
    """
    This function is the main entry point for tuning the simulator parameters.
    TODO: Refactor this function, as it's a bit burried in the code.
    TODO: lag is already in the config, don't have it separately here i think.

    Parameters:
    - config_path: The path to the base configuration file.
    - algo_specific_params_to_tune: A dictionary of algorithm-specific parameters to tune, where the keys are the parameter names and the values are
    lists of possible values for each parameter.
    - general_params_to_tune: A dictionary of parameters to tune that are not specific to the algorithm
    - predictive_params_to_tune: A dictionary of predictive parameters to tune that are specific to the predictive window
    and the values are lists of possible values for each parameter. #TODO: these may need to be combined with params_to_tune.
    - strategy: The tuning strategy to use. Currently, only "grid" and "random" are supported.
    - num_combinations: The number of parameter combinations to generate.
    - num_workers: The number of worker processes to use for parallel execution.
    - data_dir: The directory containing the simulation data.
    - lag: The lag parameter defines the number of minutes to wait before making a prediction.
    - algorithm: The algorithm to use for the simulation. Currently, only "multiplicative" and "additive" are supported.
    - initial_cpu_limit: The initial number of cores to use for the simulation. (Ex: the number of cores before you start autoscaling)

    """

    # Load the base configuration from the specified file
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
        baseconfig, algo_specific_params_to_tune, general_params_to_tune, predictive_params_to_tune, strategy, num_combinations)

    # Initialize the pool of worker processes
    with multiprocessing.Pool(processes=num_workers) as pool:
        # Map the tuning function to the modified configs
        param_combinations = [(modified_config, data_dir, modified_config.general_config["lag"] or lag, algorithm, initial_cpu_limit)
                              for modified_config in modified_configs]
        print(f"Running {len(param_combinations)} configurations...")
        results = pool.starmap(_tune_parameters, param_combinations)

    # For debugging, you can just call one directly for now, using the first modified config
    # TODO: the starmap isn't showing up in codecov. Write a unit test for the code above that looks like this
    # (only not in a loop, maybe just for ONE modified config)
    # #  results = _tune_parameters(modified_config[0], data_dir, lag, algorithm, initial_cpu_limit)

    # The results will be a list of tuples, where each tuple contains the modified config and the resulting metrics
    return results
