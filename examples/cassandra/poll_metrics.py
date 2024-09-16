#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#
from datetime import datetime
from pathlib import Path
from time import sleep
import docker

"""
This script is used to read live CPU usage data from the container and write it to a file.

It stores the csv file in the 'data' directory, with the format:
TIMESTAMP,CPU_USAGE_ACTUAL
2021.06.02-15:45:12:123456,0.5

"""

WAIT_INTERVAL = 60  # how often to poll the CPU usage
CONTAINER_NAME = "some-cassandra1"  # the container to monitor
ERROR_BACKOFF = 5


def get_curr_cpu_usage(container_name=CONTAINER_NAME):
    """
    This demo shows only a standalone container, but it could be modified to read CPU usage from a
    Kubernetes cluster/metrics-server, or from multiple containers.

    To modify this to work with Kubernetes, you would need to use the Kubernetes API. Contributions welcome!
    """

    client = docker.from_env()
    container = client.containers.get(container_name)
    stats = container.stats(stream=False)

    cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
    system_cpu_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
    number_cpus = len(stats['cpu_stats']['cpu_usage']['percpu_usage'])
    cpu_percentage = (cpu_delta / system_cpu_delta) * number_cpus
    return cpu_percentage


def get_timestamp():
    """
    This is based on the current format that VASim read the timestamps.

    Ideally, this would be replaced with a more robust timestamping mechanism and standard format.
    See: https://github.com/microsoft/vasim/issues/34
    """
    return datetime.now().strftime("%Y.%m.%d-%H:%M:%S:%f")


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

    print("starting monitor loop. Writing to " + filename + ". Ctrl-C to exit.")
    while True:
        try:
            usage = get_curr_cpu_usage()
            readings = "{},{}\n".format(get_timestamp(), usage)
        except KeyError:
            print("error getting data, is container running? Trying again")
            sleep(ERROR_BACKOFF)
            continue

        print(readings)
        f.write(readings)
        f.flush()
        sleep(WAIT_INTERVAL)
