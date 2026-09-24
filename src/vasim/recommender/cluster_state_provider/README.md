# Info

* [ClusterStateConfig.py](ClusterStateConfig.py): This handles the configuration stored in the `metadata.json` file. This is a bit of a work in progress, see <https://github.com/microsoft/vasim/issues/31>. Note: `ClusterStateConfig` subclasses `dict` but stores its data in instance attributes (`algo_specific_config`, `general_config`, `prediction_config`). It implements `__getstate__`/`__setstate__` so it serialises correctly when passed across a `multiprocessing.Pool` boundary (e.g. in `tune_with_strategy`).
* [ClusterStateProvider](ClusterStateProvider.py): Base class. We need to refactor.
* [FileClusterStateProvider.py](FileClusterStateProvider.py): This was part of bindings to a Kubernetes cluster. We need to refactor it, but the `get_next_recorded_data` is a key function that is still called directly by the simulator.
* [PredictiveFileClusterStateProvider.py](PredictiveFileClusterStateProvider.py): This needs to be refactored/removed
