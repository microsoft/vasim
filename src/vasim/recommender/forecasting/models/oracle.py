#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#
import os
import pandas as pd
from datetime import datetime, timedelta


class Oracle:
    def __init__(self, data_dir):
        dfs = []
        for file_name in os.listdir(data_dir):
            if file_name.endswith('.csv'):
                # Construct the full file path
                file_path = os.path.join(data_dir, file_name)

                # Load the CSV file into a pandas DataFrame
                df = pd.read_csv(file_path)
                # Append the DataFrame to the list
                dfs.append(df)
        # Concatenate all DataFrames into a single DataFrame
        temp_data = pd.concat(dfs, ignore_index=True)
        temp_data["cpu"] = temp_data["CPU_USAGE_ACTUAL"]
        temp_data["time"] = temp_data["TIMESTAMP"].apply(
            lambda x: datetime.strptime(x, "%Y.%m.%d-%H:%M:%S:%f"))
        temp_data = temp_data.sort_values("time", ascending=True)
        self.all_performance_data = temp_data

    def fit(self, data):
        pass

    def predict(self, data, number_of_points_to_predict):
        temp_data = self.all_performance_data
        latest_timestamp = data.index.max()

        # Get the 120 data points immediately after the latest timestamp from df2
        data_after_latest = temp_data[temp_data['time'] > latest_timestamp].head(number_of_points_to_predict)
        data_after_latest = data_after_latest[['time', 'cpu']]

        data_after_latest['timeindex'] = data_after_latest['time']
        data_after_latest.set_index('timeindex', inplace=True)
        return data_after_latest
