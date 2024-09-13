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
from simulator.InMemorySimulator import InMemoryRunnerSimulator

RECOMMENDATION_FREQ = 300  # how often to make a recommendation in seconds

# make the main method

if __name__ == '__main__':

    # we will pass it the metadata.json file that is up a directory. you can change this to the path of your metadata.json file
    root_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    # go up one directory, then go into data  folder, so we need ../data/metadata.json appended to root_dir
    meta = root_dir / "../data/metadata.json"

    # data dir is inside the root_dir
    data_dir = root_dir / "data"

    # BTW, this will write out the files into the "data_simulation" folder in the same directory as this file

    runner = InMemoryRunnerSimulator(data_dir, initial_cpu_limit=14, algorithm="additive", config_path=meta)

    print("starting recommender loop. Writing to data_simulation dir. Ctrl-C to exit.")

    # We will call this in a loop every 5 minutes
    while True:
        results = runner.run_last_window_only()
        print(results)
        print(f"Now sleeping for {RECOMMENDATION_FREQ} seconds")
        time.sleep(RECOMMENDATION_FREQ)
