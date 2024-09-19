#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#
import os
import shutil
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from vasim.simulator.ParameterTuning import tune_with_strategy

"""
This is a true run of simulator end to end.

It is not a unit test.

It calls tune_with_strategy, which performs a tuning run of the simulator, trying different configurations.
"""


class TestRunnerSimulatorIntegrationTest(unittest.TestCase):
    def setUp(self):

        # For this test we'll use the "mini" dataset, which is a smaller version of the full dataset
        root_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        self.source_dir = root_dir / "test_data/alibaba_control_c_29247_denom_1_mini"
        # Here we'll copy the source directory to a target directory, so we can modify the target directory without
        # affecting the source directory
        # Use a unique directory for each worker when using xdist to parallelize tests.
        uid = os.environ.get("PYTEST_XDIST_WORKER", "")
        self.target_dir = root_dir / f"test_data/tmp/{uid}/alibaba_control_c_29247_denom_1_test_to_delete_mini"
        self.target_dir_sim = root_dir / f"test_data/tmp/{uid}/alibaba_control_c_29247_denom_1_test_to_delete_mini_tuning"
        shutil.rmtree(self.target_dir, ignore_errors=True)
        shutil.copytree(self.source_dir, self.target_dir)

    @classmethod
    def setUpClass(cls):
        patcher = patch("builtins.print", MagicMock())  # Mock the print function globally
        patcher.start()
        cls.patcher = patcher

    def test_run_tuning_grid(self):
        """
        Now use the tuning function to test the tuning process.

        We will use the tune_with_strategy function. This function will run the simulator multiple times with
        different configurations and return the best configuration and the metrics for that configuration.
        """

        config_path = f"{self.source_dir}/metadata.json"
        general_params_to_tune = {
            "window": [60, 120],  # the window size is the number of minutes to consider for the prediction
        }
        algorithm_specific_params_to_tune = {
            "addend": [1, 3, 5, 10],  # the addend is the number of minutes to add to the prediction
        }
        predictive_params_to_tune = None
        selected_algorithm = "additive"
        initial_cpu_limit = 30
        strategy = "grid"  # "grid" and "random" are the only two strategies available currently
        data_dir = self.target_dir
        num_workers = 8  # how many threads to spin up
        num_combinations = 8  # how many combinations to try, here we'll do all 8 for consistency (2 windows * 4 addends)
        results = tune_with_strategy(
            config_path,
            strategy,
            num_combinations=num_combinations,
            num_workers=num_workers,
            data_dir=data_dir,
            algorithm=selected_algorithm,
            initial_cpu_limit=initial_cpu_limit,
            algo_specific_params_to_tune=algorithm_specific_params_to_tune,
            general_params_to_tune=general_params_to_tune,
            predictive_params_to_tune=predictive_params_to_tune,
        )

        assert results is not None

        expected = {
            "average_slack": 1.811722919741429,
            "average_insufficient_cpu": 0.024489840390519074,
            "sum_slack": 8118.330403361344,
            "sum_insufficient_cpu": 109.73897478991597,
            "num_scalings": 109,
            "num_insufficient_cpu": 41,
            "insufficient_observations_percentage": 0.9149743360856952,
            "slack_percentage": 17.29254351366721,
            "median_insufficient_cpu": 0.0,
            "median_slack": 1.5999999999999996,
            "max_slack": 22.98857142857143,
        }

        # TODO: There is a bug with 'grid' in that it always trys all combinations, even if num_combinations is less than the total.
        # assert len(results) == num_combinations
        # check the first result's combinations, which is deterministic because we're using grid
        self.assertEqual(results[0][0].general_config["window"], 60)
        # # check the first result's metrics
        self.assertAlmostEqual(results[0][1]["average_slack"], expected["average_slack"], places=2)
        self.assertAlmostEqual(results[0][1]["median_slack"], expected["median_slack"], places=2)
        self.assertAlmostEqual(results[0][1]["sum_slack"], expected["sum_slack"], places=2)
        self.assertAlmostEqual(results[0][1]["max_slack"], expected["max_slack"], places=2)
        self.assertAlmostEqual(results[0][1]["num_scalings"], expected["num_scalings"], places=2)
        self.assertAlmostEqual(results[0][1]["average_insufficient_cpu"], expected["average_insufficient_cpu"], places=2)
        self.assertAlmostEqual(results[0][1]["median_insufficient_cpu"], expected["median_insufficient_cpu"], places=2)
        self.assertAlmostEqual(results[0][1]["sum_insufficient_cpu"], expected["sum_insufficient_cpu"], places=2)
        self.assertAlmostEqual(results[0][1]["num_insufficient_cpu"], expected["num_insufficient_cpu"], places=2)
        self.assertAlmostEqual(
            results[0][1]["insufficient_observations_percentage"],
            expected["insufficient_observations_percentage"],
            places=2,
        )
        self.assertAlmostEqual(results[0][1]["slack_percentage"], expected["slack_percentage"], places=2)

        print(results)

    def test_run_tuning_grid_withpred(self):
        """This version provides a predictive parameter to tune as well."""

        config_path = f"{self.source_dir}/metadata.json"
        general_params_to_tune = {
            "window": [60, 120],  # the window size is the number of minutes to consider for the prediction
        }
        algorithm_specific_params_to_tune = {
            "addend": [1, 3, 5, 10],  # the addend is the number of minutes to add to the prediction
        }
        predictive_params_to_tune = {
            "waiting_before_predict": [60, 24 * 60],  # wait 1 hour or for 1 day before making a prediction
        }
        selected_algorithm = "additive"
        initial_cpu_limit = 30
        strategy = "grid"  # "grid" and "random" are the only two strategies available currently
        data_dir = self.target_dir
        num_workers = 8  # how many threads to spin up. Each thread will run a separate simulation, twice in this case
        # TODO: There is a bug with 'grid' in that it always trys all combinations, even if num_combinations is less than the total.
        # how many combinations to try, there are 16 (2 * 4 * 2) total possible combinations. (For grid, it will try all)
        num_combinations = 16
        results = tune_with_strategy(
            config_path,
            strategy,
            num_combinations=num_combinations,
            num_workers=num_workers,
            data_dir=data_dir,
            algorithm=selected_algorithm,
            initial_cpu_limit=initial_cpu_limit,
            algo_specific_params_to_tune=algorithm_specific_params_to_tune,
            general_params_to_tune=general_params_to_tune,
            predictive_params_to_tune=predictive_params_to_tune,
        )

        assert results is not None
        expected = {
            "average_slack": 1.8384330290920206,
            "average_insufficient_cpu": 0.019845341394759197,
            "sum_slack": 8238.018403361344,
            "sum_insufficient_cpu": 88.92697478991596,
            "num_scalings": 133,
            "num_insufficient_cpu": 46,
            "insufficient_observations_percentage": 1.0265565721937069,
            "slack_percentage": 17.49512801350962,
            "median_insufficient_cpu": 0.0,
            "median_slack": 1.58,
            "max_slack": 22.98857142857143,
        }

        # assert len(results) == num_combinations
        # check the first result's combinations, which is deterministic because we're using grid
        self.assertEqual(results[0][0].general_config["window"], 60)
        self.assertEqual(results[0][0]["prediction_config"]["waiting_before_predict"], 60)
        # # check the first result's metrics
        self.assertAlmostEqual(results[0][1]["average_slack"], expected["average_slack"], places=2)
        self.assertAlmostEqual(results[0][1]["median_slack"], expected["median_slack"], places=2)
        self.assertAlmostEqual(results[0][1]["sum_slack"], expected["sum_slack"], places=2)
        self.assertAlmostEqual(results[0][1]["max_slack"], expected["max_slack"], places=2)
        self.assertAlmostEqual(results[0][1]["num_scalings"], expected["num_scalings"], places=2)
        self.assertAlmostEqual(results[0][1]["average_insufficient_cpu"], expected["average_insufficient_cpu"], places=2)
        self.assertAlmostEqual(results[0][1]["median_insufficient_cpu"], expected["median_insufficient_cpu"], places=2)
        self.assertAlmostEqual(results[0][1]["sum_insufficient_cpu"], expected["sum_insufficient_cpu"], places=2)
        self.assertAlmostEqual(results[0][1]["num_insufficient_cpu"], expected["num_insufficient_cpu"], places=2)
        self.assertAlmostEqual(
            results[0][1]["insufficient_observations_percentage"],
            expected["insufficient_observations_percentage"],
            places=2,
        )
        self.assertAlmostEqual(results[0][1]["slack_percentage"], expected["slack_percentage"], places=2)

        print(results)

    def test_run_tuning_random(self):
        """
        This version used the random strategy to tune the parameters.

        We won't check the results, just that the function runs without error.
        """

        config_path = f"{self.source_dir}/metadata.json"
        general_params_to_tune = {
            "window": [60, 120],  # the window size is the number of minutes to consider for the prediction
        }
        algorithm_specific_params_to_tune = {
            "addend": [1, 3, 5, 10, 13],  # the addend is the number of minutes to add to the prediction
        }
        predictive_params_to_tune = None
        selected_algorithm = "additive"
        initial_cpu_limit = 30
        strategy = "random"  # "grid" and "random" are the only two strategies available currently
        data_dir = self.target_dir
        num_workers = 8  # how many threads to spin up
        num_combinations = 8  # how many combinations to try, here we'll do all 8 for consistency (2 windows * 4 addends)
        results = tune_with_strategy(
            config_path,
            strategy,
            num_combinations=num_combinations,
            num_workers=num_workers,
            data_dir=data_dir,
            algorithm=selected_algorithm,
            initial_cpu_limit=initial_cpu_limit,
            algo_specific_params_to_tune=algorithm_specific_params_to_tune,
            general_params_to_tune=general_params_to_tune,
            predictive_params_to_tune=predictive_params_to_tune,
        )

        assert results is not None
        # This should work for grid.
        assert len(results) == num_combinations
        # not checking the results because random

        print(results)

    def tearDown(self):
        shutil.rmtree(self.target_dir_sim, ignore_errors=True)
        shutil.rmtree(self.target_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
