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
    This module contains unit tests for the `tune_with_strategy` function. The simulation
    runs and the multiprocessing pool are mocked out, so the tests only exercise the
    parameter combination and result collection logic of the tuning code.

Classes:
    TestTuneWithStrategy:
        Verifies that every (config, metrics) tuple returned by `tune_with_strategy` carries
        the configuration that was actually simulated, including the tuned algorithm specific,
        general and predictive parameters.
"""

import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from vasim.recommender.cluster_state_provider.ClusterStateConfig import (
    ClusterStateConfig,
)
from vasim.simulator.ParameterTuning import tune_with_strategy


def _fake_pool(processes=1):  # pylint: disable=unused-argument
    """Return a fake multiprocessing pool that runs the mapped function in-process."""
    pool = MagicMock()
    pool.__enter__.return_value = pool
    pool.__exit__.return_value = False
    pool.starmap = lambda function, iterable: [function(*arguments) for arguments in iterable]
    return pool


def _fake_tune_parameters(config, _data_dir, _algorithm, _initial_cpu_limit):
    """Return the config that would have been simulated, along with dummy metrics."""
    return config, {"average_slack": 1.0, "num_scalings": 5}


class TestTuneWithStrategy(unittest.TestCase):

    def setUp(self):
        root_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        self.config_path = str(root_dir / "test_data/alibaba_control_c_29247_denom_1_mini/metadata.json")
        for patcher in (
            patch("multiprocessing.Pool", side_effect=_fake_pool),
            patch("vasim.simulator.ParameterTuning._tune_parameters", side_effect=_fake_tune_parameters),
            patch("builtins.print", MagicMock()),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)

    def _tune(self, strategy, num_combinations=2, **params_to_tune):
        return tune_with_strategy(
            config_path=self.config_path,
            strategy=strategy,
            num_combinations=num_combinations,
            num_workers=1,
            data_dir="data_dir",
            algorithm="additive",
            initial_cpu_limit=30,
            **params_to_tune,
        )

    def test_grid_results_contain_tuned_parameters(self):
        """Each result must carry the config that was simulated, not an empty one."""
        results = self._tune(
            "grid", algo_specific_params_to_tune={"addend": [1, 3]}, general_params_to_tune={"window": [20, 40]}
        )

        self.assertEqual(len(results), 4)  # 2 addends x 2 windows
        for config, metrics in results:
            self.assertIsInstance(config, ClusterStateConfig)
            self.assertIn(config.algo_specific_config["addend"], [1, 3])
            self.assertIn(config.general_config["window"], [20, 40])
            self.assertEqual(metrics["num_scalings"], 5)

    def test_grid_results_contain_tuned_predictive_parameters(self):
        """Predictive parameters must be tuned and returned too."""
        results = self._tune(
            "grid",
            algo_specific_params_to_tune={"addend": [1]},
            general_params_to_tune={"window": [20]},
            predictive_params_to_tune={"waiting_before_predict": [60]},
        )

        self.assertEqual(len(results), 1)
        config, _ = results[0]
        self.assertEqual(config.prediction_config["waiting_before_predict"], 60)

    def test_random_results_contain_tuned_parameters(self):
        """The random strategy must also return the configs that were simulated."""
        results = self._tune("random", num_combinations=3, general_params_to_tune={"window": [20, 40, 60]})

        self.assertEqual(len(results), 3)
        for config, _ in results:
            self.assertIsInstance(config, ClusterStateConfig)
            self.assertIn(config.general_config["window"], [20, 40, 60])

    def test_invalid_parameter_name_is_rejected(self):
        """Tuning a parameter that is not part of the base config must raise."""
        with self.assertRaises(AssertionError):
            self._tune("grid", general_params_to_tune={"not_a_parameter": [1]})


if __name__ == "__main__":
    unittest.main()
