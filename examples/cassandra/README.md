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

This demo contains several code files:

- DemoCommons.py: Utility functions related to getting information about the running container(s)
- InMemoryLive.py: This is similar to `InMemorySimulator.py` except that it works on live data as it comes in, not a full trace.
- LiveContainerInfraScaler.py: This is similar to `SimulatedInfraScaler.py`, except that it makes changes to running containers.
- poll_metrics.py: This generates csvs of CPU usage of the running container(s)
- run_recommender.py: This is the main function to run the recommender live.

Folders:

- data: This will be where the generated CPU metrics data goes
  - metadata.json: This is the configuration file, as described in the [notebook](https://github.com/microsoft/vasim/blob/main/examples/using_vasim.ipynb).
- data_simulations: This will be generated, the output will go here.
- cassfiles: These will be used with the `nb5` tool to drive the traffic.

## Start the demo

### Setup the benchmark

```bash
# change directory
cd cassfiles

# get the IP address of the docker container:
IP_ADDR=docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' some-cassandra1
DC=datacenter1

# Setup schema
./nb5 nova-keyvalue default.schema thread-count=1 hosts=$IP_ADDR  driverconfig=driverconfig.json  localdc=$DC

# Rampup
./nb5 nova-keyvalue default.rampup rampup-cycles=10000000 main-cycles=10000000 cyclerate=60000 thread-count=160 hosts=$IP_ADDR localdc=$DC driverconfig=driverconfig.json  --progress console:1s --report-csv-to casscsv-ramp
```

### Start collecting the metrics

```bash
python3 poll_metrics.py
```

This will start a file that looks like this:

```bash
cat data/*_perf_event_log.csv
```

```csv
TIMESTAMP,CPU_USAGE_ACTUAL
2024.09.23-00:28:23:847311,0.0062846441947565545
2024.09.23-00:29:26:869317,0.006324667154204469
2024.09.23-00:30:29:919104,0.006529308732144707
```

### Check the config in metadata.json

For this example, we'll use the `additive` algorithm, from [DummyAdditiveRecommender.py](https://github.com/microsoft/vasim/blob/main/src/vasim/recommender/DummyAdditiveRecommender.py).

```bash
cat data/metadata.json
```

```json
{
    "algo_specific_config": {
        "addend": 2 # add 2 cores buffer on top of a moving average.
    },
    "general_config": {
        "recovery_time": 2, # How long to wait after doing an update (after making a change to #cpus)
        "window": 5, # How many minutes of data to feed to the algorithm
        "lag": 1, # How many minutes to wait between runs of the recommender algorithm
        "max_cpu_limit": 5.0, # The max number of cores to recommend
        "min_cpu_limit": 1.0 # The minimum number of cores to recommend
    }
}
```

Ignore any `prediction_config`, this is not used for now.

### Start the recommender

Depending on how large your machine is, you might want to set some different defaults for the number of cores. In `data/metadata.json` there is a parameter `"max_cpu_limit": 5,` that you can change.  Remember that you have two containers running, along with the recommender script and benchmark (if you did this all on one machine), so you might need to adjust this number down.

This will start the recommender with the config above and the default algorithm.

```bash
python3 run_recommender.py
```

### Start the traffic

Now we are ready to start the traffic!
