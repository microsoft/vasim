# 1. Clean-up
* Remove unnecessary files and directories.
  * KS: this is mostly done, except maybe the "data" folder, need to clean up the "sandbox" folder, then see Karla's notes below.
  * also need to clean up sandbox_analysis and the rest of the plot functions.
* Add comments and docstrings to explain the code - for recommender and simulator
* Remove hard - coded values of metadata.json or perf_log.csv and use configuration files or command - line arguments.
I think we can make as parameters filenames for metadata and perf_log, but our output namings need to go to global configs and be hardcoded
* Update README and design docs. You can use docs folder for seq diagrams and use https: // sequencediagram.org for changing them(use txt files)
* Maybe rename Caasper to Vasim? I didn't dare to do it because my dependencies and python env is to fragile))
  * This will be done when we move to github, but we should doublecheck the references!
* Please do something about forecasting folder. i think it looks sad with 2 folders and 2 files
  * KS: I'm a little confused about how this relates to the run() function the user writes. how can we also make this pluggable?


Notes from Karla:
* Let's plan to keep the pareto just as 2d for now (simplier), then can add 3d later as a PR?
* Do we want to keep "predictive" params and regular params separate? or was that specific to Caasper?  (ex: in `ParameterTuning.py: create_modified_configs` they are separate)
  * I think we need to redo the json file to have {algo specific params} {simulator general params} {simulator prediction params}
  * But I am still a bit confused on the prediction params and how to best allow users to modify them
* TODO: maybe we unify FileClusterStateProvider and Predictive? (similar with simulator..unify the predictive and reactive)? if they don't want to use predictive, then maybe we can just feed it 0 data for the window size?
* What can we borrow from anna's demo [notebook](https://msgsl.visualstudio.com/Ozone/_git/CaaSPER?path=/demo/demo.ipynb&version=GBdemo_video&_a=preview) to help users understand how to use our code?
* Is it ok to get rid of FileClusterStateProvider and just replace that with ClusterStateProvider? is there some way we should clean this up now that it's just simulated/not a real system? or maybe I am making some bad assumptions!!  And what about PredcitiveFileClusterState... etc
* what is the calculate_objective function? If the alphas are random, how does that whole process work? also, why is the loop for 500 in paretofront2d line 28?
* TODO: There is a bug with 'grid' in that it always trys all combinations, even if num_combinations is less than the total.
* TODO delete sqlmi sandbox and make some other tutorial based on the tests.
* Still confused about what forecasting/models/oracle.py is? do we use it?  What about the forecasting folder?
* Do we need to keep both the InMemoryPredictive and the regular ClusterStateProvider?

* TODO, we're currently reading in all CSVs at once. maybe streaming would be more scalable.

##### Contributing
This project uses [pre-commit](https://pre-commit.com/) hooks. Run  `python -m pip install pre-commit` if you don't already have this in your machine. Afterward, run `pre-commit install` to install pre-commit into your git hooks.

# 2. Improvements / Refactoring
* we use self - written grid search. Let's utilize sklearn's GridSearchCV or moe flexible / advanced

```

from hyperopt import fmin, tpe, hp, Trials, STATUS_OK

def objective(params):
    # Your custom objective function
    accuracy= your_custom_training_function(params)
    return {'loss': -accuracy, 'status': STATUS_OK}

space= {
    'param1': hp.choice('param1', [1, 2, 3]),
    'param2': hp.uniform('param2', 0.1, 1.0)
}

best= fmin(fn=objective,
            space=space,
            algo=tpe.suggest,
            max_evals=100)
print("Best parameters found:", best)

```

# 3. Pluggable Simulator Design

# Overview

The goal is to make the existing Python - based simulator pluggable, allowing users to implement their own scaling algorithms in any programming language. Users will then provide the path to their executable algorithm, and the simulator will handle the integration seamlessly.


# Objectives

- **Language - Agnostic**: Allow users to implement their scaling algorithms in any programming language.
- **Simple Integration**: Users should only need to provide the path to their executable, with no need for extensive integration work.
- **Flexible Communication**: Use stdin / stdout or other methods(like HTTP or gRPC) for communication between the simulator and the algorithm.
- **Extensible Design**: The simulator should be able to support various communication protocols and easily extend to new ones.

# Design Components

# 1. **Simulator Interface**
   - The simulator should define a clear interface that users' algorithms need to implement. This interface will consist of:
     - **Input**: The simulator will pass input data(e.g., metrics) to the algorithm. Config can be read from the json file
     - **Output**: The simulator will expect the algorithm to return processed data(e.g., scaled metrics).

# 2. **External Algorithm Implementation**
   - Users will write their scaling algorithms as standalone executables that:
     - Accept input via stdin, files, or network requests.
     - Process the input data according to the specified logic.
     - Output the results to stdout, files, or send them back over the network.
   - These algorithms can be written in any programming language.

# 3. **Wrapper/Adapter in Simulator**
   - The simulator will include a wrapper or adapter that:
     - Launches the external algorithm as a separate process or service.
     - Passes the necessary input data to the algorithm.
     - Captures and processes the output data returned by the algorithm.
   - This component will handle errors, such as process failures or incorrect data formats.

# 4. **Configuration and Execution**
   - Users will specify the path to their algorithm executable via a command - line argument or configuration file.
   - Example command - line usage: ```bash
     python simulator.py - -algorithm / path / to / external / algorithm - -config data / metadata.json
     ```
   - The simulator will invoke the provided executable, passing data and retrieving results as part of the simulation.

# 5. **Error Handling and Validation**
   - The simulator will validate the output from the external algorithm to ensure it matches the expected format.
   - Robust error handling will be implemented to manage issues like:
     - Failed process execution.
     - Incorrect output formats.
     - Timeouts or unresponsive algorithms.

# 6. **Extensibility**
   - The design should allow for easy addition of new communication protocols(e.g., gRPC, REST API).
   - Users and developers should be able to extend the simulator to support different types of external algorithms without modifying the core logic.

# Advantages

- **Language Independence**: Users are free to implement algorithms in the language of their choice.
- **Ease of Use**: Simple interface and minimal setup required for users to integrate their algorithms.
- **Scalability**: The simulator can be extended to support more complex integration patterns, including distributed algorithms or web services.

# Next Steps

1. ** Define the input / output format ** that the simulator and external algorithms will use.
2. ** Implement the wrapper / adapter ** in the simulator for process management and data handling.
3. ** Create example implementations ** of scaling algorithms in different languages to demonstrate the pluggability.
4. ** Develop documentation ** to guide users in implementing their algorithms and integrating them with the simulator.
