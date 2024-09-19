#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#

# pylint: disable=no-member # FIXME

import json
import os
from typing import Optional

import pandas as pd
import streamlit as st
from examples.streamlit.utils import run_simulation, unflatten_dict

from vasim.recommender.cluster_state_provider.ClusterStateConfig import (
    ClusterStateConfig,
)

st.set_page_config(layout="wide")
st.title("VASIM Autoscaling Simulator Toolkit Presentation")


@st.cache_data()
def create_charts(data):
    # Create a new DataFrame for Streamlit line_chart
    chart_data = pd.DataFrame({"TIMESTAMP": data["TIMESTAMP"], "CPU_USAGE_ACTUAL": data["CPU_USAGE_ACTUAL"]})

    # Plot the DataFrame using Streamlit line_chart
    st.sidebar.line_chart(chart_data.set_index("TIMESTAMP"))
    # pylint: disable=possibly-used-before-assignment # FIXME
    st.sidebar.success(f"Workload visualization finished for {selected_csv}")


def process_params_to_tune(selected_params):
    params_to_tune = {}

    for param_name in selected_params:
        param_values = process_parameter_input(param_name)
        params_to_tune[param_name] = param_values

    return params_to_tune


def process_parameter_input(param_name):
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
        df = pd.read_csv(selected_csv)
        df["TIMESTAMP"] = pd.to_datetime(df["TIMESTAMP"], format="%Y.%m.%d-%H:%M:%S:%f")
        df["TIMESTAMP"] = pd.DatetimeIndex(df["TIMESTAMP"]).floor("min")
        df = df.drop_duplicates(subset=["TIMESTAMP"], keep="last")
        perf_log_resampled = df.set_index("TIMESTAMP").resample("1T").ffill().reset_index()

        # Display the chart in the left sidebar
        chart_data = pd.DataFrame({"TIMESTAMP": df["TIMESTAMP"], "CPU_USAGE_ACTUAL": df["CPU_USAGE_ACTUAL"]})
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
else:
    st.write("WIP")
