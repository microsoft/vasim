#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#

"""
Module Name: TestPlotUtilsMetrics.

Description:
    Unit tests for scaling-count metrics in the analysis helpers. These are fast,
    deterministic tests that do not run the simulator end-to-end.

    They cover:
        - `calculate_metrics` counting `num_scalings` as the number of real changes
          in `CURR_LIMIT` between consecutive rows (regression for the off-by-one
          that `shift(-1)` introduced by leaving the last row as NaN).
        - `calculate_metrics` returning an empty dict for empty input.
        - `ParetoFrontier.preprocess_df` not raising when no configuration scales,
          which becomes reachable once `num_scalings` can legitimately be 0.
"""

import unittest

import pandas as pd

from vasim.simulator.analysis.ParetoFrontier import ParetoFrontier
from vasim.simulator.analysis.plot_utils import calculate_metrics


def _merged_from_limits(curr_limit):
    """
    Build a minimal `merged` DataFrame with the columns `calculate_metrics` reads.

    SLACK and INSUFFICIENT_CPU are set to zero because these tests only assert on
    `num_scalings`; CURR_LIMIT is positive so `slack_percentage` does not divide by zero.
    """
    length = len(curr_limit)
    return pd.DataFrame(
        {
            "CURR_LIMIT": curr_limit,
            "SLACK": [0.0] * length,
            "INSUFFICIENT_CPU": [0.0] * length,
        }
    )


class TestPlotUtilsMetrics(unittest.TestCase):
    """Fast unit tests for num_scalings computation and its Pareto normalization."""

    def test_num_scalings_counts_only_real_changes(self):
        """Count num_scalings as the number of CURR_LIMIT changes between consecutive rows."""
        cases = [
            ([4, 4, 4, 4, 4], 0),  # never scales
            ([4, 4, 8, 8, 8], 1),  # one change
            ([4, 8, 8, 2, 2], 2),  # two changes
            ([4], 0),  # single row
            ([4, 8, 4, 8, 4], 4),  # alternating
        ]
        for curr_limit, expected in cases:
            with self.subTest(curr_limit=curr_limit):
                metrics = calculate_metrics(_merged_from_limits(curr_limit))
                self.assertEqual(int(metrics["num_scalings"]), expected)

    def test_calculate_metrics_returns_empty_dict_for_empty_input(self):
        """An empty frame yields no metrics rather than a spurious scaling count."""
        self.assertEqual(calculate_metrics(pd.DataFrame({"CURR_LIMIT": []})), {})

    def test_preprocess_df_handles_no_scaling_configurations(self):
        """When no configuration scales, preprocessing must not raise on the missing norm column."""
        df = pd.DataFrame(
            {
                "sum_slack": [10.0, 20.0, 30.0],
                "sum_insufficient_cpu": [1.0, 2.0, 3.0],
                "num_scalings": [0, 0, 0],
            }
        )

        result = ParetoFrontier.preprocess_df(df)

        # No thrashing to filter out, so every row survives and the norm column is absent.
        self.assertEqual(len(result), 3)
        self.assertNotIn("num_scalings_norm", result.columns)

    def test_preprocess_df_filters_thrashing_when_scalings_present(self):
        """When configurations scale, the norm column is created and the 90th percentile is filtered."""
        df = pd.DataFrame(
            {
                "sum_slack": [10.0, 20.0, 30.0, 40.0],
                "sum_insufficient_cpu": [1.0, 2.0, 3.0, 4.0],
                "num_scalings": [1, 2, 3, 1000],
            }
        )

        result = ParetoFrontier.preprocess_df(df)

        self.assertIn("num_scalings_norm", result.columns)
        # The extreme thrashing row (1000) sits above the 90th percentile and is dropped,
        # leaving the low-scaling configurations behind.
        self.assertEqual(result["num_scalings"].tolist(), [1, 2, 3])


if __name__ == "__main__":
    unittest.main()
