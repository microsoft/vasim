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

from vasim.simulator.InMemorySimulator import InMemoryRunnerSimulator


class TestRunnerSimulatorIntegrationTest(unittest.TestCase):
    """
    This is a true run of simulator end to end.

    It is not a unit test.

    It calls InMemoryRunnerSimulator, which performs a single run of the simulator without tuning.
    """

    def setUp(self):
        root_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        self.source_dir = root_dir / "test_data/alibaba_control_c_29247_denom_1"
        # Here we'll copy the source directory to a target directory, so we can modify the target directory without
        # affecting the source directory
        # Use a unique directory for each worker when using xdist to parallelize tests.
        uid = os.environ.get("PYTEST_XDIST_WORKER", "")
        self.target_dir = root_dir / f"test_data/tmp/{uid}/alibaba_control_c_29247_denom_1_test_to_delete"
        self.target_dir_sim = root_dir / f"test_data/tmp/{uid}/alibaba_control_c_29247_denom_1_test_to_delete_simulations"
        shutil.rmtree(self.target_dir, ignore_errors=True)
        shutil.copytree(self.source_dir, self.target_dir)

    @classmethod
    def setUpClass(cls):
        patcher = patch("builtins.print", MagicMock())  # Mock the print function globally
        patcher.start()
        cls.patcher = patcher

    def test_run_multiplicative_algo(self):
        """Test a single run of the simulator with the multiplicative algorithm."""
        runner = InMemoryRunnerSimulator(self.target_dir, initial_cpu_limit=14, algorithm="multiplicative")
        assert runner.initial_cpu_limit == 14
        results = runner.run_simulation()
        assert results is not None

        # assert file exists
        assert os.path.exists(self.target_dir)

        # now we need to check the files. There will be a random uuid, so we'll just grab the first folder
        # it will be self.target_dir + (some random uuid) + "_simulations"
        folder = os.listdir(self.target_dir_sim)[0]
        sim_dir = os.path.join(self.target_dir_sim, folder)  # todo add _simulations

        assert os.path.exists(os.path.join(sim_dir, "decisions.txt"))
        assert os.path.exists(os.path.join(sim_dir, "metadata.json"))
        assert os.path.exists(os.path.join(sim_dir, "perf_event_log.csv"))

        # With the multiplicative algorithm, we expect the average slack to be large because the multiplier is 2, mean
        # the desired CPU usage is twice the actual CPU usage.

        expected = {
            "average_slack": 9.255356800676894,
            "average_insufficient_cpu": 8.710042679209252e-06,
            "sum_slack": 106260.75142857143,
            "sum_insufficient_cpu": 0.10000000000000142,
            "num_scalings": 466,
            "num_insufficient_cpu": 1,
            "insufficient_observations_percentage": 0.008710042679209128,
            "slack_percentage": 51.50325900419567,
            "median_insufficient_cpu": 0.0,
            "median_slack": 9.845714285714289,
            "max_slack": 16.759999999999998,
        }
        self.assertAlmostEqual(results["average_slack"], expected["average_slack"], places=2)
        self.assertAlmostEqual(results["median_slack"], expected["median_slack"], places=2)
        self.assertAlmostEqual(results["sum_slack"], expected["sum_slack"], places=2)
        self.assertAlmostEqual(results["max_slack"], expected["max_slack"], places=2)
        self.assertAlmostEqual(results["num_scalings"], expected["num_scalings"], places=2)
        self.assertAlmostEqual(results["average_insufficient_cpu"], expected["average_insufficient_cpu"], places=2)
        self.assertAlmostEqual(results["median_insufficient_cpu"], expected["median_insufficient_cpu"], places=2)
        self.assertAlmostEqual(results["sum_insufficient_cpu"], expected["sum_insufficient_cpu"], places=2)
        self.assertAlmostEqual(results["num_insufficient_cpu"], expected["num_insufficient_cpu"], places=2)
        self.assertAlmostEqual(
            results["insufficient_observations_percentage"],
            expected["insufficient_observations_percentage"],
            places=2,
        )
        self.assertAlmostEqual(results["slack_percentage"], expected["slack_percentage"], places=2)

    def test_run_additive_algo(self):
        """Test a single run of the simulator with the additive algorithm."""
        runner = InMemoryRunnerSimulator(self.target_dir, initial_cpu_limit=14, algorithm="additive")
        results = runner.run_simulation()
        assert results is not None

        # assert file exists
        assert os.path.exists(self.target_dir)

        # now we need to check the files. There will be a random uuid, so we'll just grab the first folder
        # it will be self.target_dir + (some random uuid) + "_simulations"
        folder = os.listdir(self.target_dir_sim)[0]
        sim_dir = os.path.join(self.target_dir_sim, folder)  # todo add _simulations

        assert os.path.exists(os.path.join(sim_dir, "decisions.txt"))
        assert os.path.exists(os.path.join(sim_dir, "metadata.json"))
        assert os.path.exists(os.path.join(sim_dir, "perf_event_log.csv"))

        expected = {
            "average_slack": 2.629179874824244,
            "average_insufficient_cpu": 0.006747035474759541,
            "sum_slack": 30185.614142857143,
            "sum_insufficient_cpu": 77.46271428571428,
            "num_scalings": 347,
            "num_insufficient_cpu": 23,
            "insufficient_observations_percentage": 0.20033098162180996,
            "slack_percentage": 23.19009122417309,
            "median_insufficient_cpu": 0.0,
            "median_slack": 2.539999999999999,
            "max_slack": 14.4,
        }

        # We expect the average slack to be between 2 and 3, because the addend is 2, meaning we want to keep
        # a buffer of 2 cores. The slack is the difference between the desired CPU usage and the actual CPU usage.
        # We always round up to the nearest 0.5 core, so the slack should be between 2 and 3.
        assert 2 <= results["average_slack"] <= 3, f"Expected slack to be between 2 and 3, but got {results['average_slack']}"

        # Now some tests based on expected we know to be true
        self.assertAlmostEqual(results["average_slack"], expected["average_slack"], places=2)
        self.assertAlmostEqual(results["median_slack"], expected["median_slack"], places=2)
        self.assertAlmostEqual(results["sum_slack"], expected["sum_slack"], places=2)
        self.assertAlmostEqual(results["max_slack"], expected["max_slack"], places=2)
        self.assertAlmostEqual(results["num_scalings"], expected["num_scalings"], places=2)
        self.assertAlmostEqual(results["average_insufficient_cpu"], expected["average_insufficient_cpu"], places=2)
        self.assertAlmostEqual(results["median_insufficient_cpu"], expected["median_insufficient_cpu"], places=2)
        self.assertAlmostEqual(results["sum_insufficient_cpu"], expected["sum_insufficient_cpu"], places=2)
        self.assertAlmostEqual(results["num_insufficient_cpu"], expected["num_insufficient_cpu"], places=2)
        self.assertAlmostEqual(
            results["insufficient_observations_percentage"],
            expected["insufficient_observations_percentage"],
            places=2,
        )
        self.assertAlmostEqual(results["slack_percentage"], expected["slack_percentage"], places=2)

    def tearDown(self):
        shutil.rmtree(self.target_dir_sim, ignore_errors=True)
        shutil.rmtree(self.target_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
