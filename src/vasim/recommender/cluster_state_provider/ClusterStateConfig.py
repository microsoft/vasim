#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#
"""
Module that defines a configuration management class for managing cluster state configurations.

used by the autoscaling recommender. It allows loading configuration from a dictionary or a
JSON file, validation of the configuration, and saving it back to a file in JSON format.

Classes:
    ClusterStateConfig: Handles loading, saving, and validation of cluster state configurations.
"""

import json
import logging

from vasim.recommender.cluster_state_provider.ConfigStateConstants import (
    DEFAULT_FORECASTING_MODEL,
    DEFAULT_FREQUENCY_MINUTES,
    DEFAULT_LAG,
    DEFAULT_MAX_CPU_LIMIT,
    DEFAULT_MIN_CPU_LIMIT,
    DEFAULT_MINUTES_TO_PREDICT,
    DEFAULT_TOTAL_PREDICTIVE_WINDOW,
    DEFAULT_WAITING_BEFORE_PREDICT,
    DEFAULT_WINDOW,
    RECOVERY_TIME,
)

# Set up logging
logging.basicConfig(level=logging.INFO)  # You can adjust the logging level as needed


class ClusterStateConfig(dict):
    """
    A class that manages the cluster state configuration used for autoscaling recommendations.

    Attributes:
        algo_specific_config (dict): A dictionary for algorithm-specific configuration settings.
        general_config (dict): A dictionary for general configuration settings like CPU limits and recovery time.
        prediction_config (dict): A dictionary for prediction-related configuration settings like forecasting models and prediction windows.
        defaults (dict): Contains default configuration values for general, algorithm-specific, and prediction settings.

    Methods:
        __getitem__(key): Allows access to configuration sections using dictionary-like keys.
        __setitem__(key, value): Allows setting values in configuration sections using dictionary-like keys.
        get(key, default=None): Retrieves a value by key, returning a default if not found.
        _load_from_dict(config_dict): Merges user-provided configuration with default values.
        _load_from_json(filename): Loads configuration from a JSON file.
        to_json(filepath): Saves the current configuration to a JSON file.
        validate_config(): Validates required config values, ensuring they are present and within valid ranges.
        _check_positive_integer(key, value): Checks if a configuration value is a positive integer.
    """

    def __init__(self, config_dict=None, filename=None):
        """
        Initialize the ClusterStateConfig object.

        Args:
            config_dict (dict, optional): A dictionary containing the configuration values.
            filename (str, optional): The path to the JSON file containing the configuration values.

        Raises:
            KeyError: If invalid keys are provided in the configuration.
        """
        super().__init__()  # Initialize the dictionary part of the object
        self.algo_specific_config = {}
        self.general_config = {}
        self.prediction_config = {}

        self.defaults = {
            "general_config": {
                "window": DEFAULT_WINDOW,
                "lag": DEFAULT_LAG,
                "max_cpu_limit": DEFAULT_MAX_CPU_LIMIT,
                "min_cpu_limit": DEFAULT_MIN_CPU_LIMIT,
                "recovery_time": RECOVERY_TIME,
            },
            "prediction_config": {
                "enabled": False,
                "waiting_before_predict": DEFAULT_WAITING_BEFORE_PREDICT,
                "frequency_minutes": DEFAULT_FREQUENCY_MINUTES,
                "forecasting_models": DEFAULT_FORECASTING_MODEL,
                "minutes_to_predict": DEFAULT_MINUTES_TO_PREDICT,
                "total_predictive_window": DEFAULT_TOTAL_PREDICTIVE_WINDOW,
            },
        }

        if config_dict:
            self._load_from_dict(config_dict)
        elif filename:
            self._load_from_json(filename)

        self.validate_config()

    def __getitem__(self, key):
        """
        Retrieve a configuration section using dictionary-like keys.

        Args:
            key (str): The key representing the configuration section (e.g., 'general_config').

        Returns:
            dict: The corresponding configuration section.

        Raises:
            KeyError: If an invalid key is provided.
        """
        if key == "general_config":
            return self.general_config
        elif key == "algo_specific_config":
            return self.algo_specific_config
        elif key == "prediction_config":
            return self.prediction_config
        else:
            raise KeyError(f"Invalid key: {key}")

    def __setitem__(self, key, value):
        """
        Set a value for a configuration section using dictionary-like keys.

        Args:
            key (str): The key representing the configuration section (e.g., 'general_config').
            value (dict): The value to assign to the configuration section.

        Raises:
            KeyError: If an invalid key is provided.
        """
        if key == "general_config":
            self.general_config = value
        elif key == "algo_specific_config":
            self.algo_specific_config = value
        elif key == "prediction_config":
            self.prediction_config = value
        else:
            raise KeyError(f"Invalid key: {key}")

    def get(self, key, default=None):
        """
        Retrieve a configuration value by key, or return a default if not found.

        Args:
            key (str): The key representing the configuration section or value.
            default: The value to return if the key is not found. Defaults to None.

        Returns:
            The value corresponding to the key, or the default value if the key is not found.
        """
        try:
            return self[key]
        except KeyError:
            return default

    def _load_from_dict(self, config_dict):
        """
        Load the configuration from a provided dictionary and merge it with the default values.

        Args:
            config_dict (dict): A dictionary containing the configuration values.
        """
        self.general_config = config_dict.get("general_config", {})
        self.algo_specific_config = config_dict.get("algo_specific_config", {})
        self.prediction_config = config_dict.get("prediction_config", {})

    def _load_from_json(self, filename):
        """
        Load the configuration from a JSON file.

        Args:
            filename (str): The path to the JSON file.

        Raises:
            FileNotFoundError: If the specified JSON file is not found.
            json.JSONDecodeError: If there is an error in parsing the JSON file.
        """
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._load_from_dict(data)
        except FileNotFoundError as e:
            logging.error("Configuration file not found: %s", filename)
            raise e
        except json.JSONDecodeError as e:
            logging.error("Invalid JSON format in the configuration file: %s", filename)
            raise e

    def to_json(self, filepath):
        """
        Save the current configuration to a JSON file.

        Args:
            filepath (str): The path to the JSON file.

        Raises:
            OSError: If there is an error while writing to the file.
            json.JSONDecodeError: If there is an error in serializing the configuration to JSON.
        """
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                full_dict = {
                    "general_config": self.general_config,
                    "algo_specific_config": self.algo_specific_config,
                    "prediction_config": self.prediction_config,
                }
                json.dump(full_dict, f, indent=4)
        except (OSError, IOError) as file_error:
            logging.error("File error while writing JSON file: %s", filepath, exc_info=file_error)
            raise
        except (TypeError, ValueError, json.JSONDecodeError) as json_error:
            logging.error("JSON serialization error for file: %s", filepath, exc_info=json_error)
            raise

    def validate_config(self):
        """
        Validate the configuration values to ensure required keys are present and have valid values.

        This method checks both the general configuration and the prediction configuration (if enabled).
        It also performs sanity checks to ensure numeric values are within valid ranges.
        """
        general_required_keys = ["window", "lag", "max_cpu_limit", "min_cpu_limit", "recovery_time"]

        for key in general_required_keys:
            if key not in self.general_config:
                logging.warning(
                    "Missing key '%s' in general_config. Using default value: %s",
                    key,
                    self.defaults["general_config"][key],
                )
                self.general_config[key] = self.defaults["general_config"][key]

        if "enabled" in self.prediction_config and self.prediction_config["enabled"]:
            prediction_required_keys = [
                "waiting_before_predict",
                "frequency_minutes",
                "forecasting_models",
                "minutes_to_predict",
                "total_predictive_window",
            ]
            for key in prediction_required_keys:
                if key not in self.prediction_config:
                    logging.warning(
                        "Missing key '%s' in prediction_config. Using default value: '%s'",
                        key,
                        self.defaults["prediction_config"][key],
                    )
                    self.prediction_config[key] = self.defaults["prediction_config"][key]
        else:
            self.prediction_config["enabled"] = False

        # Sanity checks
        self._check_positive_integer("window", self.general_config["window"])
        self._check_positive_integer("lag", self.general_config["lag"])
        self._check_positive_integer("max_cpu_limit", self.general_config["max_cpu_limit"])
        self._check_positive_integer("min_cpu_limit", self.general_config["min_cpu_limit"])

        if self.general_config["min_cpu_limit"] > self.general_config["max_cpu_limit"]:
            logging.warning(
                "min_cpu_limit (%s) is greater than max_cpu_limit (%s). Using default limits.",
                self.general_config["min_cpu_limit"],
                self.general_config["max_cpu_limit"],
            )
            self.general_config["min_cpu_limit"] = self.defaults["general_config"]["min_cpu_limit"]
            self.general_config["max_cpu_limit"] = self.defaults["general_config"]["max_cpu_limit"]

    def _check_positive_integer(self, key, value):
        """
        Helper method to check if a configuration value is a positive integer.

        Args:
            key (str): The name of the configuration value being checked.
            value: The value to check.

        Logs a warning and uses the default value if the check fails.
        """
        if not isinstance(value, int) or value <= 0:
            logging.warning(
                "Invalid value for '%s': %s. Using default value: %s",
                key,
                value,
                self.defaults["general_config"][key],
            )
            self.general_config[key] = self.defaults["general_config"][key]
