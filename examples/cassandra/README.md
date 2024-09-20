# Cassandra Demo

This is going to be an autoscaling demo of Cassandra.  Currently it is a work-in-progress!!

This is an example of autoscaling a single Cassandra container instance. A real deployment would run in multiple containers or on Kubernetes, but for here we focus on demonstrating the autoscaling capability.

Also note that this example uses a single container.  In a real deployment, where you have multiple containers, you have some choices to make depending on your workload.

1. (Most common) You can take the (average/median/sampling/etc) of the CPU usage across the cluster, and scale them all to the same limit
2. You could scale the containers independently, and run the algorithm for each CPU trace. This usually does not make sense for a balanced deployment.

Contributions are welcome to the instructions and example!

## Prereqs:

You must have a machine with Python and Docker.

## Setup:

1. First, make sure you have [installed](https://github.com/microsoft/vasim/blob/main/CONTRIBUTING.md#developing) VASim.

2. You must also install the python docker package.

   `pip install docker`

3. Pull the [Cassandra image](https://hub.docker.com/_/cassandra/).

`docker run --name some-cassandra1 --network some-network -d cassandra:tag`