#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#

# utils.py
import multiprocessing
import os
import uuid
from pathlib import Path
import pandas as pd
from vasim.simulator.analysis.plot_utils import calculate_metrics, process_data, read_data
import streamlit as st

from vasim.recommender.cluster_state_provider.ClusterStateConfig import ClusterStateConfig
from vasim.simulator.InMemorySimulator import InMemoryRunnerSimulator
from vasim.simulator.ParameterTuning import create_uuid


def calculate_and_return_metrics(experiment_dir, perf_log_file_path=None, decision_file_path=None):
    if not perf_log_file_path:
        perf_log_file_path = f"{experiment_dir}/{[f for f in os.listdir(experiment_dir) if f.endswith('.csv')][0]}"

    if not decision_file_path:
        decision_file_path = f"{experiment_dir}/decisions.txt"

    decision_df, perf_df = read_data(decision_file_path, perf_log_file_path)
    merged = process_data(decision_df, perf_df)
    metrics = calculate_metrics(merged)

    return metrics


def parse_input(value):
    try:
        if isinstance(value, str):
            return [float(x.strip()) for x in value.split(',')]
        elif isinstance(value, (int, float)):
            return [float(value)]
        else:
            return []
    except ValueError:
        return []


def process_folder(target_folder, folder):
    if folder.startswith("target_"):
        metadata_file = f"{target_folder}/{folder}/metadata.json"
        if os.path.exists(f"{target_folder}/{folder}/calc_metrics.json") and os.path.exists(metadata_file):
            config = ClusterStateConfig(filename=metadata_file)
            metrics = calculate_and_return_metrics(f"{target_folder}/{folder}")
            return (folder, config, metrics)
    return None


def create_df(results):
    rows = []
    for folder, config, metrics in results:

        row = pd.Series({
            'folder': folder,
            'sum_slack': metrics["sum_slack"],
            'sum_insufficient_cpu': metrics["sum_insufficient_cpu"],
            'num_scalings': metrics["num_scalings"],
            'average_slack': metrics["average_slack"],
            'average_insufficient_cpu': metrics["average_insufficient_cpu"],
            'insufficient_observations_percentage': metrics["insufficient_observations_percentage"],
            'slack_percentage': metrics["slack_percentage"],
            'num_insufficient_cpu': metrics["num_insufficient_cpu"],
            'window': config.window,
            'scale_down_buffer': config.scale_down_buffer,
            'uuid': config.uuid,
            'low_threshold': config.low_threshold,
            'high_threshold': config.high_threshold,
            'ecdf_threshold': config.ecdf_threshold,
            'lower_slack_threshold': config.lower_slack_threshold,
            'slack': config.slack,
            'max_autoscale_up': config.max_autoscale_up,
            'max_autoscale_down': config.max_autoscale_down,
            'lag': config.lag,
            'max_slack': metrics['max_slack']

        })
        rows.append(row)  # Add the row to the list

    df = pd.concat(rows, axis=1).T
    return df


def unflatten_dict(d, sep='.'):
    result_dict = {}
    for key, value in d.items():
        parts = key.split(sep)
        d = result_dict
        for part in parts[:-1]:
            d = d.setdefault(part, {})
        d[parts[-1]] = value
    return result_dict


def load_results_parallel(target_folder):
    with multiprocessing.Pool() as pool:
        results = pool.starmap(process_folder, ((target_folder, folder)
                                                for folder in os.listdir(target_folder)))
    return results


def run_simulation(algorithm, data_dir, initial_cores_count, config):
    uid = create_uuid()
    # Create target directory
    target_dir_name = Path(data_dir).parent / "simulation_results" / str(uid)
    target_dir_name.mkdir(parents=True, exist_ok=True)

    runner = InMemoryRunnerSimulator(
        data_dir=data_dir,
        algorithm=algorithm,
        initial_cpu_limit=initial_cores_count,
        config=config,
        target_simulation_dir=str(target_dir_name)
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
    except Exception as e:
        st.error(f"An error occurred during the simulation: {str(e)}")
        raise
    finally:
        st.write("Wait a second. Plot is generated!")

        progress_bar.empty()  # Clear the progress bar after completion

        perf_log_file_path = f"{data_dir}/{[f for f in os.listdir(data_dir) if f.endswith('.csv')][0]}"
        # Replace this with your plotnine code
        plot_cpu_usage_and_sku_target_streamlit(target_dir_name, perf_log_file_path=perf_log_file_path)


def plot_cpu_usage_and_sku_target_streamlit(experiment_dir, perf_log_file_path=None, decision_file_path=None):
    if not perf_log_file_path:
        perf_log_file_path = f"{experiment_dir}/{[f for f in os.listdir(experiment_dir) if f.endswith('.csv')][0]}"

    if not decision_file_path:
        decision_file_path = f"{experiment_dir}/decisions.txt"

    decision_df, perf_df = read_data(decision_file_path, perf_log_file_path)
    merged = process_data(decision_df, perf_df)

    # Convert TIMESTAMP to datetime, CURR_LIMIT and CPU_USAGE_ACTUAL to float
    merged['TIMESTAMP'] = pd.to_datetime(merged['TIMESTAMP'])
    merged['CURR_LIMIT'] = merged['CURR_LIMIT'].astype(float)
    merged['CPU_USAGE_ACTUAL'] = merged['CPU_USAGE_ACTUAL'].astype(float)

    # Plot the DataFrame using Streamlit line_chart
    st.line_chart(merged.set_index('TIMESTAMP')[['CURR_LIMIT', 'CPU_USAGE_ACTUAL']], color=["#0000FF", "#FF0000"])
