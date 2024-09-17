# Info

## Files

* [InMemorySimulator.py](InMemorySimulator.py): This is the main control loop. It contains `run_simulation` which drives calling the algorithm.
  **Important:** for now, the `_create_recommender_algorithm` is what you need to modify to add your own autoscaling algorithm.
* Simulated**StateProvider: These files contain the main guts of the simulation code. Right now, there are several redundant files that we plan to fix up in <https://github.com/microsoft/vasim/issues/14>.
* [SimulatedInfraScaler.py](SimulatedInfraScaler.py): This simulates scaling the pods up/down and contains a recovery parameter to simulate the delay to update/resize a pod in a live system
* [ParameterTuning.py](ParameterTuning.py): This generates different parameter combinations and then kicks off a series of simulations based on those

## Future plans

We hope to make the simulator more pluggable (including allowing algorithms based in other programming languages), with details outlined in [the wiki](https://github.com/microsoft/vasim/wiki/Pluggable-Simulator-Design).
