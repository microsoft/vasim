import os
import unittest
import shutil
from unittest.mock import patch, MagicMock
from simulator.analysis.pareto_visualization import create_pareto_curve_from_folder
from simulator.ParameterTuning import tune_with_strategy
from pathlib import Path

'''
This is a true run of simulator end to end. It is not a unit test.

It calls tune_with_strategy, which performs a tuning run of the simulator, trying different configurations.
'''


class TestRunnerSimulatorIntegrationTest(unittest.TestCase):
    def setUp(self):

        # For this test we'll use the "mini" dataset, which is a smaller version of the full dataset
        ROOT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
        self.source_dir = ROOT_DIR / "test_data/alibaba_control_c_29247_denom_1_mini"
        # Here we'll copy the source directory to a target directory, so we can modify the target directory without
        # affecting the source directory
        self.target_dir = ROOT_DIR / "test_data/alibaba_control_c_29247_denom_1_test_to_delete_mini"
        self.target_dir_sim = ROOT_DIR / "test_data/alibaba_control_c_29247_denom_1_test_to_delete_mini_tuning"
        shutil.rmtree(self.target_dir, ignore_errors=True)
        shutil.copytree(self.source_dir, self.target_dir)

    @classmethod
    def setUpClass(cls):
        patcher = patch('builtins.print', MagicMock())  # Mock the print function globally
        patcher.start()
        cls.patcher = patcher

    def test_pareto2d(self):

        # First create some test data to tune
        config_path = f"{self.source_dir}/metadata.json"
        params_to_tune = {
            'window': [60, 120],  # the window size is the number of minutes to consider for the prediction
            "addend": [1, 2, 3],  # the addend is the number of minutes to add to the prediction
            "lag": [1, 15]  # the lag is the number of minutes to wait before making a prediction
        }
        predictive_params_to_tune = None
        selected_algorithm = "additive"
        initial_cpu_limit = 30
        strategy = "grid"  # use grid so the results are predictable
        data_dir = self.target_dir
        num_workers = 12  # how many threads to spin up
        # keep this number low for testing. Here there are 12 (2*3*2) combinations possible, try them all
        num_combinations = 12

        # This will populate the self.target_dir_sim folder with the results of the tuning
        tune_with_strategy(config_path, params_to_tune, predictive_params_to_tune, strategy,
                           num_combinations=num_combinations,
                           num_workers=num_workers, data_dir=data_dir, lag=10,
                           algorithm=selected_algorithm,
                           initial_cpu_limit=initial_cpu_limit)

        # Now we'll plot them
        pareto_2d = create_pareto_curve_from_folder(data_dir, self.target_dir_sim)

        assert pareto_2d is not None
        # Make sure the main parateo file was created
        self.assertTrue(os.path.exists(f"{self.target_dir_sim}/pareto_frontier.png"))

        # Now make sure the usage graphs in the folders are created.
        # The folders will be named after the UUID of the configuration
        self.assertTrue(len(list(Path(self.target_dir_sim).rglob("cpu_usage_and_new_limit.pdf"))) == num_combinations)

        ret = pareto_2d.find_closest_to_zero()
        # This function returns folder, config, dimension_1, and dimension_2 of the closest combination
        # We don't know what folder will be because it's random, but we can check the other values
        # We know that a config with the added value of 1 has the least slack and expect that to be the closest to zero
        self.assertEqual(ret[1]['addend'], 1)
        # The other two are dimensions: the slack and the insufficient cpu
        # We pre-computed these.
        self.assertAlmostEqual(ret[2], 7500, places=0)
        self.assertAlmostEqual(ret[3], 76.7, places=1)

    def tearDown(self):
        shutil.rmtree(self.target_dir_sim, ignore_errors=True)
        shutil.rmtree(self.target_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
