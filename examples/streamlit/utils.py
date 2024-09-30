#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#
"""
This module provides various utility functions for running simulations,.

processing folder data, parsing inputs, and generating metrics and plots
related to CPU usage and autoscaling simulations.
Functions:
    - calculate_and_return_metrics: Calculates and returns performance metrics from CSV and decision files.
    - parse_input: Parses input values from a string or numeric value and returns a list of floats.
    - process_folder: Processes a folder and returns the config and metrics if it contains valid simulation data.
    - create_df: Creates a pandas DataFrame from simulation results for further analysis.
    - unflatten_dict: Converts a flat dictionary into a nested dictionary based on separator.
    - load_results_parallel: Loads and processes simulation results in parallel from the target folder.
    - run_simulation: Runs the autoscaling simulation and updates a Streamlit progress bar.
    - plot_cpu_usage_and_sku_target_streamlit: Plots CPU usage and SKU targets using Streamlit's line_chart.
"""
# pylint: disable=no-member # FIXME

# utils.py
import multiprocessing
import os
from pathlib import Path

import pandas as pd
import streamlit as st

from vasim.recommender.cluster_state_provider.ClusterStateConfig import (
    ClusterStateConfig,
)
from vasim.simulator.analysis.plot_utils import (
    calculate_metrics,
    process_data,
    read_data,
)
from vasim.simulator.InMemorySimulator import InMemoryRunnerSimulator
from vasim.simulator.ParameterTuning import create_uuid


def calculate_and_return_metrics(experiment_dir, perf_log_file_path=None, decision_file_path=None):
    """
    Calculates performance metrics based on a given experiment directory, using the performance log.

    and decision files.
    Args:
        experiment_dir (str): Directory where the experiment data is stored.
        perf_log_file_path (str): Optional path to the performance log CSV file.
        decision_file_path (str): Optional path to the decisions file.
    Returns:
        dict: A dictionary containing the calculated performance metrics.
    """
    if not perf_log_file_path:
        perf_log_file_path = f"{experiment_dir}/{[f for f in os.listdir(experiment_dir) if f.endswith('.csv')][0]}"

    if not decision_file_path:
        decision_file_path = f"{experiment_dir}/decisions.csv"

    decision_df, perf_df = read_data(decision_file_path, perf_log_file_path)
    merged = process_data(decision_df, perf_df)
    metrics = calculate_metrics(merged)

    return metrics


def parse_input(value):
    """
    Parses input values from a string or numeric value and returns a list of floats.

    Args:
        value (str, int, or float): The value to be parsed, which could be a string of comma-separated values
        or a single numeric value.
    Returns:
        list: A list of floats parsed from the input value.
    """
    try:
        if isinstance(value, str):
            return [float(x.strip()) for x in value.split(",")]
        elif isinstance(value, (int, float)):
            return [float(value)]
        else:
            return []
    except ValueError:
        return []


def process_folder(target_folder, folder):
    """
    Processes a folder in the target directory.

    If the folder contains valid simulation data,
    returns the folder name, configuration, and metrics.
    Args:
        target_folder (str): The directory where target folders are located.
        folder (str): The folder to process.
    Returns:

        tuple or None: A tuple containing folder name, config, and metrics, or None if the folder is invalid.
    """
    if folder.startswith("target_"):
        metadata_file = f"{target_folder}/{folder}/metadata.json"
        if os.path.exists(f"{target_folder}/{folder}/calc_metrics.json") and os.path.exists(metadata_file):
            config = ClusterStateConfig(filename=metadata_file)
            metrics = calculate_and_return_metrics(f"{target_folder}/{folder}")
            return (folder, config, metrics)
    return None


def create_df(results):
    """
    Creates a pandas DataFrame from the results of multiple simulations.

    Args:
        results (list): A list of tuples containing folder names, configurations, and metrics.
    Returns:
        pd.DataFrame: A DataFrame with the simulation results.
    """
    rows = []
    for folder, config, metrics in results:

        row = pd.Series(
            {
                "folder": folder,
                "sum_slack": metrics["sum_slack"],
                "sum_insufficient_cpu": metrics["sum_insufficient_cpu"],
                "num_scalings": metrics["num_scalings"],
                "average_slack": metrics["average_slack"],
                "average_insufficient_cpu": metrics["average_insufficient_cpu"],
                "insufficient_observations_percentage": metrics["insufficient_observations_percentage"],
                "slack_percentage": metrics["slack_percentage"],
                "num_insufficient_cpu": metrics["num_insufficient_cpu"],
                "window": config.window,
                "scale_down_buffer": config.scale_down_buffer,
                "uuid": config.uuid,
                "low_threshold": config.low_threshold,
                "high_threshold": config.high_threshold,
                "ecdf_threshold": config.ecdf_threshold,
                "lower_slack_threshold": config.lower_slack_threshold,
                "slack": config.slack,
                "max_autoscale_up": config.max_autoscale_up,
                "max_autoscale_down": config.max_autoscale_down,
                "lag": config.lag,
                "max_slack": metrics["max_slack"],
            }
        )
        rows.append(row)  # Add the row to the list

    df = pd.concat(rows, axis=1).T
    return df


def unflatten_dict(d, sep="."):
    """
    Converts a flat dictionary into a nested dictionary, using a separator to determine levels of nesting.

    Args:
        d (dict): The flat dictionary to be unflattened.
        sep (str): The separator used to determine nesting.
    Returns:
        dict: A nested dictionary.
    """
    result_dict = {}
    for key, value in d.items():
        parts = key.split(sep)
        d = result_dict
        for part in parts[:-1]:
            d = d.setdefault(part, {})
        d[parts[-1]] = value
    return result_dict


def load_results_parallel(target_folder):
    """
    Loads and processes simulation results in parallel from the specified target folder.

    Args:
        target_folder (str): The folder containing target simulation data.
    Returns:
        list: A list of processed results from the simulations.
    """
    with multiprocessing.Pool() as pool:
        results = pool.starmap(process_folder, ((target_folder, folder) for folder in os.listdir(target_folder)))
    return results


def run_simulation(algorithm, data_dir, initial_cores_count, config):
    """
    Runs the autoscaling simulation using the specified algorithm and configuration.

    Args:
        algorithm (str): The name of the autoscaling algorithm to use (e.g., "additive" or "multiplicative").
        data_dir (str): Directory containing the workload data.
        initial_cores_count (int): Initial CPU limit for the simulation.
        config (ClusterStateConfig): Configuration object for the simulation.
    """
    uid = create_uuid()
    # Create target directory
    target_dir_name = Path(data_dir).parent / "simulation_results" / str(uid)
    target_dir_name.mkdir(parents=True, exist_ok=True)

    runner = InMemoryRunnerSimulator(
        data_dir=data_dir,
        algorithm=algorithm,
        initial_cpu_limit=initial_cores_count,
        config=config,
        target_simulation_dir=str(target_dir_name),
    )

    # Call the generator function
    progress_generator = runner.run_simulation_with_progress()

    # Create the progress bar
    progress_bar = st.progress(0)

    # Update the progress bar and handle exceptions
    try:
        for status in progress_generator:
            if isinstance(status, float):
                # Ensure progress is between 0 and 1
                progress_bar.progress(min(status, 1.0))
            else:
                # Handle final metrics
                progress_bar.progress(1.0)  # Mark progress as complete
                break
    except Exception as e:  # pylint: disable=broad-exception-caught  # FIXME
        st.error(f"An error occurred during the simulation: {str(e)}")
        raise
    finally:
        st.write("Wait a second. Plot is generated!")

        progress_bar.empty()  # Clear the progress bar after completion

        perf_log_file_path = f"{data_dir}/{[f for f in os.listdir(data_dir) if f.endswith('.csv')][0]}"
        # Replace this with your plotnine code
        plot_cpu_usage_and_sku_target_streamlit(target_dir_name, perf_log_file_path=perf_log_file_path)


def plot_cpu_usage_and_sku_target_streamlit(experiment_dir, perf_log_file_path=None, decision_file_path=None):
    """
    Plots CPU usage and SKU target data using Streamlit's line_chart.

    Args:
        experiment_dir (str): Directory where the experiment data is stored.
        perf_log_file_path (str): Optional path to the performance log CSV file.
        decision_file_path (str): Optional path to the decisions file.

    Returns:
        None
    """
    if not perf_log_file_path:
        perf_log_file_path = f"{experiment_dir}/{[f for f in os.listdir(experiment_dir) if f.endswith('.csv')][0]}"

    if not decision_file_path:
        decision_file_path = f"{experiment_dir}/decisions.csv"

    decision_df, perf_df = read_data(decision_file_path, perf_log_file_path)
    merged = process_data(decision_df, perf_df)

    # Convert TIMESTAMP to datetime, CURR_LIMIT and CPU_USAGE_ACTUAL to float
    merged["TIMESTAMP"] = pd.to_datetime(merged["TIMESTAMP"])
    merged["CURR_LIMIT"] = merged["CURR_LIMIT"].astype(float)
    merged["CPU_USAGE_ACTUAL"] = merged["CPU_USAGE_ACTUAL"].astype(float)

    # Plot the DataFrame using Streamlit line_chart
    st.line_chart(merged.set_index("TIMESTAMP")[["CURR_LIMIT", "CPU_USAGE_ACTUAL"]], color=["#0000FF", "#FF0000"])
