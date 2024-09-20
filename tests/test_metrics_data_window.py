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
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from vasim.recommender.cluster_state_provider.ClusterStateConfig import (
    ClusterStateConfig,
)
from vasim.recommender.cluster_state_provider.FileClusterStateProvider import (
    FileClusterStateProvider,
)
from vasim.simulator.InMemorySimulator import InMemoryRunnerSimulator
from vasim.simulator.SimulatedInMemoryPredictiveClusterStateProvider import (
    SimulatedInMemoryPredictiveClusterStateProvider,
)


class TestSimulatedInMemoryPredictiveClusterStateProvider(unittest.TestCase):
    """
    Although this is testing the PredictiveFileClusterStateProvider, it is using the.

    SimulatedInMemoryPredictiveClusterStateProvider.

    There is no prediction for this because the datasize is too small to trigger the prediction.
    """

    def setUp(self):

        root_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        self.source_dir = root_dir / "test_data/alibaba_control_c_29247_denom_1_mini"
        self.source_dir_toosmall = root_dir / "test_data/alibaba_control_c_29247_denom_1_toosmall"
        # Here we'll copy the source directory to a target directory, so we can modify the target directory without
        # affecting the source directory
        # Use a unique directory for each worker when using xdist to parallelize tests.
        uid = os.environ.get("PYTEST_XDIST_WORKER", "")
        self.target_dir = root_dir / f"test_data/tmp/{uid}/alibaba_control_c_29247_denom_1_test_to_delete_mini"
        self.target_dir_toosmall = root_dir / f"test_data/tmp/{uid}/alibaba_control_c_29247_denom_1_test_to_delete_toosmall"
        # TODO: sometimes the output is 'simulations', sometimes it is 'tuning'. this is confusing.
        self.target_dir_sim = root_dir / f"test_data/tmp/{uid}/alibaba_control_c_29247_denom_1_test_to_delete_mini_simulations"
        self.target_dir_sim_toosmall = (
            root_dir / f"test_data/tmp/{uid}/alibaba_control_c_29247_denom_1_test_to_delete_toosmall_simulations"
        )
        shutil.rmtree(self.target_dir, ignore_errors=True)
        shutil.rmtree(self.target_dir_toosmall, ignore_errors=True)
        shutil.copytree(self.source_dir, self.target_dir)
        shutil.copytree(self.source_dir_toosmall, self.target_dir_toosmall)
        self.config = ClusterStateConfig(filename=self.source_dir / "metadata.json")

    def test_read_metrics_data(self):
        """Test the read_metrics_data method, which is the window of data to process next."""

        sim_inmem_p_prov = SimulatedInMemoryPredictiveClusterStateProvider(
            window=40,
            lag=10,
            data_dir=self.target_dir,
            decision_file_path=self.target_dir / "decisions.txt",
            max_cpu_limit=14,
            config=self.config,
            prediction_config=self.config.prediction_config,
            general_config=self.config.general_config,
        )

        # Set up test data
        sim_inmem_p_prov.curr_cpu_limit = 10
        sim_inmem_p_prov.current_time = pd.Timestamp(datetime(2024, 1, 1, 0, 7, 0))
        sim_inmem_p_prov.end_time = pd.Timestamp(datetime(2024, 1, 1, 0, 10, 0))
        sim_inmem_p_prov.config.general_config = {"window": 5, "lag": 2}
        sim_inmem_p_prov.recorded_data = pd.DataFrame(
            [
                {"timestamp": pd.Timestamp(datetime(2024, 1, 1, 0, 0, 0)), "cpu": 1.0},
                {"timestamp": pd.Timestamp(datetime(2024, 1, 1, 0, 1, 0)), "cpu": 2.0},
                {"timestamp": pd.Timestamp(datetime(2024, 1, 1, 0, 2, 0)), "cpu": 3.0},  # should be in window
                {"timestamp": pd.Timestamp(datetime(2024, 1, 1, 0, 3, 0)), "cpu": 4.0},  # should be in window
                {"timestamp": pd.Timestamp(datetime(2024, 1, 1, 0, 4, 0)), "cpu": 5.0},  # should be in window
                {"timestamp": pd.Timestamp(datetime(2024, 1, 1, 0, 5, 0)), "cpu": 6.0},  # should be in window
                {"timestamp": pd.Timestamp(datetime(2024, 1, 1, 0, 6, 0)), "cpu": 7.0},  # should be in window.
                {"timestamp": pd.Timestamp(datetime(2024, 1, 1, 0, 7, 0)), "cpu": 8.0},  # CURRENT TIME.
                {"timestamp": pd.Timestamp(datetime(2024, 1, 1, 0, 8, 0)), "cpu": 9.0},
                {"timestamp": pd.Timestamp(datetime(2024, 1, 1, 0, 9, 0)), "cpu": 10.0},
                {"timestamp": pd.Timestamp(datetime(2024, 1, 1, 0, 10, 0)), "cpu": 11.0},
            ]
        )
        sim_inmem_p_prov.recorded_data.set_index("timestamp", inplace=True)

        # Call the method
        result = sim_inmem_p_prov.read_metrics_data()

        # Verify the result
        expected_result = pd.DataFrame(
            [
                {"cpu": 3.0},  # This is inclusive of the current time, so 2mins:3cpu is still in the 5min window (2m-7m)
                {"cpu": 4.0},
                {"cpu": 5.0},
                {"cpu": 6.0},
                {"cpu": 7.0},
                {"cpu": 8.0},
            ]
        )

        type(result)
        self.assertEqual(result["cpu"].values.tolist(), expected_result["cpu"].values.tolist())

    def test_get_next_recorded_data(self):
        """Test the read_metrics_data method, which is the window of data to process next."""

        file_cs_prov = FileClusterStateProvider(
            window=40,
            lag=10,
            data_dir=self.target_dir,
            decision_file_path=self.target_dir / "decisions.txt",
            max_cpu_limit=14,
            config=self.config,
            prediction_config=self.config.prediction_config,
            general_config=self.config.general_config,
        )

        # Set up test data
        file_cs_prov.curr_cpu_limit = 10
        file_cs_prov.current_time = pd.Timestamp(datetime(2024, 1, 1, 0, 7, 0))  # current time is 7 minutes
        file_cs_prov.end_time = pd.Timestamp(datetime(2024, 1, 1, 0, 10, 0))
        file_cs_prov.config.general_config = {"window": 5, "lag": 2, "max_cpu_limit": 14}
        recorded_data = pd.DataFrame(
            [
                {"time": pd.Timestamp(datetime(2024, 1, 1, 0, 2, 0)), "cpu": 3.0},  # should be in window
                {"time": pd.Timestamp(datetime(2024, 1, 1, 0, 3, 0)), "cpu": 4.0},  # should be in window
                {"time": pd.Timestamp(datetime(2024, 1, 1, 0, 4, 0)), "cpu": 5.0},  # should be in window
                {"time": pd.Timestamp(datetime(2024, 1, 1, 0, 4, 30)), "cpu": 6.1},  # should be in window
                {"time": pd.Timestamp(datetime(2024, 1, 1, 0, 5, 0)), "cpu": 6.0},  # should be in window
                {"time": pd.Timestamp(datetime(2024, 1, 1, 0, 6, 0)), "cpu": 7.0},  # should be in window.
                {"time": pd.Timestamp(datetime(2024, 1, 1, 0, 6, 0)), "cpu": 7.0},  # duplicate should be dropped.
                {"time": pd.Timestamp(datetime(2024, 1, 1, 0, 7, 0)), "cpu": 8.0},  # CURRENT TIME.
            ]
        )
        # recorded_data.set_index('timestamp', inplace=True)

        # for the file_cs_prov, we need to mock out get_current_cpu_limit
        # we want it to be 14.0. Now we mock it:
        with patch.object(FileClusterStateProvider, "get_current_cpu_limit", return_value=14.0):
            # and patch read_metrics_data to return the data we want as shown above
            with patch.object(FileClusterStateProvider, "read_metrics_data", return_value=recorded_data):
                # Call the method
                recorded_data, _end_time = file_cs_prov.get_next_recorded_data()

        # Verify the result
        expected_result = pd.DataFrame(
            [
                {"cpu": 3.0},
                {"cpu": 4.0},
                {"cpu": 5.0},
                {"cpu": 6.1},
                {"cpu": 6.0},
                {"cpu": 7.0},
                {"cpu": 8.0},
            ]
        )

        self.assertEqual(recorded_data["cpu"].values.tolist(), expected_result["cpu"].values.tolist())

    def test_too_small_data(self):

        # Here we'll work with the too small data.  We were hitting a bug where there is at
        # least one data point in the window, but not enough data points to make a prediction.
        # This is a regression test for that bug.

        runner = InMemoryRunnerSimulator(self.target_dir_toosmall, initial_cpu_limit=14, algorithm="additive")
        cfg = runner.run_simulation()

        self.assertEqual(cfg, {})

    def tearDown(self):
        shutil.rmtree(self.target_dir_sim, ignore_errors=True)
        shutil.rmtree(self.target_dir, ignore_errors=True)
        shutil.rmtree(self.target_dir_toosmall, ignore_errors=True)
        shutil.rmtree(self.target_dir_sim_toosmall, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
