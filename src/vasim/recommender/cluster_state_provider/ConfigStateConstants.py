#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#

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
