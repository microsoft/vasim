#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#
from abc import abstractmethod

import pandas as pd


class ClusterStateProvider:

    def __init__(self, data_dir=None, features=None, window=None, decision_file_path=None, lag=None):
        # pylint: disable=too-many-arguments
        # TODO: How did we chose to include lag and window, but not the rest? I think make them all kwargs
        pass

    @abstractmethod
    def get_next_recorded_data(self):
        pass

    @abstractmethod
    def get_current_cpu_limit(self):
        pass

    @abstractmethod
    def get_total_cpu(self):
        pass

    def prediction_activated(self, data=None):
        # pylint: disable=unused-argument
        # pylint: disable=no-self-use
        return False

    @abstractmethod
    def process_data(self, data=None):
        pass

    @staticmethod
    def drop_duplicates(recorded_data: pd.DataFrame):
        recorded_data = recorded_data.drop_duplicates()
        return recorded_data

    @staticmethod
    def sort_data(recorded_data: pd.DataFrame):
        recorded_data = recorded_data.assign(time=pd.to_datetime(recorded_data["time"]))
        recorded_data = recorded_data.sort_values(by="time")
        return recorded_data
