#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#
import warnings

import numpy as np
from sktime.forecasting.compose import MultiplexForecaster
from sktime.forecasting.model_selection import SlidingWindowSplitter
from sktime.forecasting.naive import NaiveForecaster

from recommender.forecasting.models.oracle import Oracle


class TimeSeriesForecaster:
    def __init__(self, data_dir=None, sp=24 * 60 * 2, selected_forecaster=["naive"]):
        self.window_splitter = 0.7
        self.sp = sp
        self.selected_forecaster = selected_forecaster
        self.forecaster = None
        self.forecaster_param_grid = None
        self.cv = SlidingWindowSplitter(window_length=1, fh=[0])
        self.data_dir = data_dir
        self.set_forecaster(selected_forecaster)

    def set_forecaster(self, selected_forecaster):
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

    def get_prediction(self, data, number_of_points_to_predict):
        y_pred = self._forecast(data, number_of_points_to_predict)
        # make y_pred a dataframe with time and cpu columns
        y_pred['time'] = y_pred.index
        y_pred = y_pred.rename(columns={0: "cpu"})
        y_pred = y_pred.reset_index(drop=True)
        return y_pred

    def _forecast(self, data, number_of_points_to_predict):
        fh_abs = np.arange(1, number_of_points_to_predict + 1)
        self.cv = SlidingWindowSplitter(window_length=int(len(data) * self.window_splitter), fh=fh_abs)
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        warnings.filterwarnings("ignore", category=FutureWarning)
        forecaster = self.forecaster
        forecaster.fit(data)
        if self.selected_forecaster == ["oracle"]:
            y_pred = forecaster.predict(data, number_of_points_to_predict)
        else:
            y_pred = forecaster.predict(fh_abs)
        return y_pred
