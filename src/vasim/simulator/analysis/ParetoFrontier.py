#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#
import json
import os
from abc import ABC, abstractmethod

import numpy as np
import pandas as pd

from vasim.recommender.cluster_state_provider.ClusterStateConfig import (
    ClusterStateConfig,
)


class ParetoFrontier(ABC):
    def __init__(self, workload_run_metrics):
        self.workload_run_metrics = workload_run_metrics

    def get_pareto_frontier(self):
        pass

    def filter_out_less_than_by_dimension(self, dimension, value):
        return list(filter(lambda x: x[2][dimension] <= value, self.workload_run_metrics))

    def find_closest_to_zero(self):
        pass

    @staticmethod
    def preprocess_df(df):
        # normalize by dividing by max value
        if df["sum_slack"].max() > 0:
            df["sum_slack_norm"] = df["sum_slack"] / df["sum_slack"].max()
        if df["sum_insufficient_cpu"].max() > 0:
            df["sum_insufficient_cpu_norm"] = df["sum_insufficient_cpu"] / df["sum_insufficient_cpu"].max()
        if df["num_scalings"].max() > 0:
            df["num_scalings_norm"] = df["num_scalings"] / df["num_scalings"].max()

        # Filter out 90 percentile of num_scalings_norm, to eliminate thrashing cases
        # Lots of times, the number of scalings is very high, which is not desirable
        df = df[df["num_scalings_norm"] <= np.percentile(df["num_scalings_norm"], 90)]
        return df

    @staticmethod
    def read_metrics(file_path):
        with open(file_path, "r") as file:
            return json.load(file)

    @staticmethod
    def process_folder(target_folder, folder):
        if folder.startswith("target_"):
            metadata_file = f"{target_folder}/{folder}/metadata.json"
            if os.path.exists(f"{target_folder}/{folder}/calc_metrics.json") and os.path.exists(metadata_file):
                config = ClusterStateConfig(filename=metadata_file)
                # read metrics from calc_metrics.json
                metrics = ParetoFrontier.read_metrics(f"{target_folder}/{folder}/calc_metrics.json")
                return (folder, config, metrics)
        return None

    @staticmethod
    def create_df(results):
        df = pd.DataFrame(
            columns=[
                "folder",
                "sum_slack",
                "average_slack",
                "insufficient_observations_percentage",
                "slack_percentage",
                "sum_insufficient_cpu",
                "num_scalings",
            ]
        )
        rows = []
        for folder, config, metrics in results:
            row = pd.Series(
                {
                    "folder": folder,
                    "sum_slack": metrics["sum_slack"],
                    "sum_insufficient_cpu": metrics["sum_insufficient_cpu"],
                    "num_scalings": metrics["num_scalings"],
                    "average_slack": metrics["average_slack"],
                    "insufficient_observations_percentage": metrics["insufficient_observations_percentage"],
                    "slack_percentage": metrics["slack_percentage"],
                    "window": config.general_config["window"],
                    "uuid": config.get("uuid", folder.lstrip("target_") or "unknown"),
                    "predictive": config.prediction_config["waiting_before_predict"] < 24 * 60 * 2,
                    "waiting_before_predict": config.prediction_config["waiting_before_predict"],
                    "frequency_minutes": config.prediction_config["frequency_minutes"],
                    "forecasting_models": config.prediction_config["forecasting_models"],
                    "minutes_to_predict": config.prediction_config["minutes_to_predict"],
                    "total_predictive_window": config.prediction_config["total_predictive_window"],
                    "config": config,
                }
            )
            rows.append(row)  # Add the row to the list

        df = pd.concat(rows, axis=1).T
        return df
