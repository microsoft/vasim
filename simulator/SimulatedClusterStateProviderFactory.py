from recommender.cluster_state_provider.ClusterStateConfig import ClusterStateConfig
from simulator.SimulatedBaseClusterStateProvider import SimulatedBaseClusterStateProvider
from simulator.SimulatedInMemoryClusterStateProvider import SimulatedInMemoryClusterStateProvider
from simulator.SimulatedInMemoryPredictiveClusterStateProvider import SimulatedInMemoryPredictiveClusterStateProvider


class SimulatedClusterStateProviderFactory:
    def __init__(self, data_dir: str, out_filename: str, config: ClusterStateConfig):
        self.config = config
        self.data_dir = data_dir
        self.out_filename = out_filename
        if config.predictive:
            self.prediction_config = config.prediction_config

    def create_provider(self, predictive: bool) -> SimulatedBaseClusterStateProvider:
        if predictive:
            return SimulatedInMemoryPredictiveClusterStateProvider(
                data_dir=self.data_dir,
                prediction_config=self.prediction_config,
                max_cpu_limit=self.config.max_cpu_limit,
                decision_file_path=self.out_filename,
                granularity=self.config.granularity,
                lag=self.config.lag,
                window=self.config.window,
                min_cpu_limit=self.config.min_cpu_limit,
                config=self.config
            )
        else:
            return SimulatedInMemoryClusterStateProvider(
                data_dir=self.data_dir,
                max_cpu_limit=self.config.max_cpu_limit,
                decision_file_path=self.out_filename,
                granularity=self.config.granularity,
                lag=self.config.lag,
                window=self.config.window,
                min_cpu_limit=self.config.min_cpu_limit,
                config=self.config
            )
