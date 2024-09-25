#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#

"""
This module provides an interactive interface for running autoscaling simulations using.

Streamlit. It supports various operations like visualizing workloads from CSV files,
configuring simulation parameters, and running autoscaling algorithms.
Main Features:
- Workload Visualization: Display CPU usage trends from CSV files.
- Simulation Options: Run autoscaling simulations or tune simulation parameters.
- Parameter Input: Dynamically adjust simulation parameters based on user input.
Modules:
    create_charts: Displays charts of CPU usage over time.
    process_params_to_tune: Processes simulation parameters for tuning.
    get_files_with_extension: Retrieves files with a specific extension from a directory.
"""

# pylint: disable=no-member # FIXME

import itertools
import json
import os
from typing import Optional

import pandas as pd
import streamlit as st
from utils import run_simulation, unflatten_dict  # pylint: disable=import-error

from vasim.recommender.cluster_state_provider.ClusterStateConfig import (
    ClusterStateConfig,
)
from vasim.simulator.ParameterTuning import tune_with_strategy

st.set_page_config(layout="wide")
st.title("VASIM Autoscaling Simulator Toolkit Presentation")


def construct_config_metric_df(config_metrics_list) -> pd.DataFrame:
    """
    Helper function to output parameter list and metrics.

    Args:
        config_metrics_list (list): A List of metrics and configs
    """
    # Create an empty list to store row data
    rows = []

    # Iterate through the results and add rows to the list
    for modified_config, metrics in config_metrics_list:
        if metrics is None:
            print(f"Skipping {modified_config.uuid} because of an error")
            continue
        row_data = {**metrics, **modified_config}  # TODO: there is a known issue https://github.com/microsoft/vasim/issues/119
        rows.append(row_data)

    # Create the DataFrame from the list of row data
    df = pd.DataFrame(rows)

    return df


@st.cache_data()
def create_charts(data):
    """
    Creates and displays a line chart for CPU usage over time in the sidebar.

    Args:
        data (pd.DataFrame): A DataFrame containing CPU usage data with a TIMESTAMP column.
    """
    # Create a new DataFrame for Streamlit line_chart
    chart_data_df = pd.DataFrame({"TIMESTAMP": data["TIMESTAMP"], "CPU_USAGE_ACTUAL": data["CPU_USAGE_ACTUAL"]})

    # Plot the DataFrame using Streamlit line_chart
    st.sidebar.line_chart(chart_data_df.set_index("TIMESTAMP"))
    # pylint: disable=possibly-used-before-assignment # FIXME
    st.sidebar.success(f"Workload visualization finished for {selected_csv}")


def process_params_to_tune(input_selected_params_to_tune):
    """
    Processes selected parameters by prompting the user for input and returning.

    the processed values.
    Args:
        input_selected_params_to_tune (list): A list of parameter names selected by the user.
    Returns:
        dict: A dictionary with parameter names as keys and user-supplied values as values.
    """
    resulted_params_to_tune = {}

    for param_name in input_selected_params_to_tune:
        param_values = process_parameter_input(param_name)
        resulted_params_to_tune[param_name] = param_values

    return resulted_params_to_tune


def process_parameter_input(param_name):
    """
    Prompts the user for input values for a specific simulation parameter and.

    returns the values as a list.
    Args:
        param_name (str): The name of the parameter to be processed.
    Returns:
        list: A list of values input by the user for the parameter.
    """
    st.subheader(f"Edit values for parameter: {param_name}")
    user_input = st.text_input(f"Enter values for {param_name} (comma-separated):")

    # Process user input and return a list of values
    param_values = [float(x.strip()) for x in user_input.split(",")] if user_input else []
    return param_values


# Sidebar for simulation options
st.sidebar.title("Simulation Options")
simulation_option = st.sidebar.radio(
    "Select Simulation Option", ["Simulation Run", "Simulation Tuning", "Simulation Tuning History"]
)

# Sidebar for workload visualization and navigation
st.sidebar.title("Workload Visualization")


# Add Path Input for the user
st.sidebar.subheader("Input Data Directory")
parent_data_input_directory = st.sidebar.text_input("Enter the directory path for CSV files:", "tests/test_data")

# Function to get all CSV files recursively from a directory


def get_files_with_extension(directory, format_suffix=".csv"):
    """
    Recursively retrieves all files with a specific extension from a directory.

    Args:
        directory (str): The directory to search for files.
        format_suffix (str): The file extension to filter (default is ".csv").
    Returns:
        list: A list of file paths matching the specified extension.
    """
    files = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            if filename.endswith(format_suffix):
                files.append(os.path.join(root, filename))
    return files


# Get all CSV files from the directory input by the user
csv_files = get_files_with_extension(parent_data_input_directory, ".csv")

# Check if there are CSV files available
if not csv_files:
    st.sidebar.error("No CSV files found in the directory.")
else:
    # Display the list of CSV files in the sidebar
    selected_csv = st.sidebar.selectbox("Select a CSV file:", csv_files)

selected_algorithm_names = st.sidebar.selectbox("Select an algorithm:", ["additive", "multiplicative"])

# Get all JSON files recursively from the data input directory
json_config_files = get_files_with_extension(parent_data_input_directory, ".json")

# Check if there are CSV files available
config_path_run: Optional[str] = None
if not json_config_files:
    st.sidebar.error("No json files found in the directory.")
else:
    # Display the list of CSV files in the sidebar
    config_path_run = st.sidebar.selectbox("Select a json file:", json_config_files)

# Check if file exists
if not config_path_run or not os.path.exists(config_path_run):
    st.error(f"Error loading JSON file: {config_path_run} does not exist")
    st.stop()

with open(config_path_run, mode="r", encoding="utf-8") as json_file_run:
    data_run = json.load(json_file_run)
    df_run = pd.json_normalize(data_run)

data_dir = os.path.dirname(selected_csv)
# Check if there's a selected CSV file
if selected_csv:
    if st.sidebar.button("Visualize workload"):
        workload_df = pd.read_csv(selected_csv)
        workload_df["TIMESTAMP"] = pd.to_datetime(workload_df["TIMESTAMP"], format="%Y.%m.%d-%H:%M:%S:%f")
        workload_df["TIMESTAMP"] = pd.DatetimeIndex(workload_df["TIMESTAMP"]).floor("min")
        workload_df = workload_df.drop_duplicates(subset=["TIMESTAMP"], keep="last")
        perf_log_resampled = workload_df.set_index("TIMESTAMP").resample("1T").ffill().reset_index()

        # Display the chart in the left sidebar
        chart_data = pd.DataFrame({"TIMESTAMP": workload_df["TIMESTAMP"], "CPU_USAGE_ACTUAL": workload_df["CPU_USAGE_ACTUAL"]})
        create_charts(chart_data)
# Page 1: Simulation Run
if simulation_option == "Simulation Run":
    st.title("Simulation Run")

    initial_cores_count_run = st.slider("Select the initial core count:", 1, 20, 7)

    # Display the DataFrame with an editable data editor
    edited_data_run = st.data_editor(df_run)

    # Convert the edited data back to JSON
    edited_json_run = edited_data_run.to_dict(orient="records")[0]
    edited_json_run = unflatten_dict(edited_json_run)
    # Display the edited JSON data
    st.json(edited_json_run)

    # Create a button to run the algorithm for simulation run
    if st.button("Run Simulation"):
        config_run = ClusterStateConfig(config_dict=edited_json_run)
        run_simulation(selected_algorithm_names, data_dir, initial_cores_count_run, config_run)
# Page 2: Simulation Tuning
elif simulation_option == "Simulation Tuning":
    st.title("Simulation Tuning")
    initial_cores_count_run = st.slider("Select the initial core count:", 1, 20, 7)

    # Display the full data
    st.json(data_run)

    # Define the sections available in metadata.json
    config_sections = ["algo_specific_config", "general_config", "prediction_config"]

    # Create a dictionary to hold selected parameters for each section
    params_to_tune = {}

    # Allow users to tune parameters from all sections
    for section in config_sections:
        st.subheader(f"Tuning {section}")
        selected_params = list(data_run[section].keys())

        # Multiselect to allow selecting parameters within each section
        selected_params_to_tune = st.multiselect(f"Select parameters to tune from {section}:", selected_params)

        # Process the selected parameters for tuning
        params_to_tune[section] = process_params_to_tune(selected_params_to_tune)

    st.divider()

    # Predictive parameters (example)
    predictive_params_to_tune = {"waiting_before_predict": [24 * 60]}

    # Create the ClusterStateConfig with all sections' data
    config_tun = ClusterStateConfig(config_dict=data_run)

    # Strategy selection
    strategy = st.radio("Select tuning strategy:", ["grid", "random"])

    # Number of combinations
    NUM_COMBINATIONS = None
    if strategy == "random":
        NUM_COMBINATIONS = st.number_input("Enter num_combinations:", min_value=1, value=500)
    else:
        # Calculate combinations for grid strategy
        all_combinations = [list(itertools.product(*params.values())) for params in params_to_tune.values()]
        config_param_combinations = list(itertools.product(*[item for sublist in all_combinations for item in sublist]))
        NUM_COMBINATIONS = len(config_param_combinations)
        st.text(f"Number of combinations (calculated): {NUM_COMBINATIONS}")
        st.text("The 'num_combinations' field is disabled because the strategy is 'grid'.")

    # Number of workers and initial cores count
    num_workers = st.number_input("Enter num_workers:", min_value=1, value=10)
    initial_cores_count = st.number_input("Enter initial_cores_count:", min_value=1, value=10)

    # Update session state with selected parameters
    st.session_state.tuning_has_run = False

    # Available dimensions for analysis
    available_dimensions = [
        "average_slack",
        "average_insufficient_cpu",
        "sum_slack",
        "sum_insufficient_cpu",
        "num_scalings",
        "num_insufficient_cpu",
        "insufficient_observations_percentage",
        "slack_percentage",
        "median_insufficient_cpu",
        "median_slack",
        "max_slack",
    ]
    # Run tuning when button clicked
    if st.button("Run Tuning"):
        st.session_state.tuning_has_run = True

        # Pass the section being tuned and parameters into the tuning function
        results = tune_with_strategy(
            config_path_run,
            strategy,
            num_combinations=NUM_COMBINATIONS,
            num_workers=num_workers,
            data_dir=data_dir,
            algorithm=selected_algorithm_names,
            initial_cpu_limit=initial_cores_count_run,
            algo_specific_params_to_tune=params_to_tune["algo_specific_config"],
            general_params_to_tune=params_to_tune["general_config"],
            predictive_params_to_tune=params_to_tune["prediction_config"],
        )

        st.write(f"Tuning results saved at: {data_dir}")
        config_metric_df = construct_config_metric_df(results)
        st.dataframe(config_metric_df)
else:
    st.write("WIP")
