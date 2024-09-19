#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#
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
    def __init__(self, config_dict=None, filename=None):
        super().__init__()  # Initialize the dictionary part of the object
        self.algo_specific_config = {}
        self.general_config = {}
        self.prediction_config = {}

        # Define default values for the configuration
        self.defaults = {
            "general_config": {
                "window": DEFAULT_WINDOW,  # Default window value
                "lag": DEFAULT_LAG,  # Default lag value
                "max_cpu_limit": DEFAULT_MAX_CPU_LIMIT,  # Default max CPU limit
                "min_cpu_limit": DEFAULT_MIN_CPU_LIMIT,  # Default min CPU limit
                "recovery_time": RECOVERY_TIME,  # Default time for system recovery between scalings.
            },
            "prediction_config": {
                "enabled": False,
                "waiting_before_predict": DEFAULT_WAITING_BEFORE_PREDICT,  # Default waiting time
                "frequency_minutes": DEFAULT_FREQUENCY_MINUTES,  # Default prediction frequency
                "forecasting_models": DEFAULT_FORECASTING_MODEL,  # Default forecasting model
                "minutes_to_predict": DEFAULT_MINUTES_TO_PREDICT,  # Default prediction window
                "total_predictive_window": DEFAULT_TOTAL_PREDICTIVE_WINDOW,  # Default predictive window
            },
        }

        if config_dict:
            self._load_from_dict(config_dict)
        elif filename:
            self._load_from_json(filename)

        # Perform validation after loading the config
        self.validate_config()

    def __getitem__(self, key):
        # Allow access to the configuration sections via dictionary-like keys
        if key == "general_config":
            return self.general_config
        elif key == "algo_specific_config":
            return self.algo_specific_config
        elif key == "prediction_config":
            return self.prediction_config
        else:
            raise KeyError(f"Invalid key: {key}")

    def __setitem__(self, key, value):
        # Allow setting values for the configuration sections via dictionary-like keys
        if key == "general_config":
            self.general_config = value
        elif key == "algo_specific_config":
            self.algo_specific_config = value
        elif key == "prediction_config":
            self.prediction_config = value
        else:
            raise KeyError(f"Invalid key: {key}")

    def get(self, key, default=None):
        # Implement the get method to access sections like a dictionary
        try:
            return self[key]
        except KeyError:
            return default

    def _load_from_dict(self, config_dict):
        # Merge user-provided config with default config
        self.general_config = config_dict.get("general_config", {})
        self.algo_specific_config = config_dict.get("algo_specific_config", {})
        self.prediction_config = config_dict.get("prediction_config", {})

    def _load_from_json(self, filename):
        # Load the configuration from a JSON file
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            self._load_from_dict(data)

    def to_json(self, filepath):
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                full_dict = {
                    "general_config": self.general_config,
                    "algo_specific_config": self.algo_specific_config,
                    "prediction_config": self.prediction_config,
                }
                json.dump(full_dict, f, indent=4)
        except Exception as e:  # pylint: disable=broad-exception-caught  # FIXME
            logging.error("Error writing JSON file: %s", filepath, exc_info=e)
            raise

    def validate_config(self):
        """
        Validate the config values in general_config to ensure that.

        required keys (e.g., 'window', 'lag') are present and valid.
        Perform sanity checks on ranges and types.
        """
        # Required keys from general section
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
            # Required keys from prediction section
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

        # Ensure that min_cpu_limit is less than or equal to max_cpu_limit
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
        Helper method to check if a value is a positive integer.

        Logs and uses the default value if the check fails.
        """
        if not isinstance(value, int) or value <= 0:
            logging.warning(
                "Invalid value for '%s': %s. Using default value: %s",
                key,
                value,
                self.defaults["general_config"][key],
            )
            self.general_config[key] = self.defaults["general_config"][key]
