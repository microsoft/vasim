#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#
"""
This file containers common functions used in the Cassandra demo.
It is used by the poll_metrics.py and run_recommender.py scripts.

This simple demo shows only standalone containers, but it could be modified to read CPU usage from a
    Kubernetes cluster/metrics-server/K8ssandra/etc. Contributions welcome!

"""

from datetime import datetime
import docker


WAIT_INTERVAL = 60  # how often to poll the CPU usage
CONTAINER_PREFIX = "some-cassandra"  # the containers to monitor must all start with this prefix
ERROR_BACKOFF = 5  # how long to wait before retrying after an error

RECOMMENDATION_FREQ = 10  # how often to make a recommendation in seconds
INITIAL_CPU_LIMIT_DEFAULT = 6  # the initial CPU limit to use, containers will be set to this.


def get_containers_list():
    """
    get a list of all containers with the name prefix CONTAINER_PREFIX
    """
    client = docker.from_env()
    # Get a list of all running container with the name prefix CONTAINER_PREFIX
    containers = client.containers.list()
    # Now, filter to list ALL containers with the prefix
    container_list = [c for c in containers if c.name.startswith(CONTAINER_PREFIX)]

    return container_list


def get_curr_cpu_usage(container):
    """
    This
    To modify this to work with Kubernetes, you would need to use the Kubernetes API. Contributions welcome!
    """

    container.reload()
    stats = container.stats(stream=False)

    cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
    system_cpu_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
    number_cpus = stats['cpu_stats']['online_cpus']
    cpu_percentage = (cpu_delta / system_cpu_delta) * number_cpus
    return cpu_percentage


def get_current_cpu_limit(containers):
    """
    Get the current CPU limit from the container
    This is a naive implementation that assumes all containers are set to the same CPU limit.
    """

    # We have the containers, but the data may be stale. So we need to read it from the container.
    containers[0].reload()

    return containers[0].attrs['HostConfig']['CpuQuota'] / 100000


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
