#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#

# In this file, we will run a recommender algorithm to recommend the best algorithm to use for the Cassandra container.
# we will use the data collected from the poll_metrics.py script to make the recommendation.

import time
import os
from pathlib import Path
import docker
from simulator.InMemorySimulator import InMemoryRunnerSimulator
from poll_metrics import CONTAINER_NAME

RECOMMENDATION_FREQ = 10  # how often to make a recommendation in seconds
INITIAL_CPU_LIMIT_DEFAULT = 6  # the initial CPU limit to use if we can't read it from the container


if __name__ == '__main__':

    # we will pass it the metadata.json file that is up a directory. you can change this to the path of your metadata.json file
    root_dir = Path(os.path.dirname(os.path.abspath(__file__)))

    # data dir is inside the root_dir
    data_dir = root_dir / "data"

    # Read the current CPU limit from the container. This is the initial CPU limit that we will use for the simulation.
    # If it is not set, use the default value.

    client = docker.from_env()
    container = client.containers.get(CONTAINER_NAME)
    INITIAL_CPU_LIMIT = container.attrs['HostConfig']['CpuQuota'] / 100000

    if INITIAL_CPU_LIMIT == 0:
        print(f"No CPU limit on container {CONTAINER_NAME}. Using default value.")
        INITIAL_CPU_LIMIT = INITIAL_CPU_LIMIT_DEFAULT

    print(f"Initial CPU limit: {INITIAL_CPU_LIMIT}")

    # we will use the additive algorithm for now. You can change this to any of the other algorithms.
    runner = InMemoryRunnerSimulator(data_dir, initial_cpu_limit=INITIAL_CPU_LIMIT, algorithm="additive")

    print("starting recommender loop. Writing to data_simulation dir. Ctrl-C to exit.")

    # We will call this in a loop every 5 minutes
    while True:

        # This will run the recommender algorithm for the last window of data and write the results to
        #      the data_simulation folder. (run_simulation -> _execute_simulation_step).
        # TODO: As part of this, it calls self.infra_scaler.scale(). We could override this method to call our own
        runner.run_simulation(save_to_file=False)

        print(f"Now sleeping for {RECOMMENDATION_FREQ} seconds")
        time.sleep(RECOMMENDATION_FREQ)

        # Now read in the new data that accumlated from the poll_metrics.py while we were sleeping
        runner.cluster_state_provider.process_data(list(data_dir.glob("**/*.csv")))
