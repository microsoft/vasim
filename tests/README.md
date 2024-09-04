# About tests

The tests focus on e2e (end-to-end) tests, and then specific tests that focus on particularly important areas of the code.


## End-to-end
Some tests of note:
* [test_e2e_single_run_sim.py](test_e2e_single_run_sim.py): A simple test run of a fixed set of parameters for both of the dummy algorithms.
* [test_e2e_multi_run_tune_with_strategy.py](test_e2e_multi_run_tune_with_strategy.py): Tests tuning parameters for both the `grid` (all combos) and `random` (with a max # to try) strategies.
* [test_e2e_analysis_pareto.py](test_e2e_analysis_pareto.py): Tests generating a Pareto curve to visualize the tuned data and the optimal parameters to minimize both slack and throttling.


## Code-specific tests
Highlighting a few that might be relevant for those wanting to use the simulator:
* [test_SimulatedInfraScaler.py](test_SimulatedInfraScaler.py): A test of the simulated infra scaler, which is the part of VASim that simulates K8s functionality (for example) of actually resizing the pods. The **recovery_time** parameter can be adusted to mimic the actual time of doing the pod scaling in the physical system.
* [test_config_params.py](test_config_params.py): This test is a work in progress and needs more tests added. Currently it tests the `lag` parameter, which defines the number of minutes to wait before making a prediction, essentially how long to wait for more data before reruning the autoscaling decision algorithm.


## Notes:
For our tests [data](test_data/), we use a trace from the [Alibaba dataset](https://github.com/alibaba/clusterdata).