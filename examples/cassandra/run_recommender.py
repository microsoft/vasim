#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#

#

"""
In this file, we will run a recommender algorithm to recommend the best algorithm to use for the Cassandra container.

we will use the data collected from the poll_metrics.py script to make the recommendation.
"""

import os
from pathlib import Path

from DemoCommons import get_containers_list, get_max_cpu_limit, set_current_cpu_limit
from InMemoryLive import InMemoryLiveRunner

if __name__ == "__main__":

    # we will pass it the metadata.json file that is up a directory. you can change this to the path of your metadata.json file
    root_dir = Path(os.path.dirname(os.path.abspath(__file__)))

    # data dir is inside the root_dir
    data_dir = root_dir / "data"
    # config file is inside the data_dir
    config_path = data_dir / "metadata.json"

    # Read the current CPU limit from the container. This is the initial CPU limit that we will use for the simulation.
    # If it is not set, use the default value.
    # You can reset this manually on the command line with `docker update some-cassandra --cpu-quota 600000`` for example
    containers_list = get_containers_list()

    # Reset all of the containers to the initial CPU limit
    initial_cpu_limit = get_max_cpu_limit(config_path)
    print("Setting all containers to the initial CPU limit of", initial_cpu_limit)
    for container in containers_list:
        set_current_cpu_limit([container], initial_cpu_limit)

    # we will use the additive algorithm for now. You can change this to any of the other algorithms.
    # We will just pass it a single container for now. You can pass it a list of containers.
    runner = InMemoryLiveRunner(
        data_dir, initial_cpu_limit=initial_cpu_limit, algorithm="additive", containers=containers_list
    )

    runner.run_live()
