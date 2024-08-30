from abc import abstractmethod


class ClusterStateProvider:
    def __init__(self, data_dir=None, features=None, window=None, decision_file_path=None, lag=None):
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
        return False

    @abstractmethod
    def process_data(self, data=None):
        pass
