#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#

"""
Module Name: TimeSeriesForecaster.

Description:
    The `TimeSeriesForecaster` class is responsible for forecasting future data points in time series data using
    various forecasting models such as the NaiveForecaster or Oracle. The class supports forecasting through
    selected models and allows customization of seasonal periodicity and forecast horizons.

Classes:
    TimeSeriesForecaster:
        Provides methods for configuring and executing time series forecasts on performance data,
        using models like NaiveForecaster or Oracle.

Attributes:
    window_splitter (float): Proportion of data to use for training during forecasting (default 0.7).
    sp (int): Seasonal periodicity for time series forecasting (default to 24 * 60 * 2).
    selected_forecaster (list): List of forecasters to be used (default ["naive"]).
    forecaster (object): The forecaster object, which is set dynamically based on the selected forecaster.
    forecaster_param_grid (dict): Parameter grid for the forecaster.
    cv (SlidingWindowSplitter): Cross-validation splitter used for windowed predictions.
    data_dir (str): Directory containing the training data for the forecasting models.

Methods:
    __init__(data_dir=None, sp=24*60*2, selected_forecaster=None):
        Initializes the `TimeSeriesForecaster` with the given data directory, seasonal periodicity,
        and selected forecaster models.

    set_forecaster(selected_forecaster):
        Configures the forecaster object based on the provided list of selected forecasters.

    get_prediction(data, forecast_horizon):
        Generates the forecasted data points for the specified forecast horizon.

    _forecast(data, forecast_horizon):
        Performs the forecasting operation using the provided data and forecast horizon,
        returns the predicted data points.

Parameters:
    data_dir (str):
        The directory path containing the data for training the forecasting models.

    sp (int):
        The seasonal periodicity for the time series (default is 24 * 60 * 2).

    selected_forecaster (list):
        A list of forecasters to use for the prediction. Default is ["naive"].

    data (pd.DataFrame):
        Input data for prediction or forecasting, typically a DataFrame with time series data.

    forecast_horizon (int):
        The number of future data points to predict.

Returns:
    The `get_prediction` and `_forecast` methods return a `pd.DataFrame` containing the predicted
    data points with time and CPU columns.
"""
import warnings
from typing import List, Optional, Union

import numpy as np
from sktime.forecasting.compose import MultiplexForecaster
from sktime.forecasting.model_selection import SlidingWindowSplitter
from sktime.forecasting.naive import NaiveForecaster

from vasim.recommender.forecasting.models.oracle import Oracle


class TimeSeriesForecaster:
    """
    A class for forecasting time series data using various forecasting models.

    Attributes:
        window_splitter (float): Proportion of data to use for training.
        sp (int): Seasonal periodicity.
        selected_forecaster (list): List of selected forecasters.
        forecaster (object): The forecaster object.
        forecaster_param_grid (dict): Parameter grid for the forecaster.
        cv (SlidingWindowSplitter): Cross-validation splitter.
        data_dir (str): Directory containing training data.
    """

    def __init__(self, data_dir=None, sp=24 * 60 * 2, selected_forecaster: Optional[Union[str, List[str]]] = None):
        """
        Initializes the TimeSeriesForecaster with the specified parameters.

        Args:
            data_dir (str, optional): Directory containing the data. Defaults to None.
            sp (int, optional): Seasonal periodicity. Defaults to 24 * 60 * 2.
            selected_forecaster (list, optional): List of selected forecasters. Defaults to ["naive"].
        """
        if selected_forecaster is None:
            selected_forecaster = ["naive"]
        self.window_splitter = 0.7
        self.sp = sp
        self.selected_forecaster = selected_forecaster
        self.forecaster = None
        self.forecaster_param_grid = None
        self.cv = SlidingWindowSplitter(window_length=1, fh=[0])
        self.data_dir = data_dir
        self.set_forecaster(selected_forecaster)

    def set_forecaster(self, selected_forecaster):
        """
        Sets the forecaster based on the selected forecaster.

        Args:
            selected_forecaster (list): List of selected forecasters.
        """
        self.selected_forecaster = selected_forecaster
        # Select the forecaster based on the selected_forecaster string, it is one to one mapping
        if selected_forecaster == "naive":
            self.forecaster = NaiveForecaster(strategy="last", sp=self.sp)
        elif selected_forecaster == ["oracle"]:
            self.forecaster = Oracle(data_dir=self.data_dir)
        elif selected_forecaster == ["naive"]:
            self.forecaster = MultiplexForecaster(
                forecasters=[
                    ("naive", NaiveForecaster(strategy="last", sp=self.sp)),
                ]
            )
        self.forecaster_param_grid = {"selected_forecaster": [selected_forecaster]}

    def get_prediction(self, data, forecast_horizon):
        """
        Gets the prediction for the specified number of points.

        Args:
            data (pd.DataFrame): The input data for prediction.
            forecast_horizon (int): Number of future data points to predict.

        Returns:
            pd.DataFrame: DataFrame containing the predicted data points with time and cpu columns.
        """
        y_pred = self._forecast(data, forecast_horizon)
        # make y_pred a dataframe with time and cpu columns
        y_pred["time"] = y_pred.index
        y_pred = y_pred.rename(columns={0: "cpu"})
        y_pred = y_pred.reset_index(drop=True)
        return y_pred

    def _forecast(self, data, forecast_horizon):
        """
        Forecasts the future data points based on the provided data.

        Args:
            data (pd.DataFrame): The input data for forecasting.
            forecast_horizon (int): Number of future data points to predict.

        Returns:
            pd.DataFrame: DataFrame containing the forecasted data points.
        """
        fh_abs = np.arange(1, forecast_horizon + 1)
        self.cv = SlidingWindowSplitter(window_length=int(len(data) * self.window_splitter), fh=fh_abs)
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        warnings.filterwarnings("ignore", category=FutureWarning)
        forecaster = self.forecaster
        forecaster.fit(data)
        if self.selected_forecaster == ["oracle"]:
            y_pred = forecaster.predict(data, forecast_horizon)
        else:
            y_pred = forecaster.predict(fh_abs)
        return y_pred
