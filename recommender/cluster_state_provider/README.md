# Info

* [ClusterStateConfig.py](cluster_state_provider/ClusterStateConfig.py): This handles the configuration stored in the `metadata.json` file. This is a bit of a work in progress, see https://github.com/microsoft/vasim/issues/31
* [ClusterStateProvider](cluster_state_provider/ClusterStateProvider.py): Base class. We need to refactor.
* [FileClusterStateProvider.py](cluster_state_provider/FileClusterStateProvider.py): This was part of bindings to a Kubernetes cluster. We need to refactor it, but the `get_next_recorded_data` is a key function that is still called directly by the simulator.
* [PredictiveFileClusterStateProvider.py](cluster_state_provider/PredictiveFileClusterStateProvider.py): This needs to be refactored/removed
