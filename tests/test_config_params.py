#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#
import csv
import json
import os
import shutil
import unittest
from datetime import datetime
from pathlib import Path

from vasim.simulator.InMemorySimulator import InMemoryRunnerSimulator


class TestRunnerSimulatorIntegrationTest(unittest.TestCase):
    """
    This is a true run of simulator end to end.

    It is not a unit test.

    It calls InMemoryRunnerSimulator, which performs a single run of the simulator without tuning.
    """

    def setUp(self):
        root_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        self.source_dir = root_dir / "test_data/alibaba_control_c_29247_denom_1_mini"
        # Here we'll copy the source directory to a target directory, so we can modify the target directory without
        # affecting the source directory
        # Use a unique directory for each worker when using xdist to parallelize tests.
        uid = os.environ.get("PYTEST_XDIST_WORKER", "")
        self.target_dir = root_dir / f"test_data/tmp/{uid}/alibaba_control_c_29247_denom_1_test_to_delete_mini"
        # TODO: sometimes the output is 'simulations', sometimes it is 'tuning'. this is confusing.
        self.target_dir_sim = root_dir / f"test_data/tmp/{uid}/alibaba_control_c_29247_denom_1_test_to_delete_mini_simulations"
        shutil.rmtree(self.target_dir, ignore_errors=True)
        shutil.copytree(self.source_dir, self.target_dir)

    def test_lag_parameter_10(self):
        """
        The lag parameter defines the number of minutes to wait before making a prediction.

        This test checks that the lag parameter is being used correctly.

        We often set it to 10, so we'll start with that.
        """

        # assert file exists
        assert os.path.exists(self.target_dir)

        runner = InMemoryRunnerSimulator(self.target_dir, initial_cpu_limit=14, algorithm="additive")
        results = runner.run_simulation()
        assert results is not None

        # now we need to check the files. There will be a random uuid, so we'll just grab the first folder
        # it will be self.target_dir + (some random uuid) + "_simulations"
        folder = os.listdir(self.target_dir_sim)[0]
        sim_dir = os.path.join(self.target_dir_sim, folder)  # todo add _simulations

        # There should be a decisions.txt file in the simulation directory
        assert os.path.exists(os.path.join(sim_dir, "decisions.txt"))

        # the lag parameter defines the number of minutes to wait before making a prediction
        # So we expect the first decision to be made at 10 minutes
        # and subsequent decisions to be made every 10 minutes. Let's open the decisions.txt file
        # and compare the times to the expected times from the csv.
        with open(os.path.join(sim_dir, "decisions.txt"), "r", encoding="utf-8") as f:
            # TODO rename decisions.txt to be csv. It's not a txt file.
            # We'll read it as a csv file.
            reader = csv.reader(f)
            next(reader)  # skip the header
            # We'll look at the first column of lines 1 and 2, and use a  time diff
            # to assert that they are 10 minutes apart
            first_time = next(reader)[0]
            second_time = next(reader)[0]
            third_time = next(reader)[0]
            # We'll convert the times to datetime objects
            first_time = datetime.strptime(first_time, "%Y-%m-%d %H:%M:%S")
            second_time = datetime.strptime(second_time, "%Y-%m-%d %H:%M:%S")
            # We'll calculate the difference in minutes
            diff = (second_time - first_time).total_seconds() / 60
            # open the metadata file to get the lag parameter
            with open(os.path.join(sim_dir, "metadata.json"), "r", encoding="utf-8") as f:
                metadata = json.load(f)
                lag_read_in = metadata["general_config"]["lag"]
                assert lag_read_in == 10, f"Expected the lag parameter to be 5, but got {lag_read_in}"
            assert diff == lag_read_in, f"Expected the difference lines 1-2 to be {lag_read_in} minutes, but got {diff}"
            # and now we'll check that the third time is 10 minutes after the second time
            third_time = datetime.strptime(third_time, "%Y-%m-%d %H:%M:%S")
            diff = (third_time - second_time).total_seconds() / 60
            assert diff == lag_read_in, f"Expected the difference lines 2-3 to be {lag_read_in} minutes, but got {diff}"

    def test_lag_parameter_5(self):
        """
        The lag parameter defines the number of minutes to wait before making a prediction.

        In the alt config, it is set to 5 minutes. (Usually it is 10 minutes)
        This test checks that the lag parameter is being used correctly.
        """

        # assert file exists
        assert os.path.exists(self.target_dir)

        runner = InMemoryRunnerSimulator(
            self.target_dir,
            initial_cpu_limit=14,
            algorithm="additive",
            config_path=f"{self.target_dir}/metadata_alt_config_lag.json",
        )
        results = runner.run_simulation()
        assert results is not None

        # now we need to check the files. There will be a random uuid, so we'll just grab the first folder
        # it will be self.target_dir + (some random uuid) + "_simulations"
        folder = os.listdir(self.target_dir_sim)[0]
        sim_dir = os.path.join(self.target_dir_sim, folder)  # todo add _simulations

        # There should be a decisions.txt file in the simulation directory
        assert os.path.exists(os.path.join(sim_dir, "decisions.txt"))

        # the lag parameter defines the number of minutes to wait before making a prediction
        # So we expect the first decision to be made at 5 minutes
        # and subsequent decisions to be made every 5 minutes. Let's open the decisions.txt file
        # and compare the times to the expected times from the csv.
        with open(os.path.join(sim_dir, "decisions.txt"), "r", encoding="utf-8") as f:
            # TODO rename decisions.txt to be csv. It's not a txt file.
            # We'll read it as a csv file.
            reader = csv.reader(f)
            next(reader)  # skip the header
            # We'll look at the first column of lines 1 and 2, and use a  time diff
            # to assert that they are 10 minutes apart
            first_time = next(reader)[0]
            second_time = next(reader)[0]
            third_time = next(reader)[0]
            # We'll convert the times to datetime objects
            first_time = datetime.strptime(first_time, "%Y-%m-%d %H:%M:%S")
            second_time = datetime.strptime(second_time, "%Y-%m-%d %H:%M:%S")
            # We'll calculate the difference in minutes
            diff = (second_time - first_time).total_seconds() / 60
            # open the metadata file to get the lag parameter
            with open(os.path.join(sim_dir, "metadata.json"), "r", encoding="utf-8") as f:
                metadata = json.load(f)
                lag_read_in = metadata["general_config"]["lag"]
                assert lag_read_in == 5, f"Expected the lag parameter to be 5, but got {lag_read_in}"
            assert diff == lag_read_in, f"Expected the difference lines 1-2 to be {lag_read_in} minutes, but got {diff}"
            # and now we'll check that the third time is 10 minutes after the second time
            third_time = datetime.strptime(third_time, "%Y-%m-%d %H:%M:%S")
            diff = (third_time - second_time).total_seconds() / 60
            assert diff == lag_read_in, f"Expected the difference lines 2-3 to be {lag_read_in} minutes, but got {diff}"

    def tearDown(self):
        shutil.rmtree(self.target_dir_sim, ignore_errors=True)
        shutil.rmtree(self.target_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
