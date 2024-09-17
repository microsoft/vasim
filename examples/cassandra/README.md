# Cassandra Demo

This is going to be an autoscaling demo of Cassandra.  Currently it is a work-in-progress!!

This is an example of autoscaling a single Cassandra container instance. A real deployment would run in multiple containers or on Kubernetes, but for here we focus on demonstrating the autoscaling capability.

Contributions are welcome to the instructions and example!

## Prereqs:

You must have a machine with Python and Docker.

## Setup:

1. First, make sure you have [installed](https://github.com/microsoft/vasim/blob/main/CONTRIBUTING.md#developing) VASim.

2. You must also install the python docker package.

   `pip install docker`

3. Pull the [Cassandra image](https://hub.docker.com/_/cassandra/).

`docker run --name some-cassandra1 --network some-network -d cassandra:tag`