#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#

"""
Module Name: ClusterStateProvider.

Description:
    This module defines an abstract base class `ClusterStateProvider` which serves as a
    blueprint for managing the state and data of a cluster. It provides methods for
    retrieving cluster data, CPU limits, and performing data processing tasks like
    dropping duplicates and sorting data by time.

Classes:
    ClusterStateProvider:
        An abstract base class that provides a framework for interacting with cluster
        data and performing various data operations. Subclasses are expected to implement
        the abstract methods `get_next_recorded_data`, `get_current_cpu_limit`,
        `get_total_cpu`, and `process_data`.

Methods:
    __init__(data_dir=None, features=None, window=None, decision_file_path=None, lag=None):
        Initializes the `ClusterStateProvider` with various parameters, with a note to
        possibly convert all arguments to keyword arguments for consistency.

    get_next_recorded_data():
        Abstract method to retrieve the next set of recorded data.

    get_current_cpu_limit():
        Abstract method to retrieve the current CPU limit of the cluster.

    get_total_cpu():
        Abstract method to retrieve the total CPU capacity of the cluster.

    prediction_activated(data=None):
        A method that returns False, indicating no prediction activation. This can be
        overridden in subclasses.

    process_data(data=None):
        Abstract method to process cluster data.

    drop_duplicates(recorded_data: pd.DataFrame):
        Static method that removes duplicate records from the recorded data.

    sort_data(recorded_data: pd.DataFrame):
        Static method that sorts recorded data by the 'time' column after converting it
        to a datetime format.
"""

from abc import abstractmethod
from typing import Optional

import pandas as pd


class ClusterStateProvider:

    def __init__(
        self,
        data_dir: Optional[str] = None,
        features=None,
        window=None,
        decision_file_path=None,
        lag=None,
    ) -> None:
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
    def drop_duplicates(recorded_data: pd.DataFrame) -> pd.DataFrame:
        recorded_data = recorded_data.drop_duplicates()
        return recorded_data

    @staticmethod
    def sort_data(recorded_data: pd.DataFrame) -> pd.DataFrame:
        recorded_data = recorded_data.assign(time=pd.to_datetime(recorded_data["time"]))
        recorded_data = recorded_data.sort_values(by="time")
        return recorded_data
