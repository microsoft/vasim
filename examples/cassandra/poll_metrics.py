#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#
"""
This script is used to read live CPU usage data from the container and write it to a file.

It stores the csv file in the 'data' directory, with the format:
TIMESTAMP,CPU_USAGE_ACTUAL
2021.06.02-15:45:12:123456,0.5

"""

from datetime import datetime
from pathlib import Path
from time import sleep
import docker


from DemoCommons import WAIT_INTERVAL, ERROR_BACKOFF, CONTAINER_PREFIX
from DemoCommons import get_curr_cpu_usage, get_timestamp


if __name__ == "__main__":

    curr_dir = Path().absolute()
    # if there is no data directory, create it
    # TODO: remove hardcoded path
    if not Path(str(curr_dir) + "/data").exists():
        Path(str(curr_dir) + "/data").mkdir()
    filename = str(curr_dir) + "/data/" + \
        datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + "_perf_event_log.csv"
    monitor_file = Path(filename)
    if not monitor_file.exists():  # write the header
        f = open(monitor_file, 'a')
        f.write("TIMESTAMP,CPU_USAGE_ACTUAL\n")
    else:
        f = open(monitor_file, 'a')

    client = docker.from_env()
    # Get a list of all running container with the name prefix CONTAINER_PREFIX
    # We'll get a list of all containers to start with, then do a regex
    # First, get all containers:
    containers = client.containers.list()
    # Now, filter to list ALL containers with the prefix
    container_list = [c for c in containers if c.name.startswith(CONTAINER_PREFIX)]

    print("starting monitor loop. Writing to " + filename + ". Ctrl-C to exit.")
    while True:
        try:
            usage = get_curr_cpu_usage(container_list)  # TODO: loop through all containers
            readings = "{},{}\n".format(get_timestamp(), usage)
        except KeyError:
            print("error getting data, is container running? Trying again")
            sleep(ERROR_BACKOFF)
            continue

        print(readings)
        f.write(readings)
        f.flush()
        sleep(WAIT_INTERVAL)
