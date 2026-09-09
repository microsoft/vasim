#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#

"""
Module Name: TestParameterTuning.

Description:
    Unit tests for the `tune_with_strategy` function in ParameterTuning.
    These tests mock the simulator and multiprocessing pool to verify that
    the returned result tuples contain the actual parameter values tested,
    not an empty dict (regression for issue #119).

Classes:
    TestTuneWithStrategyConfig:
        Verifies that each (config, metrics) tuple returned by tune_with_strategy
        has a non-empty config dict containing the tested parameter keys and values.
"""

import json
import unittest
from unittest.mock import MagicMock, patch

from vasim.recommender.cluster_state_provider.ClusterStateConfig import ClusterStateConfig
from vasim.simulator.ParameterTuning import tune_with_strategy


MINIMAL_CONFIG = {
    "general_config": {
        "window": 60,
        "lag": 10,
        "max_cpu_limit": 100,
        "min_cpu_limit": 1,
        "recovery_time": 10,
    },
    "algo_specific_config": {"addend": 1},
    "prediction_config": {"enabled": False},
}


def _make_fake_pool(modified_configs, data_dir, algorithm, initial_cpu_limit):
    """Return fake starmap results that mirror what _tune_parameters would return."""

    def fake_starmap(fn, args):
        return [(cfg, {"average_slack": 1.0, "num_scalings": 5}) for cfg, *_ in args]

    pool = MagicMock()
    pool.__enter__ = MagicMock(return_value=pool)
    pool.__exit__ = MagicMock(return_value=False)
    pool.starmap = fake_starmap
    return pool


class TestTuneWithStrategyConfig(unittest.TestCase):
    """Regression tests for issue #119: config dict in result tuples must be non-empty."""

    def _run_tune(self, strategy, algo_params, general_params, predictive_params=None):
        json_data = json.dumps(MINIMAL_CONFIG)
        with (
            patch("builtins.open", unittest.mock.mock_open(read_data=json_data)),
            patch("multiprocessing.Pool", side_effect=_make_fake_pool),
            patch("builtins.print"),
        ):
            return tune_with_strategy(
                config_path="dummy.json",
                strategy=strategy,
                num_combinations=2,
                num_workers=1,
                data_dir="/tmp/fake_data",
                algorithm="additive",
                initial_cpu_limit=30,
                algo_specific_params_to_tune=algo_params,
                general_params_to_tune=general_params,
                predictive_params_to_tune=predictive_params,
            )

    def test_grid_config_is_non_empty(self):
        """Config dict must not be empty; must contain all tuned parameter keys."""
        algo_params = {"addend": [1, 3]}
        general_params = {"window": [60, 120]}

        results = self._run_tune("grid", algo_params, general_params)

        self.assertGreater(len(results), 0)
        for config, metrics in results:
            self.assertIsInstance(config, dict)
            self.assertNotEqual(config, {}, "config dict must not be empty (issue #119)")
            self.assertIn("addend", config, "algo param 'addend' must appear in config dict")
            self.assertIn("window", config, "general param 'window' must appear in config dict")
            self.assertIn(config["addend"], algo_params["addend"])
            self.assertIn(config["window"], general_params["window"])

    def test_random_config_is_non_empty(self):
        """Random strategy must also return non-empty config dicts."""
        algo_params = {"addend": [1, 3, 5]}
        general_params = {"window": [60, 120]}

        results = self._run_tune("random", algo_params, general_params)

        self.assertGreater(len(results), 0)
        for config, _metrics in results:
            self.assertIsInstance(config, dict)
            self.assertNotEqual(config, {}, "config dict must not be empty (issue #119)")
            self.assertIn("addend", config)
            self.assertIn("window", config)

    def test_config_contains_only_tuned_keys(self):
        """Config dict should contain exactly the keys that were tuned, nothing extra."""
        algo_params = {"addend": [1]}
        general_params = {"window": [60]}

        results = self._run_tune("grid", algo_params, general_params)

        self.assertEqual(len(results), 1)
        config, _ = results[0]
        self.assertEqual(set(config.keys()), {"addend", "window"})
        self.assertEqual(config["addend"], 1)
        self.assertEqual(config["window"], 60)

    def test_predictive_params_in_config(self):
        """Predictive params must also appear in the returned config dict."""
        algo_params = {"addend": [1]}
        general_params = {"window": [60]}
        predictive_params = {"waiting_before_predict": [60]}

        results = self._run_tune("grid", algo_params, general_params, predictive_params)

        self.assertEqual(len(results), 1)
        config, _ = results[0]
        self.assertIn("waiting_before_predict", config)
        self.assertEqual(config["waiting_before_predict"], 60)


if __name__ == "__main__":
    unittest.main()
