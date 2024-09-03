import unittest
import os
import shutil
from datetime import datetime
from pathlib import Path
import pandas as pd
from simulator.SimulatedInMemoryPredictiveClusterStateProvider import SimulatedInMemoryPredictiveClusterStateProvider
from recommender.cluster_state_provider.ClusterStateConfig import ClusterStateConfig


class TestSimulatedInMemoryPredictiveClusterStateProvider(unittest.TestCase):
    def setUp(self):

        root_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        self.source_dir = root_dir / "test_data/alibaba_control_c_29247_denom_1_mini"
        # Here we'll copy the source directory to a target directory, so we can modify the target directory without
        # affecting the source directory
        self.target_dir = root_dir / "test_data/alibaba_control_c_29247_denom_1_test_to_delete_mini"
        # TODO: sometimes the output is 'simulations', sometimes it is 'tuning'. this is confusing.
        self.target_dir_sim = root_dir / "test_data/alibaba_control_c_29247_denom_1_test_to_delete_mini_simulations"
        shutil.rmtree(self.target_dir, ignore_errors=True)
        shutil.copytree(self.source_dir, self.target_dir)

        config = ClusterStateConfig(filename=self.source_dir / "metadata.json")
        self.provider = SimulatedInMemoryPredictiveClusterStateProvider(window=40, lag=10, data_dir=self.target_dir, decision_file_path=self.target_dir / "decisions.txt", max_cpu_limit=14, granularity=1, config=config,
                                                                        prediction_config=config.prediction_config, general_config=config.general_config)

    def test_read_metrics_data(self):
        """
        Test the read_metrics_data method, which is the window of data to process next
        """
        # Set up test data
        self.provider.curr_cpu_limit = 10
        self.provider.current_time = pd.Timestamp(datetime(2022, 1, 1, 0, 9, 0))
        self.provider.end_time = pd.Timestamp(datetime(2022, 1, 1, 0, 10, 0))
        self.provider.config.general_config = {'window': 5, 'lag': 2}
        self.provider.recorded_data = pd.DataFrame([
            {'timestamp': pd.Timestamp(datetime(2022, 1, 1, 0, 0, 0)), 'cpu': 1.0},
            {'timestamp': pd.Timestamp(datetime(2022, 1, 1, 0, 1, 0)), 'cpu': 2.0},
            {'timestamp': pd.Timestamp(datetime(2022, 1, 1, 0, 2, 0)), 'cpu': 3.0},
            {'timestamp': pd.Timestamp(datetime(2022, 1, 1, 0, 3, 0)), 'cpu': 4.0},
            {'timestamp': pd.Timestamp(datetime(2022, 1, 1, 0, 4, 0)), 'cpu': 5.0},
            {'timestamp': pd.Timestamp(datetime(2022, 1, 1, 0, 5, 0)), 'cpu': 6.0},
            {'timestamp': pd.Timestamp(datetime(2022, 1, 1, 0, 6, 0)), 'cpu': 7.0},
            {'timestamp': pd.Timestamp(datetime(2022, 1, 1, 0, 7, 0)), 'cpu': 8.0},
            {'timestamp': pd.Timestamp(datetime(2022, 1, 1, 0, 8, 0)), 'cpu': 9.0},
            {'timestamp': pd.Timestamp(datetime(2022, 1, 1, 0, 9, 0)), 'cpu': 10.0},
            {'timestamp': pd.Timestamp(datetime(2022, 1, 1, 0, 10, 0)), 'cpu': 11.0},
        ])
        self.provider.recorded_data.set_index('timestamp', inplace=True)

        # Call the method
        result = self.provider.read_metrics_data()

        # Verify the result
        expected_result = pd.DataFrame([
            {'cpu': 3.0},  # TODO: I think we have a bug. We want the window 5+ lag 2, so i think 7 data points, not 8.
            {'cpu': 4.0},
            {'cpu': 5.0},
            {'cpu': 6.0},
            {'cpu': 7.0},
            {'cpu': 8.0},
            {'cpu': 9.0},
            {'cpu': 10.0},  # TODO: or maybe this is "future" data from prediction?
        ])

        type(result)
        self.assertEqual(result['cpu'].values.tolist(), expected_result['cpu'].values.tolist())

    def tearDown(self):
        shutil.rmtree(self.target_dir_sim, ignore_errors=True)
        shutil.rmtree(self.target_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
