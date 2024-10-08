#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#

"""
This module provides functions for processing and visualizing CPU usage data.

and new limit data from a cluster scaling simulator. The primary functionality
includes reading decision and performance log files, calculating key metrics
(such as slack and insufficient CPU), and generating line plots to visualize
the scaling decisions and their impact on CPU usage.

Functions:
    - read_data: Reads decision and performance log files, with optional resampling.
    - process_data: Merges and processes decision and performance data to calculate slack
                    and insufficient CPU.
    - calculate_metrics: Calculates important metrics like slack, insufficient CPU,
                         and scaling events.
    - create_line_plots: Creates line plots of CPU usage and new limits over time.
    - calculate_and_return_metrics_to_target: Combines all steps to compute and return
                                              metrics to a target directory.
    - plot_cpu_usage_and_new_limit_reformat: Creates and saves a line plot of CPU usage
                                             and new limits.
    - plot_cpu_usage_and_new_limit_plotnine: Creates and saves a line plot of CPU usage
                                             and new limits using the plotnine library.
"""
import os
import warnings

import pandas as pd
from plotnine import aes, geom_line, ggplot, labs

# Filter out UserWarning messages
warnings.filterwarnings("ignore", category=UserWarning)


def read_data(decision_file_path, perf_log_file_path, if_resample=True):
    """
    This function reads the decision and performance log files and returns the dataframes.

    This data is generated by the simulator in output_decision().

    Resampling is done to ensure that the data is at 1 minute intervals. Some data may be missing
    or duplicated, depending on the publisher.

    Parameters:
        decision_file_path (str): The path to the decisions.csv file.
        perf_log_file_path (str): The path to the performance log file.
        if_resample (bool, Optional): If True, the data will be resampled to 1 minute intervals.

    Returns:
        The decision and performance log dataframes.
    """
    if not os.path.exists(decision_file_path):
        raise FileNotFoundError(f"Decision file not found at path: {decision_file_path}")
    if not os.path.exists(perf_log_file_path):
        raise FileNotFoundError(f"Performance log file not found at path: {perf_log_file_path}")

    decision_df = pd.read_csv(decision_file_path)
    decision_df.drop_duplicates(subset=["LATEST_TIME"], inplace=True)
    decision_df["LATEST_TIME"] = pd.to_datetime(decision_df["LATEST_TIME"])
    if if_resample:
        decision_df["LATEST_TIME"] = pd.DatetimeIndex(decision_df["LATEST_TIME"]).floor("min")  # pylint: disable=no-member
        decision_df.drop_duplicates(subset=["LATEST_TIME"], keep="last", inplace=True)
    else:
        decision_df["LATEST_TIME"] = pd.DatetimeIndex(decision_df["LATEST_TIME"])
        decision_df.drop_duplicates(subset=["LATEST_TIME"], keep="last", inplace=True)
    perf_df = pd.read_csv(perf_log_file_path)
    perf_df["TIMESTAMP"] = pd.to_datetime(perf_df["TIMESTAMP"], format="%Y.%m.%d-%H:%M:%S:%f")
    if if_resample:
        perf_df["TIMESTAMP"] = pd.DatetimeIndex(perf_df["TIMESTAMP"]).floor("min")  # pylint: disable=no-member
        perf_df = perf_df.drop_duplicates(subset=["TIMESTAMP"], keep="last")
    else:
        perf_df["TIMESTAMP"] = pd.DatetimeIndex(perf_df["TIMESTAMP"])
        perf_df = perf_df.drop_duplicates(subset=["TIMESTAMP"], keep="last")

    return decision_df, perf_df


def process_data(decision_df, perf_df, if_resample=True):
    if if_resample:
        decision_resampled = decision_df.set_index("LATEST_TIME").resample("1T").ffill().reset_index()
        perf_log_resampled = perf_df.set_index("TIMESTAMP").resample("1T").ffill().reset_index()
    else:
        decision_resampled = decision_df
        perf_log_resampled = perf_df
    merged = pd.merge(decision_resampled, perf_log_resampled, left_on="LATEST_TIME", right_on="TIMESTAMP", how="left")

    merged["SLACK"] = (merged["CURR_LIMIT"] - merged["CPU_USAGE_ACTUAL"]).apply(lambda x: 0 if x <= 0 else x)
    merged["INSUFFICIENT_CPU"] = (merged["CPU_USAGE_ACTUAL"] - merged["CURR_LIMIT"]).apply(lambda x: 0 if x <= 0 else x)

    return merged


def calculate_metrics(merged):
    if len(merged) == 0:
        print("No data to calculate metrics.")
        return {}

    num_changes = (merged["CURR_LIMIT"] != merged["CURR_LIMIT"].shift(-1)).sum()

    metrics = {
        "average_slack": merged["SLACK"].mean(),
        "average_insufficient_cpu": merged["INSUFFICIENT_CPU"].mean(),
        "sum_slack": merged["SLACK"].sum(),
        "sum_insufficient_cpu": merged["INSUFFICIENT_CPU"].sum(),
        "num_scalings": num_changes,
        "num_insufficient_cpu": (merged["INSUFFICIENT_CPU"] != 0).sum(),
        "insufficient_observations_percentage": (merged["INSUFFICIENT_CPU"] != 0).sum() / len(merged) * 100,
        "slack_percentage": merged["SLACK"].sum() / merged["CURR_LIMIT"].sum() * 100,
        "median_insufficient_cpu": merged["INSUFFICIENT_CPU"].median(),
        "median_slack": merged["SLACK"].median(),
        "max_slack": merged["SLACK"].max(),
    }

    return metrics


def create_line_plots(merged):
    df1 = merged[["TIMESTAMP", "CURR_LIMIT"]]
    df2 = merged[["TIMESTAMP", "CPU_USAGE_ACTUAL"]]

    plot = (
        ggplot()
        + geom_line(df2, aes(x="TIMESTAMP", y="CPU_USAGE_ACTUAL"), color="blue")
        + geom_line(df1, aes(x="TIMESTAMP", y="CURR_LIMIT"), color="red", linetype="dashed")
        + labs(title="CPU Usage and New Limit over Time", x="Timestamp", y="Value")
    )

    return plot


def calculate_and_return_metrics_to_target(source_dir, target_dir, perf_log_file_path=None, decision_file_path=None):
    if not perf_log_file_path:
        perf_log_file_path = f"{source_dir}/{[f for f in os.listdir(source_dir) if f.endswith('.csv')][0]}"

    if not decision_file_path:
        decision_file_path = f"{target_dir}/decisions.csv"

    decision_df, perf_df = read_data(decision_file_path, perf_log_file_path)
    merged = process_data(decision_df, perf_df)
    metrics = calculate_metrics(merged)

    return metrics


def plot_cpu_usage_and_new_limit_reformat(
    source_dir,
    target_dir,
    perf_log_file_path=None,
    plot_show=False,
    decision_file_path=None,
):
    if not perf_log_file_path:
        perf_log_file_path = f"{source_dir}/{[f for f in os.listdir(source_dir) if f.endswith('.csv')][0]}"

    if not decision_file_path:
        decision_file_path = f"{target_dir}/decisions.csv"

    decision_df, perf_df = read_data(decision_file_path, perf_log_file_path)
    merged = process_data(decision_df, perf_df)
    plot = create_line_plots(merged)
    if plot_show:
        print(plot)
    # save plot to file
    plot.save(filename=f"{target_dir}/cpu_usage_and_new_limit.pdf", verbose=False)


def plot_cpu_usage_and_new_limit_plotnine(
    experiment_dir,
    perf_log_file_path=None,
    plot_show=False,
    decision_file_path=None,
    if_resample=True,
):
    if not perf_log_file_path:
        perf_log_file_path = f"{experiment_dir}/{[f for f in os.listdir(experiment_dir) if f.endswith('.csv')][0]}"

    if not decision_file_path:
        decision_file_path = f"{experiment_dir}/decisions.csv"
    target_folder = os.path.dirname(decision_file_path)
    decision_df, perf_df = read_data(decision_file_path, perf_log_file_path, if_resample)
    merged = process_data(decision_df, perf_df, if_resample=if_resample)
    plot = create_line_plots(merged)
    if plot_show:
        print(plot)
    # save plot to file

    plot.save(filename=f"{target_folder}/cpu_usage_and_new_limit.pdf", verbose=False)
