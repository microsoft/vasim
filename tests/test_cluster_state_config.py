#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#
import json
import os
import unittest
from pathlib import Path
from unittest.mock import mock_open, patch

from vasim.recommender.cluster_state_provider.ClusterStateConfig import (
    ClusterStateConfig,
)


class TestClusterStateConfig(unittest.TestCase):

    def setUp(self):
        self.config_data = {
            "general_config": {"window": 20},
            "algo_specific_config": {"addend": 2},
            "prediction_config": {"frequency_minutes": 5, "model": "naive"},
        }

    def test_init_with_config_dict(self):
        config_dict = self.config_data
        config = ClusterStateConfig(config_dict=config_dict)

        # Test that the values are correctly assigned
        self.assertEqual(config.general_config["window"], 20)
        self.assertEqual(config.algo_specific_config["addend"], 2)
        self.assertEqual(config.prediction_config["frequency_minutes"], 5)

    def test_load_from_json(self):
        json_data = json.dumps(self.config_data)

        with patch("builtins.open", mock_open(read_data=json_data)):
            config = ClusterStateConfig(filename="dummy.json")

        # Test that the JSON data was loaded correctly
        self.assertEqual(config.general_config["window"], 20)
        self.assertEqual(config.algo_specific_config["addend"], 2)
        self.assertEqual(config.prediction_config["frequency_minutes"], 5)

    def test_to_json(self):
        config = ClusterStateConfig(self.config_data)

        # Expected dictionary structure with subsections
        expected_dict = self.config_data

        # Mock 'open' and 'json.dump'
        with patch("builtins.open", mock_open()) as mocked_file:
            with patch("json.dump") as mock_json_dump:
                config.to_json("output.json")

                # Check that 'open' was called with the correct filepath and mode
                mocked_file.assert_called_once_with("output.json", "w")

                # Ensure that 'json.dump' was called with the correct dictionary and file handle
                mock_json_dump.assert_called_once_with(expected_dict, mocked_file(), indent=4)

    def test_setattr(self):
        config = ClusterStateConfig()
        config.general_config["window"] = 10
        config.algo_specific_config["addend"] = 5

        # Check if attributes are set and accessible
        self.assertEqual(config.general_config["window"], 10)
        self.assertEqual(config.algo_specific_config["addend"], 5)

    def test_load_from_dict(self):
        config_dict = self.config_data
        config = ClusterStateConfig()
        config.load_from_dict(config_dict)

        # Ensure dictionary values are loaded properly
        self.assertEqual(config.general_config["window"], 20)
        self.assertEqual(config.prediction_config["model"], "naive")

    def test_empty_initialization(self):
        config = ClusterStateConfig()

        # Ensure default sections are initialized as empty dictionaries
        self.assertEqual(config.general_config, {})
        self.assertEqual(config.algo_specific_config, {})
        self.assertEqual(config.prediction_config, {})

    def test_load_config_from_file(self):
        # Path to the test JSON file
        data_path = "tests/test_data/alibaba_control_c_29247_denom_1/metadata.json"

        # Initialize the config from the JSON file
        config = ClusterStateConfig(filename=data_path)

        # Test the general configuration values
        self.assertEqual(config.general_config["window"], 20)
        self.assertEqual(config.general_config["lag"], 10)

        # Test the algorithm-specific configuration
        self.assertEqual(config.algo_specific_config["addend"], 2)
        self.assertEqual(config.algo_specific_config["multiplier"], 2)

        # Test prediction configuration
        self.assertEqual(config.prediction_config["waiting_before_predict"], 1440)
        self.assertEqual(config.prediction_config["forecasting_models"], "naive")

    def test_exception_in_to_json(self):
        config = ClusterStateConfig(config_dict=self.config_data)

        # Simulate an error when trying to write to a file
        with patch("builtins.open", mock_open()) as mocked_file:
            mocked_file.side_effect = Exception("File write error")

            # Capture logs at the ERROR level
            with self.assertLogs("root", level="ERROR") as log:
                try:
                    config.to_json("dummy.json")
                except Exception:
                    pass  # Exception is expected, so we suppress it here

            # Ensure the error message was logged
            self.assertIn("Error writing JSON file", log.output[0])


if __name__ == "__main__":
    unittest.main()
