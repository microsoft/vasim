#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#
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
