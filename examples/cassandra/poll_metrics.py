#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#

# pylint: disable=W0511,R1732

"""
This script is used to read live CPU usage data from the container and write it to a file.

It stores the csv file in the 'data' directory, with the format:
TIMESTAMP,CPU_USAGE_ACTUAL
2021.06.02-15:45:12:123456,0.5
"""

from datetime import datetime
from pathlib import Path
from time import sleep

import docker  # pylint: disable=import-error
from DemoCommons import (
    CONTAINER_PREFIX,
    ERROR_BACKOFF,
    WAIT_INTERVAL,
    get_curr_cpu_usage,
    get_curr_cpu_usage_over_window,
    get_timestamp,
)

if __name__ == "__main__":

    curr_dir = Path().absolute()
    # if there is no data directory, create it
    # TODO: remove hardcoded path
    if not Path(str(curr_dir) + "/data").exists():
        Path(str(curr_dir) + "/data").mkdir()
    filename = str(curr_dir) + "/data/" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + "_perf_event_log.csv"
    monitor_file = Path(filename)
    if not monitor_file.exists():  # write the header
        f = open(monitor_file, "a", encoding="utf-8")
        f.write("TIMESTAMP,CPU_USAGE_ACTUAL\n")
    else:
        f = open(monitor_file, "a", encoding="utf-8")

    client = docker.from_env()
    # Get a list of all running container with the name prefix CONTAINER_PREFIX
    # We'll get a list of all containers to start with, then do a regex
    # First, get all containers:
    containers = client.containers.list()
    # Now, filter to list ALL containers with the prefix
    container_list = [c for c in containers if c.name.startswith(CONTAINER_PREFIX)]
    # Write a begining timestamp
    initial_val = get_curr_cpu_usage(container_list)
    print("Initial CPU usage: " + str(initial_val))
    f.write(f"{get_timestamp()},{initial_val}\n")
    f.flush()

    print("starting monitor loop. Writing to " + filename + ". Ctrl-C to exit.")
    while True:
        try:
            usage = get_curr_cpu_usage_over_window(container_list, WAIT_INTERVAL)
            readings = f"{get_timestamp()},{usage}\n"
        except KeyError:
            print("error getting data, is container running? Trying again")
            sleep(ERROR_BACKOFF)
            continue

        print(readings)
        f.write(readings)
        f.flush()
