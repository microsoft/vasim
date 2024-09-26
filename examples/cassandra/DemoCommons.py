#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#

# pylint: disable=C0103

"""
This file containers common functions used in the Cassandra demo.

It is used by the poll_metrics.py and run_recommender.py scripts.

This simple demo shows only standalone containers, but it could be modified to read CPU usage from a
    Kubernetes cluster/metrics-server/K8ssandra/etc. Contributions welcome!
"""

import json
from datetime import datetime
from time import sleep

import docker  # pylint: disable=import-error
import pandas as pd

WAIT_INTERVAL = 60  # how often to poll the CPU usage
CONTAINER_PREFIX = "some-cassandra"  # the containers to monitor must all start with this prefix
ERROR_BACKOFF = 5  # how long to wait before retrying after an error

RECOMMENDATION_FREQ = 10  # how often to make a recommendation in seconds


def get_containers_list():
    """Get a list of all containers with the name prefix CONTAINER_PREFIX."""
    client = docker.from_env()
    # Get a list of all running container with the name prefix CONTAINER_PREFIX
    containers = client.containers.list()
    # Now, filter to list ALL containers with the prefix
    container_list = [c for c in containers if c.name.startswith(CONTAINER_PREFIX)]

    return container_list


def get_curr_cpu_usage(containers):
    """
    This currently averages the CPU usage of all containers.

    You could change this to use the max, min, etc.
    Every workload may have different requirements.

    To modify this to work with Kubernetes, you would need to use the Kubernetes API. Contributions welcome!
    """

    all_cpu_usage = []
    for container in containers:
        container.reload()
        stats = container.stats(stream=False)

        cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - stats["precpu_stats"]["cpu_usage"]["total_usage"]
        system_cpu_delta = stats["cpu_stats"]["system_cpu_usage"] - stats["precpu_stats"]["system_cpu_usage"]
        number_cpus = stats["cpu_stats"]["online_cpus"]
        cpu_percentage = (cpu_delta / system_cpu_delta) * number_cpus
        all_cpu_usage.append(cpu_percentage)

    # Now return the average of all the containers
    cpu_percentage = sum(all_cpu_usage) / len(all_cpu_usage)
    return cpu_percentage


def get_curr_cpu_usage_over_window(containers, window_seconds=60):
    """
    This currently averages the CPU usage of all containers over a window.

    This is because there may be a lot of variability in the CPU usage, and we want to smooth it out.
    """

    # We will take the average of the CPU usage over the window
    # We will call get_curr_cpu_usage multiple times and average the results
    all_cpu_usage = []
    # This is the initial call
    all_cpu_usage.append(get_curr_cpu_usage(containers))

    # we will use pd.Timestamp to get the current time
    curr_time = pd.Timestamp.now()
    # compare this to time delta of window_seconds
    end_time = curr_time + pd.Timedelta(seconds=window_seconds)

    while curr_time < end_time:

        # We'll poll when the minutes mod 10 is 0
        if curr_time.minute % 10 == 0:
            all_cpu_usage.append(get_curr_cpu_usage(containers))

        # we need to make sure not to oversleep!!
        curr_time = pd.Timestamp.now()
        # we will sleep for 1 second, and check the time again
        # This is because docker stats can be slow.
        if curr_time < end_time:
            sleep(1)

    # Now return the average of all the containers
    cpu_percentage = sum(all_cpu_usage) / len(all_cpu_usage)
    return cpu_percentage


def get_current_cpu_limit(containers):
    """
    Get the current CPU limit from the container.

    This is a naive implementation that assumes all containers are set to the same CPU limit.
    """

    # We have the containers, but the data may be stale. So we need to read it from the container.
    containers[0].reload()

    return containers[0].attrs["HostConfig"]["CpuQuota"] / 100000


def set_current_cpu_limit(containers, new_cpu_limit):
    """Set the current CPU limit on the container."""
    for container in containers:
        container.update(cpu_quota=int(new_cpu_limit * 100000))


def get_timestamp():
    """
    This is based on the current format that VASim read the timestamps.

    Ideally, this would be replaced with a more robust timestamping mechanism and standard format.
    See: https://github.com/microsoft/vasim/issues/34
    """
    return datetime.now().strftime("%Y.%m.%d-%H:%M:%S:%f")


def get_max_cpu_limit(config):
    """Here we will parse metadata.json to get the max_cpu_limit."""
    # Read the config file
    with open(config, "r", encoding="utf-8") as f:
        config = json.load(f)

    return config["general_config"]["max_cpu_limit"]
