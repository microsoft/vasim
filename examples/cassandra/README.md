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

To run this all on a single VM, we recommend a VM with at least 16 CPU cores (for this simple, contrived scenario). Else, you can run it over multiple machines for a more authentic setup.

## Setup

1. First, make sure you have [installed](https://github.com/microsoft/vasim/blob/main/CONTRIBUTING.md#developing) VASim.

2. You must also install the python docker package.

   `pip install docker`

3. For this toy example, we'll use the [Cassandra container image](https://hub.docker.com/_/cassandra/) and make a 2 node cluster:

   ```bash
   TAG=cassandra:5.0-jammy
   docker network create some-network
   docker run --name some-cassandra1 --network some-network -d $TAG
   sleep 120  #wait for first one
   docker run --name some-cassandra2 --network some-network -d  -e CASSANDRA_SEEDS=some-cassandra1 $TAG
   ```

4. We also need something to generate load, so we'll use the `nb5` [NoSQLBench](https://docs.nosqlbench.io/getting-started/) tool.
There are many tools you can use for this, this is just one option.

   ```bash
   cd cassfiles
   curl -L -O https://github.com/nosqlbench/nosqlbench/releases/latest/download/nb5
   chmod 700 ./nb5
   ```

## Information

**This demo contains several code files:**

- DemoCommons.py: Utility functions related to getting information about the running container(s)
- InMemoryLive.py: This is similar to `InMemorySimulator.py` except that it works on live data as it comes in, not a full trace.
- LiveContainerInfraScaler.py: This is similar to `SimulatedInfraScaler.py`, except that it makes changes to running containers.
- poll_metrics.py: This generates csvs of CPU usage of the running container(s)
- run_recommender.py: This is the main function to run the recommender live.

**Folders:**

- data: This will be where the generated CPU metrics data goes
  - metadata.json: This is the configuration file, as described in the [notebook](https://github.com/microsoft/vasim/blob/main/examples/using_vasim.ipynb).
- data_simulations: This will be generated, the output will go here.
- cassfiles: These will be used with the `nb5` tool to drive the traffic.

## Phase 1: Get the initial trace

In the first phase, we will setup the benchmark and record the CPU data WITHOUT running the recommendation algorithm.

**IMPORTANT:** _Ensure that you have enough free CPUs on your machine to run the benchmark without CPU throttling._ If the CPU usage is throttled, it makes it harder (but not impossible) to recreate the simulation. VASim detects throttling when the max CPU usage value is the same as the CPU quota/limit.  But for gathering the initial trace, it is best that it is not throttled.  If necessary, place your container (or the benchmarking tool) on multiple machines.

For this toy example with everything on a single machine, we recommend TODO #CPUs on the machine.

### Setup the benchmark

```bash
# change directory
cd cassfiles

# Get the IP address
#
# This depends on your setup: If you have this machine running on a differnet host, you may need to use the IP of the machine instead
# Here is an example of getting it for docker if you are on the same machine
IP_ADDR=`docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' some-cassandra1`
DC=datacenter1

# Setup schema
./nb5 rdwr_keyvalue default.schema thread-count=1 hosts=$IP_ADDR  driverconfig=driverconfig.json  localdc=$DC

# Rampup
./nb5 rdwr_keyvalue default.rampup rampup-cycles=10000000 main-cycles=10000000 cyclerate=60000 thread-count=160 hosts=$IP_ADDR localdc=$DC driverconfig=driverconfig.json  --progress console:1s --report-csv-to casscsv-ramp
```

**Note:** If you get an error such as `WARN  [rampup:037] CoreMotor    attempted to stop motor 154: from non Running state:Errored`, then make sure both of your containers are running and healthy.

### Start collecting the metrics

In a **new** terminal window (as this will loop until you stop it), run:

```bash
python3 poll_metrics.py
```

### Start the benchmark load

The `CYCLERATE` parameter is the main driver of CPU usage.

```bash
cd cassfile
./start_load.sh
```

**Note:** If you are running across multiple machines, alter line 3 of the `IP_address` of `start_load.sh`.

Wait for this to complete. It will take TODO minutes.

### Stop the poll_metrics

Now it is time to stop the CPU trace.  Hit Ctrl-C whereever you were running `poll_metrics.py`, and make sure that you have a file that looks like this:

```bash
cat data/*_perf_event_log.csv
```

```csv
TIMESTAMP,CPU_USAGE_ACTUAL
2024.09.23-00:28:23:847311,0.0062846441947565545
2024.09.23-00:29:26:869317,0.006324667154204469
2024.09.23-00:30:29:919104,0.006529308732144707
```

You will use this file in the next step.

## Phase 2: Autoscaling Algorithm and Tuning

We need 3 things to run the simulator:

- CSVs: You generated this in the last step
- Algorithm: For this example, we'll use the `additive` algorithm, from [DummyAdditiveRecommender.py](https://github.com/microsoft/vasim/blob/main/src/vasim/recommender/DummyAdditiveRecommender.py).
- Metadata: This is included in the `data` folder as `metadata.json`.

### Check the config in metadata.json

Here is an example of some default values.

```bash
cat data/metadata.json
```

Here is the file with some annotations:

```go
{
    "algo_specific_config": {
        "addend": 2 // add 2 cores buffer on top of a moving average.
    },
    "general_config": {
        "recovery_time": 2, // How long to wait after doing an update (after making a change to #cpus)
        "window": 5, // How many minutes of data to feed to the algorithm
        "lag": 1, // How many minutes to wait between runs of the recommender algorithm
        "max_cpu_limit": 5.0, // The max number of cores to recommend
        "min_cpu_limit": 1.0 // The minimum number of cores to recommend
    }
}
```

Ignore any `prediction_config`, this is not used for now.

### Simulate your scenario

If you are using a VM, you will need to port forward to get the webpage to load locally.
```bash
# only if using a remote VM
ssh -L 8501:localhost:8501 your-host
```

Now go to the [../streamlit](https://github.com/microsoft/vasim/tree/main/examples/streamlit) folder in the `examples folder`. Follow the install instructions, then start the webpage:

```bash
streamlit run examples/streamlit/web_demo.py
```



<p align="center">
    <img src="https://raw.githubusercontent.com/microsoft/vasim/refs/heads/kasaur/e2e-livedemo/examples/cassandra/cassfiles/vasim_cass.png" width=600 >
</p>


In the webpage, change the directory path for CSVs to `examples/cassandra/data`.

Now you can experiment with changing the values in the table. Remember for this dummy algorithm, it smooths the CPU values in the window, and adds a buffer.

- Try changing the `algo_specific_config.addend` to 1. This will decrease the "added" buffer size for our dummy recommender algorithm.
- Try changing the `general_config.winow` to larger values. This will provide more data for the smoothing window. But too much data will muddle things.

Currently, tuning the algorithm in the web interface is a work-in-progress.  For now, if you want to try many different parameters, you can refer back to the general [notebook](https://github.com/microsoft/vasim/blob/main/examples/using_vasim.ipynb) and use the `tune_with_strategy` function shown there.

Modify the `metadata.json` file in the `examples/cassandra/data` folder with the parameters you choose.

## Phase 3: Run with the recommender

Now it is time to run everything all together. This will scale the live system!


First start poll_metrics in one terminal:
```bash
python3 poll_metrics.py
```

In another terminal window (as this will loop until you stop it), run:

```bash
python3 run_recommender.py
```

This will start the recommender with the config above and the default algorithm.  It will also drive your algorithm.

Now you can see the output:

TODO
