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
import pandas as pd
from pathlib import Path
import docker
from poll_metrics import CONTAINER_NAME  # TODO: this should be in a shared file, or cmd line arg
from LiveContainerInfraScaler import LiveContainerInfraScaler

from vasim.simulator.InMemorySimulator import InMemoryRunnerSimulator
from InMemoryLive import InMemoryRunner

RECOMMENDATION_FREQ = 10  # how often to make a recommendation in seconds
INITIAL_CPU_LIMIT_DEFAULT = 6  # the initial CPU limit to use if we can't read it from the container


if __name__ == '__main__':

    # we will pass it the metadata.json file that is up a directory. you can change this to the path of your metadata.json file
    root_dir = Path(os.path.dirname(os.path.abspath(__file__)))

    # data dir is inside the root_dir
    data_dir = root_dir / "data"

    # Read the current CPU limit from the container. This is the initial CPU limit that we will use for the simulation.
    # If it is not set, use the default value.
    # You can reset this manually on the command line with `docker update some-cassandra --cpu-quota 600000`` for example

    client = docker.from_env()
    container = client.containers.get(CONTAINER_NAME)
    initial_cpu_limit = container.attrs['HostConfig']['CpuQuota'] / 100000

    if initial_cpu_limit == 0:
        print(f"No CPU limit on container {CONTAINER_NAME}. Using default value.")
        # set the default value without breaking pylint
        initial_cpu_limit = INITIAL_CPU_LIMIT_DEFAULT  # pylint: disable=invalid-name
        container.update(cpu_quota=int(initial_cpu_limit * 100000))

    print(f"Initial CPU limit: {initial_cpu_limit}")

    # we will use the additive algorithm for now. You can change this to any of the other algorithms.
    # runner = InMemoryRunnerSimulator(data_dir, initial_cpu_limit=INITIAL_CPU_LIMIT, algorithm="additive")
    runner = InMemoryRunner(data_dir, initial_cpu_limit=initial_cpu_limit, algorithm="additive", container=container)

    runner.run_live()
