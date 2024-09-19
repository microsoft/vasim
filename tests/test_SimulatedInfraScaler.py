#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#
import json
import os
import shutil
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from vasim.simulator.InMemorySimulator import InMemoryRunnerSimulator
from vasim.simulator.SimulatedInfraScaler import SimulatedInfraScaler


class TestSimulatedInfraScaler(unittest.TestCase):
    """
    TODO: This file was mostly generated by AI.

    But it's important to write unit tests for the SimulatedInfraScaler
    class. This class is responsible for simulating the scaling of the infrastructure.

    It is important to test that the scaling is done correctly, and that the recovery time is respected.

    We need to fill in and fix the rest of the tests in this file.
    """

    def setUp(self):

        # For this test we'll use the "mini" dataset, which is a smaller version of the full dataset
        root_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        self.source_dir = root_dir / "test_data/alibaba_control_c_29247_denom_1_mini"
        # Here we'll copy the source directory to a target directory, so we can modify the target directory without
        # affecting the source directory
        # Use a unique directory for each worker when using xdist to parallelize tests.
        uid = os.environ.get("PYTEST_XDIST_WORKER", "")
        self.target_dir = root_dir / f"test_data/tmp/{uid}/alibaba_control_c_29247_denom_1_test_to_delete_mini"
        self.target_dir_sim = root_dir / f"test_data/tmp/{uid}/alibaba_control_c_29247_denom_1_test_to_delete_mini_simulations"
        shutil.rmtree(self.target_dir, ignore_errors=True)
        shutil.copytree(self.source_dir, self.target_dir)

        self.start_timestamp = datetime.now()

        # Open the config path of f"{self.target_dir}/metadata_alt_config.json" and make sure that
        #     we have the right file with the recovery time of 5.
        # TODO: we need to document that the recovery time is the time it takes for the infrastructure to recover after
        # and clarify how it's different from the lag parameter.
        with open(f"{self.target_dir}/metadata_alt_config.json") as f:
            config = json.load(f)
            self.assertEqual(config["general_config"]["recovery_time"], 5)

        self.runner = InMemoryRunnerSimulator(
            self.target_dir,
            initial_cpu_limit=14,
            algorithm="multiplicative",
            config_path=f"{self.target_dir}/metadata_alt_config.json",
        )

        # now assert that the config is the same as the one we loaded
        self.assertEqual(self.runner.config.general_config["recovery_time"], 5)
        self.assertEqual(self.runner.infra_scaler.recovery_time, 5)

        # set things locally for easier access
        self.cluster_state_provider = self.runner.cluster_state_provider
        self.scaler = self.runner.infra_scaler
        self.recovery_time = self.runner.infra_scaler.recovery_time

    def test_scale_should_scale_cluster_when_recovery_time_has_passed(self):
        # Arrange
        new_limit = 10
        current_limit = 5
        time_now = self.start_timestamp + timedelta(minutes=self.recovery_time + 1)
        self.cluster_state_provider.curr_cpu_limit = current_limit

        # Act. Scale should return true because the recovery time has passed and
        #      the new limit is different from the current limit
        result = self.scaler.scale(new_limit, time_now)

        # Assert
        self.assertTrue(result)
        self.assertEqual(self.scaler.last_scaling_time, time_now)
        self.assertEqual(self.cluster_state_provider.get_current_cpu_limit(), new_limit)

    def test_scale_should_not_scale_cluster_when_recovery_time_has_not_passed(self):
        # Arrange
        new_limit = 10
        current_limit = 5
        self.scaler.last_scaling_time = self.start_timestamp + timedelta(minutes=self.recovery_time - 1)
        time_now = self.start_timestamp + timedelta(minutes=self.recovery_time - 1)
        self.cluster_state_provider.set_cpu_limit(current_limit)

        # Act. Scale should return false because the recovery time has not passed
        result = self.scaler.scale(new_limit, time_now)

        # Assert
        self.assertFalse(result)
        self.assertEqual(self.cluster_state_provider.get_current_cpu_limit(), current_limit)

    # TODO: Help wanted, fix these up. They were AI generated so there is some cleanup needed.
    # def test_scale_should_not_scale_cluster_when_new_limit_is_below_min_cpu_limit(self):
    #     # Arrange
    #     new_limit = 3
    #     time_now = self.start_timestamp + timedelta(minutes=self.recovery_time + 1)
    #     self.cluster_state_provider.get_current_cpu_limit.return_value = 5
    #     self.cluster_state_provider.config.min_cpu_limit = 4

    #     # Act
    #     result = self.scaler.scale(new_limit, time_now)

    #     # Assert
    #     self.assertFalse(result)
    #     self.cluster_state_provider.set_cpu_limit.assert_called_once_with(self.cluster_state_provider.min_cpu_limit)
    #     self.assertIsNone(self.scaler.last_scaling_time)

    # def test_scale_should_not_scale_cluster_when_new_limit_is_above_max_cpu_limit(self):
    #     # Arrange
    #     new_limit = 20
    #     time_now = self.start_timestamp + timedelta(minutes=self.recovery_time + 1)
    #     self.cluster_state_provider.get_current_cpu_limit.return_value = 5
    #     self.cluster_state_provider.config.max_cpu_limit = 15

    #     # Act
    #     result = self.scaler.scale(new_limit, time_now)

    #     # Assert
    #     self.assertFalse(result)
    #     self.cluster_state_provider.set_cpu_limit.assert_called_once_with(self.cluster_state_provider.max_cpu_limit)
    #     self.assertIsNone(self.scaler.last_scaling_time)

    # def test_scale_should_not_scale_cluster_when_new_limit_is_same_as_current_cpu_limit(self):
    #     # Arrange
    #     new_limit = 5
    #     time_now = self.start_timestamp + timedelta(minutes=self.recovery_time + 1)
    #     self.cluster_state_provider.get_current_cpu_limit.return_value = 5

    #     # Act
    #     result = self.scaler.scale(new_limit, time_now)

    #     # Assert
    #     self.assertFalse(result)
    #     self.cluster_state_provider.set_cpu_limit.assert_not_called()
    #     self.assertIsNone(self.scaler.last_scaling_time)

    def tearDown(self):
        shutil.rmtree(self.target_dir_sim, ignore_errors=True)
        shutil.rmtree(self.target_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
