#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#
import json
import unittest
from unittest.mock import mock_open, patch

from vasim.recommender.cluster_state_provider.ClusterStateConfig import (
    ClusterStateConfig,
)
from vasim.recommender.cluster_state_provider.ConfigStateConstants import (
    DEFAULT_LAG,
    DEFAULT_MAX_CPU_LIMIT,
    DEFAULT_MIN_CPU_LIMIT,
    DEFAULT_WINDOW,
    RECOVERY_TIME,
)


class TestClusterStateConfig(unittest.TestCase):
    def setUp(self):
        self.config_data = {
            "general_config": {"window": 20},
            "algo_specific_config": {"addend": 2},
            "prediction_config": {"enabled": True, "frequency_minutes": 5, "model": "naive"},
        }

        self.config = ClusterStateConfig(config_dict=self.config_data)

    def test_init_with_config_dict(self):
        # Test that the values are correctly assigned
        self.assertEqual(self.config.general_config["window"], 20)
        self.assertEqual(self.config.algo_specific_config["addend"], 2)
        self.assertEqual(self.config.prediction_config["frequency_minutes"], 5)

    def test_load_from_json(self):
        json_data = json.dumps(self.config_data)

        with patch("builtins.open", mock_open(read_data=json_data)):
            config = ClusterStateConfig(filename="dummy.json")

        # Test that the JSON data was loaded correctly
        self.assertEqual(config.general_config["window"], 20)
        self.assertEqual(config.algo_specific_config["addend"], 2)
        self.assertEqual(config.prediction_config["frequency_minutes"], 5)

    def test_load_config_file_not_exist(self):
        # Path to a file that doesn't exist
        data_path = "non_existent_file.json"

        # Assert that the exception is raised when file does not exist
        with self.assertRaises(FileNotFoundError):
            ClusterStateConfig(filename=data_path)

    def test_to_json_no_prediction(self):
        config = ClusterStateConfig({"general_config": {"window": 20}, "algo_specific_config": {"addend": 2}})

        # Expected dictionary structure with subsections
        expected_dict = {
            "general_config": {"window": 20, "lag": 15, "max_cpu_limit": 20, "min_cpu_limit": 1, "recovery_time": 15},
            "algo_specific_config": {"addend": 2},
            "prediction_config": {"enabled": False},
        }

        # Mock 'open' and 'json.dump'
        with patch("builtins.open", mock_open()) as mocked_file:
            with patch("json.dump") as mock_json_dump:
                config.to_json("output.json")

                # Check that 'open' was called with the correct filepath and mode
                mocked_file.assert_called_once_with("output.json", "w", encoding="utf-8")

                # Ensure that 'json.dump' was called with the correct dictionary and file handle
                mock_json_dump.assert_called_once_with(expected_dict, mocked_file(), indent=4)

    def test_to_json(self):
        # Expected dictionary structure with subsections
        expected_dict = {
            "general_config": {"window": 20, "lag": 15, "max_cpu_limit": 20, "min_cpu_limit": 1, "recovery_time": 15},
            "algo_specific_config": {"addend": 2},
            "prediction_config": {
                "waiting_before_predict": 1440,
                "frequency_minutes": 5,
                "forecasting_models": "naive",
                "minutes_to_predict": 10,
                "total_predictive_window": 60,
                "model": "naive",
                "enabled": True,
            },
        }

        # Mock 'open' and 'json.dump'
        with patch("builtins.open", mock_open()) as mocked_file:
            with patch("json.dump") as mock_json_dump:
                self.config.to_json("output.json")

                # Check that 'open' was called with the correct filepath and mode
                mocked_file.assert_called_once_with("output.json", "w", encoding="utf-8")

                # Ensure that 'json.dump' was called with the correct dictionary and file handle
                mock_json_dump.assert_called_once_with(expected_dict, mocked_file(), indent=4)

    def test_setattr(self):
        config = ClusterStateConfig()
        config.general_config["window"] = 10
        config.algo_specific_config["addend"] = 5

        # Check if attributes are set and accessible
        self.assertEqual(config.general_config["window"], 10)
        self.assertEqual(config.general_config["recovery_time"], RECOVERY_TIME)
        self.assertEqual(config.algo_specific_config["addend"], 5)

    def test_load_from_dict(self):

        self.config._load_from_dict(self.config_data)  # pylint: disable=protected-access

        # Ensure dictionary values are loaded properly
        self.assertEqual(self.config.general_config["window"], 20)
        self.assertEqual(self.config.prediction_config["model"], "naive")

    def test_empty_initialization(self):
        # Initialize config without any input
        config = ClusterStateConfig()

        # Ensure default values are set for general_config
        self.assertEqual(config.general_config["window"], DEFAULT_WINDOW)
        self.assertEqual(config.general_config["lag"], DEFAULT_LAG)
        self.assertEqual(config.general_config["max_cpu_limit"], DEFAULT_MAX_CPU_LIMIT)
        self.assertEqual(config.general_config["min_cpu_limit"], DEFAULT_MIN_CPU_LIMIT)
        self.assertEqual(config.general_config["recovery_time"], RECOVERY_TIME)

        # Ensure algo_specific_config and prediction_config are still empty
        # (since defaults were not provided for these in your current code)
        self.assertEqual(config.algo_specific_config, {})
        self.assertEqual(config.prediction_config, {"enabled": False})

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

        # Simulate an OSError when trying to write to a file
        with patch("builtins.open", mock_open()) as mocked_file:
            mocked_file.side_effect = OSError("File write error")

            # Capture logs at the ERROR level
            with self.assertLogs("root", level="ERROR") as log:
                with self.assertRaises(OSError):  # Expecting OSError to be raised
                    config.to_json("dummy.json")

            # Ensure the error message was logged
            self.assertIn("File error while writing JSON file", log.output[0])

    def test_min_cpu_greater_than_max_cpu(self):
        # Create the config instance with mocked config data
        config = ClusterStateConfig(
            config_dict={
                "general_config": {
                    "window": 20,
                    "lag": 10,
                    "max_cpu_limit": 2,  # Set this lower
                    "min_cpu_limit": 5,  # Set this higher to trigger the condition
                    "recovery_time": 15,
                },
                "prediction_config": {"enabled": False},
            }
        )

        # Call the method that we're testing
        config.validate_config()
        # Check that min_cpu_limit and max_cpu_limit were set to default values
        self.assertEqual(config.general_config["min_cpu_limit"], config.defaults["general_config"]["min_cpu_limit"])
        self.assertEqual(config.general_config["max_cpu_limit"], config.defaults["general_config"]["max_cpu_limit"])

    def test_min_cpu_less_than_or_equal_to_max_cpu(self):
        # Modify the config so min_cpu_limit is less than or equal to max_cpu_limit
        self.config_data["general_config"]["min_cpu_limit"] = 2
        self.config_data["general_config"]["max_cpu_limit"] = 4

        # Create the config instance with the modified config data
        config = ClusterStateConfig(config_dict=self.config_data)
        # Call the method that we're testing
        config.validate_config()

        # Ensure the min_cpu_limit and max_cpu_limit remain unchanged
        self.assertEqual(config.general_config["min_cpu_limit"], 2)
        self.assertEqual(config.general_config["max_cpu_limit"], 4)

        # Test __getitem__ for valid keys

    def test_getitem_valid_keys(self):
        # Test for general_config key

        self.assertEqual(self.config["general_config"], self.config_data["general_config"])
        # Test for algo_specific_config key
        self.assertEqual(self.config["algo_specific_config"], self.config_data["algo_specific_config"])
        # Test for prediction_config key
        self.assertEqual(self.config["prediction_config"], self.config_data["prediction_config"])

    # Test __getitem__ for an invalid key
    def test_getitem_invalid_key(self):
        with self.assertRaises(KeyError):
            self.config["invalid_key"]  # This should raise a KeyError

    # Test __setitem__ for valid keys
    def test_setitem_valid_keys(self):
        # Set a new value for general_config
        new_general_config = {"window": 15, "lag": 8}
        config = ClusterStateConfig(config_dict=self.config_data)
        config["general_config"] = new_general_config
        self.assertEqual(config["general_config"], new_general_config)

        # Set a new value for algo_specific_config
        new_algo_specific_config = {"addend": 5}
        config["algo_specific_config"] = new_algo_specific_config
        self.assertEqual(config["algo_specific_config"], new_algo_specific_config)

        # Set a new value for prediction_config
        new_prediction_config = {"enabled": True}
        config["prediction_config"] = new_prediction_config
        self.assertEqual(config["prediction_config"], new_prediction_config)

    # Test __setitem__ for an invalid key
    def test_setitem_invalid_key(self):
        with self.assertRaises(KeyError):
            self.config["invalid_key"] = {"some_key": "some_value"}  # This should raise a KeyError

    # Test get method for valid keys
    def test_get_valid_keys(self):
        self.assertEqual(self.config.get("general_config"), self.config_data["general_config"])
        self.assertEqual(self.config.get("algo_specific_config"), self.config_data["algo_specific_config"])
        self.assertEqual(self.config.get("prediction_config"), self.config_data["prediction_config"])

    # Test get method with an invalid key and a default value
    def test_get_invalid_key_with_default(self):
        self.assertEqual(self.config.get("invalid_key", "default_value"), "default_value")

    # Test get method with an invalid key without providing a default (should return None)
    def test_get_invalid_key_without_default(self):
        self.assertIsNone(self.config.get("invalid_key"))


if __name__ == "__main__":
    unittest.main()
