#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#

"""
Module Name: Pareto Curve and Analysis.

Description:
    This module is responsible for creating Pareto curves and analyzing the results of
    different configurations in a simulation. It loads performance data, processes
    simulation results in parallel, and plots the Pareto front and corresponding CPU usage
    graphs.

    The primary purpose of this module is to:
    1. Process the results from various configurations.
    2. Generate Pareto frontier plots to evaluate the performance of different parameter sets.
    3. Create individual graphs comparing CPU usage and scaling decisions for each configuration.

Functions:
    _load_results_parallel(target_folder):
        Loads the results in parallel from the specified folder, processing each configuration folder using
        multiprocessing to improve performance.

    create_pareto_curve_from_folder(original_data, tuned_data, cached_df=None, plot_surface=True):
        Creates a Pareto curve based on the performance data in the specified folder. It generates a scatter plot
        with the Pareto front and, for each configuration, plots the CPU usage and scaling decisions. Optionally,
        a cached DataFrame can be passed to avoid reprocessing the data.

Parameters:
    original_data (str): The directory containing the original performance log CSV files.
    tuned_data (str): The directory containing different tuned configurations' results.
    cached_df (str, optional): Path to a cached DataFrame file to avoid reprocessing results.
    plot_surface (bool, optional): Whether to plot the Pareto front surface. Defaults to True.

Returns:
    ParetoFront2D: The `ParetoFront2D` object, representing the Pareto front generated from the data.

Usage:
    The main function `create_pareto_curve_from_folder` can be used to analyze the results
    from multiple configurations, create Pareto frontiers, and plot graphs for each configuration.
"""

import multiprocessing
import os
import time

import pandas as pd

from vasim.simulator.analysis.ParetoFront2D import ParetoFront2D
from vasim.simulator.analysis.ParetoFrontier import ParetoFrontier
from vasim.simulator.analysis.plot_utils import plot_cpu_usage_and_new_limit_reformat


def _load_results_parallel(target_folder):
    with multiprocessing.Pool() as pool:
        results = pool.starmap(
            ParetoFrontier.process_folder, ((target_folder, folder) for folder in os.listdir(target_folder))
        )

    # Filter out None values from the results
    filtered_results = [result for result in results if result is not None]
    return filtered_results


def create_pareto_curve_from_folder(original_data, tuned_data, cached_df=None, plot_surface=True):
    """
    This function creates a Pareto curve from the results and puts them in the target_folder.

    It will also create a graph for each folder in the tuned_data folder with the decisions of this parameter.

    Optionally you can pass a cached dataframe to avoid reprocessing the results.

    Parameters:
        original_data (str): The original data folder with the performance log csv files.
        tuned_data (str): The tuned data folder with different configurations.
        cached_df (str, Optional): The cached dataframe to avoid reprocessing the results.
        plot_surface (bool, Optional): Whether to plot the surface graph. Defaults to True.

    Returns:
        ParetoFront2D: The ParetoFront2D object.
    """

    if not cached_df:
        results = _load_results_parallel(tuned_data)
        df = ParetoFrontier.create_df(results)
        df = ParetoFrontier.preprocess_df(df)
        df.to_csv(f"{tuned_data}/cached_{str(time.time())}.csv")
    else:
        df = pd.read_csv(cached_df)

    pareto_2d = ParetoFront2D(df, directory_to_save_files=tuned_data)

    if plot_surface:
        # TODO: add more comments explaining this.
        pareto_2d.plot_scatter_with_pareto()

        for uuid_id in pareto_2d.pareto_configs:
            folder_name = f"{tuned_data}/target_{uuid_id}"
            # This generates a graph for each folder in the tuned_data folder with the dicisions of this parameter
            # combination graphed along with the CPU usage reported in the original data.
            plot_cpu_usage_and_new_limit_reformat(source_dir=original_data, target_dir=folder_name, plot_show=True)
        print(f"Plotted {tuned_data}/pareto_frontier.png")

    return pareto_2d
