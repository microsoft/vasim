# Cassandra Demo

This is an autoscaling demo of Cassandra, with a goal of demonstrating how to use VASim, and demonstrating autoscaling the CPU limit as simply as possible.

In this demo we use standalone Cassandra containers. A real deployment would run in more rebust orchestrator (ex: Kubernetes, K8ssandra, your container manager of choice), but for here we focus on demonstrating the autoscaling capability.

As we have multiple containers, they may or may not have similar CPU usage. To do the autoscaling:

1. (Most common) You can take the (average/median/sampling/etc) of the CPU usage across the cluster, and scale them all to the same limit
2. You could scale the containers independently, and run the algorithm for each CPU trace. This usually does not make sense for a balanced deployment.

Here, we take approach 1.

Contributions are welcome to the instructions and example!

## Prereqs:

You must have a machine with Python and Docker.

## Setup:

1. First, make sure you have [installed](https://github.com/microsoft/vasim/blob/main/CONTRIBUTING.md#developing) VASim.

2. You must also install the python docker package.

   `pip install docker`

3. Pull the [Cassandra image](https://hub.docker.com/_/cassandra/).

`docker run --name some-cassandra1 --network some-network -d cassandra:tag`