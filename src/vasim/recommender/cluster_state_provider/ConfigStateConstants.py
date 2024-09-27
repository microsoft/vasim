#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#

"""
Module Name: Config Defaults and Validation Ranges.

Description:
    This module defines general configuration defaults and validation ranges
    used for tuning various parameters in a predictive system, particularly
    for cluster resource management. It includes default settings for time
    windows, lag periods, CPU limits, and prediction configurations.

Variables:
    General Config Defaults:
        - DEFAULT_WINDOW (int): The default time window in minutes, set to 60.
        - DEFAULT_LAG (int): The default lag value, set to 15.
        - DEFAULT_MAX_CPU_LIMIT (int): Maximum allowed CPU limit, set to 20.
        - DEFAULT_MIN_CPU_LIMIT (int): Minimum allowed CPU limit, set to 1.
        - RECOVERY_TIME (int): Time for recovery after a change, set to 15 minutes.

    Prediction Config Defaults:
        - DEFAULT_WAITING_BEFORE_PREDICT (int): Default waiting time before predictions, set to 1440 minutes (1 day).
        - DEFAULT_FREQUENCY_MINUTES (int): Frequency in minutes for making predictions, set to 1.
        - DEFAULT_FORECASTING_MODEL (str): The default forecasting model, set to "naive".
        - DEFAULT_MINUTES_TO_PREDICT (int): Number of minutes ahead to predict, set to 10.
        - DEFAULT_TOTAL_PREDICTIVE_WINDOW (int): Total time window for predictions, set to 60 minutes.

    Validation Ranges:
        - WINDOW_MIN (int): Minimum allowed value for the time window, set to 5 minutes.
        - WINDOW_MAX (int): Maximum allowed value for the time window, set to 100 minutes.
        - LAG_MIN (int): Minimum allowed value for the lag period, set to 1.
        - LAG_MAX (int): Maximum allowed value for the lag period, set to 50.
        - CPU_LIMIT_MIN (int): Minimum allowed value for CPU limit, set to 1.
        - CPU_LIMIT_MAX (int): Maximum allowed value for CPU limit, set to 100.

    Config File Path:
        - DEFAULT_CONFIG_FILE (str): Default path to the configuration file, set to "config/metadata.json".
"""

# General Config Defaults
DEFAULT_WINDOW = 60  # minutes
DEFAULT_LAG = 15
DEFAULT_MAX_CPU_LIMIT = 20
DEFAULT_MIN_CPU_LIMIT = 1
RECOVERY_TIME = 15  # minutes

# Prediction Config Defaults
DEFAULT_WAITING_BEFORE_PREDICT = 1440
DEFAULT_FREQUENCY_MINUTES = 1
DEFAULT_FORECASTING_MODEL = "naive"
DEFAULT_MINUTES_TO_PREDICT = 10
DEFAULT_TOTAL_PREDICTIVE_WINDOW = 60

# Validation Ranges
WINDOW_MIN = 5
WINDOW_MAX = 100

LAG_MIN = 1
LAG_MAX = 50

CPU_LIMIT_MIN = 1
CPU_LIMIT_MAX = 100

DEFAULT_CONFIG_FILE = "config/metadata.json"
