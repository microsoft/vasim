# Cassandra Demo

This is an autoscaling demo of Cassandra, with a goal of demonstrating how to use VASim, and demonstrating autoscaling the CPU limit as simply as possible.

In this demo we use standalone Cassandra containers. A real deployment would run in more robust orchestrator (ex: Kubernetes, K8ssandra, your container manager of choice), but for here we focus on demonstrating the autoscaling capability.

As we have multiple containers, they may or may not have similar CPU usage. To do the autoscaling:

1. (Most common) You can take the (average/median/sampling/etc) of the CPU usage across the cluster, and scale them all to the same limit
2. You could scale the containers independently, and run the algorithm for each CPU trace. This usually does not make sense for a balanced deployment.

Here, we take approach 1.

Contributions are welcome to the instructions and example!

## Prereqs

You must have a machine with Python and Docker.

## Setup

1. First, make sure you have [installed](https://github.com/microsoft/vasim/blob/main/CONTRIBUTING.md#developing) VASim.

2. You must also install the python docker package.

   `pip install docker`

3. For this toy example, we'll use the [Cassandra container image](https://hub.docker.com/_/cassandra/) and make a 2 node cluster:

   ```bash
   TAG=cassandra:5.0-jammy
   docker network create some-network
   docker run --name some-cassandra1 --network some-network  -d $TAG
   docker run --name some-cassandra2 --network some-network -d  -e CASSANDRA_SEEDS=some-cassandra $TAG
   ```

4. We also need something to generate load, so we'll use the `nb5` [NoSQLBench](https://docs.nosqlbench.io/getting-started/) tool.
There are many tools you can use for this, this is just one option.

   ```bash
   curl -L -O https://github.com/nosqlbench/nosqlbench/releases/latest/download/nb5
   chmod 700 ./nb5
   ```

## Information

This demo contains several files:

- DemoCommons.py: Utility functions related to getting information about the running container(s)
- InMemoryLive.py: This is similar to `InMemorySimulator.py` except that it works on live data as it comes in, not a full trace.
- LiveContainerInfraScaler.py: This is similar to `SimulatedInfraScaler.py`, except that it makes changes to running containers.
- poll_metrics.py: This generates csvs of CPU usage of the running container(s)
- run_recommender.py: This is the main function to run the recommender live.

Also data folders:

- data: This will be where the generated CPU metrics data goes
  - metadata.json: This is the configuration file, as described in the [notebook](https://github.com/microsoft/vasim/blob/main/examples/using_vasim.ipynb).
- data_simulations: This will be generated, the output will go here.

## Start the demo

### Start collecting the metrics

....#TODO START HERE

