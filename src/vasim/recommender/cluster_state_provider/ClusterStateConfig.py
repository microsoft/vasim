#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#
import json
import logging


class ClusterStateConfig(dict):  # Inheriting from dict
    def __init__(self, config_dict=None, filename=None, is_predictive=True):
        super().__init__()  # Initialize the dictionary part of the object
        self.algo_specific_config = {}
        self.general_config = {}
        self.prediction_config = {}

        if config_dict:
            self.load_from_dict(config_dict)
        elif filename:
            self.load_from_json(filename)

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
            return self.__getitem__(key)
        except KeyError:
            return default

    def load_from_dict(self, config_dict):
        # Load the config sections from a dictionary
        self.general_config = config_dict.get("general_config", {})
        self.algo_specific_config = config_dict.get("algo_specific_config", {})
        self.prediction_config = config_dict.get("prediction_config", {})

    def load_from_json(self, filename):
        # Load the configuration from a JSON file
        with open(filename, "r") as f:
            data = json.load(f)
            self.load_from_dict(data)

    def to_json(self, filepath):
        try:
            with open(filepath, "w") as f:
                full_dict = {
                    "general_config": self.general_config,
                    "algo_specific_config": self.algo_specific_config,
                    "prediction_config": self.prediction_config,
                }
                json.dump(full_dict, f, indent=4)
        except Exception as e:
            logging.error(f"Error writing JSON file: {e}")
            raise
