#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#
import random
import time

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

from vasim.simulator.analysis.ParetoFrontier import ParetoFrontier


def calculate_objective(alpha, sum_slack, sum_insufficient_cpu):
    """KS: what does this do? How was this formula derived?"""
    return alpha * sum_slack + sum_insufficient_cpu


class ParetoFront2D(ParetoFrontier):
    def __init__(self, df, dimension_1="sum_slack", dimension_2="sum_insufficient_cpu", directory_to_save_files=None):
        """
        This class is used to find the Pareto frontier of a 2D space.

        :param df: DataFrame containing the data to be analyzed.
        :param dimension_1: The first dimension to be considered. This is the y-axis.
        :param dimension_2: The second dimension to be considered. This is the x-axis.
        :param directory_to_save_files: The directory where the files will be saved (csv, png, etc).
        """
        super().__init__(df)
        self.df = df
        self.dimension_1 = dimension_1
        self.dimension_2 = dimension_2
        self.result = {}
        self.pareto_configs = set()
        self.alphas = []
        self.denominator = 1
        self.files = directory_to_save_files
        # TODO: I think the 500 needs to be a function of the number of configurations (size of df)
        for x_ in range(500):
            alpha = np.exp(random.uniform(-50, 50))
            best_config = self.get_best_config_for_alpha(alpha)
            self.result[alpha] = best_config
            self.alphas.append(alpha)
            self.pareto_configs.add(best_config["uuid"])
        # Save the result to csv if a directory is provided
        if self.files is not None:
            result_df = pd.DataFrame.from_dict(self.result, orient="index")
            result_df.to_csv(f"{self.files}/pareto_frontier_denominator_{self.denominator}2d.csv")

    def get_best_config_for_alpha(self, alpha):
        """TODO: KS: what does this do?"""
        sum_slack = self.df[self.dimension_1]
        sum_insufficient_cpu = self.df[self.dimension_2]
        objectives = calculate_objective(alpha, sum_slack, sum_insufficient_cpu)

        # Drop NaN values from the objectives Series
        objectives = objectives.dropna()

        if objectives.empty:
            return None  # Handle case when objectives Series is empty

        # Ensure objectives Series is numeric
        objectives = pd.to_numeric(objectives, errors="coerce")

        # Find the index of the row with the minimum objective value
        min_index = objectives.idxmin()

        # Extract the best configuration details
        best_config = {
            "uuid": self.df.loc[min_index, "uuid"],
            self.dimension_1: self.df.loc[min_index, self.dimension_1],
            self.dimension_2: self.df.loc[min_index, self.dimension_2],
            "recommender_details": self.df.loc[min_index],
        }

        return best_config

    def find_closest_to_zero(self):
        """
        This function finds the closest combination to (0, 0) for the given dimensions.

        Returns:
            Tuple: A tuple containing the folder, config, dimension_1, and dimension_2 of the closest combination
        """

        closest_combination = None
        closest_distance = float("inf")

        for index, row in self.workload_run_metrics.iterrows():
            dimension_1 = row[self.dimension_1]
            dimension_2 = row[self.dimension_2]
            folder = row["folder"]
            config = row["config"]

            # Calculate the Euclidean distance between the point and (0, 0)
            distance = np.sqrt(dimension_1**2 + dimension_2**2)

            # Check if the current combination is closer to (0, 0, 0) than the previous closest one
            if distance < closest_distance:
                closest_combination = (folder, config, dimension_1, dimension_2)
                closest_distance = distance

        # Both log and print the closest combination
        # TODO: Setup logger for this function.
        print(f"Closest combination to (0, 0) is dimension_1: {closest_combination[2]}, dimension_2: {closest_combination[3]}")
        print(f"Folder: {closest_combination[0]}, Config: {closest_combination[1]}")

        return closest_combination

    def plot_scatter_frontier(self, plot_filename="pareto_frontier"):
        fig, ax = plt.subplots()
        for alpha in self.alphas:
            ax.scatter(
                self.result[alpha][self.dimension_2] / self.denominator,
                self.result[alpha][self.dimension_1] / self.denominator,
                label=f"alpha={alpha:.3f}",
                s=5,
            )
            ax.annotate(alpha, (self.result[alpha][self.dimension_2], self.result[alpha][self.dimension_1]))
        # ax.legend()
        ax.set_ylabel(f"{self.dimension_1}")
        ax.set_xlabel(f"{self.dimension_2} CPU time")
        ax.set_title("Pareto frontier")

        plt.show()
        plt.savefig(f"{plot_filename}.pdf")

    def plot_scatter_with_pareto(self):
        """If no path was provided (self.files), the plot will be displayed only."""
        # colors = ['blue' if val else 'green' for val in df['predictive']]

        x_values = self.df[self.dimension_2] / self.denominator
        y_values = self.df[self.dimension_1] / self.denominator
        fig, ax = plt.subplots(figsize=(4, 3))

        plt.rcParams["pdf.fonttype"] = 42
        plt.rcParams["ps.fonttype"] = 42
        plt.rcParams["text.usetex"] = False

        plt.scatter(x_values, y_values, s=5, alpha=0.5)

        for alpha in self.alphas:
            folder = self.result[alpha]["uuid"]
            # For easier labels, save only the the trailing characters after the last '-'
            folder = folder.split("-")[-1]

            ax.scatter(
                self.result[alpha][self.dimension_2] / self.denominator,
                self.result[alpha][self.dimension_1] / self.denominator,
                label=f"alpha={alpha:.3f}",
                s=20,
                marker="x",
                color="red",
            )
            # Now we'll add the folder name to the point, with a light gray font
            ax.annotate(
                folder,
                (self.result[alpha][self.dimension_2], self.result[alpha][self.dimension_1]),
                fontsize=6,
                color="gray",
            )

            # ax.annotate(alpha, (metrics['sum_insufficient_cpu'], metrics['sum_slack']))
            # self.plot_folders.append((self.result[alpha]['folder'], self.result[alpha][self.dimension_1], self.result[alpha][self.dimension_2]))

        # Now plot the point closest to (0, 0)
        closest_combination = self.find_closest_to_zero()
        # label it on the left side of the point
        ax.scatter(
            closest_combination[3] / self.denominator,
            closest_combination[2] / self.denominator,
            s=50,
            marker="+",
            color="green",
        )
        # For easier labels, save only the the trailing characters after the last '-'
        folder_closest = closest_combination[0].split("-")[-1]
        ax.annotate(
            folder_closest,
            (
                closest_combination[3],
                closest_combination[2],
            ),
            fontsize=15,
            color="black",
        )

        # put a small note at the bottom about how axes do not start at 0.
        plt.text(
            0.5,
            0.01,
            "Note: Axes do not start at 0. Best config in green",
            ha="center",
            va="center",
            transform=ax.transAxes,
            fontsize=8,
            color="gray",
        )

        plt.ylabel(f"{self.dimension_1}", rotation=90)
        plt.xlabel(f"{self.dimension_2}")
        fig.tight_layout()
        plt.title(f"{self.dimension_1} vs {self.dimension_2}")
        if self.files is not None:
            print(f"Saving plot to {self.files}/pareto_frontier.png")
            # self.logger.info(f"Saving plot to {self.files}/pareto_frontier.png")
            plt.savefig(f"{self.files}/pareto_frontier.png")
        plt.show()
