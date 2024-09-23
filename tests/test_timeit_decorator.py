#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#
import time
import unittest

from vasim.recommender.forecasting.utils.helpers import timeit


class TestTimeitDecorator(unittest.TestCase):

    def test_timeit_decorator_measures_execution_time(self):
        @timeit
        def sample_function():
            time.sleep(0.1)
            return "done"

        result = sample_function()
        self.assertEqual(result, "done")

    def test_timeit_decorator_with_no_return_value(self):
        @timeit
        def sample_function():
            time.sleep(0.1)

        result = sample_function()
        self.assertIsNone(result)

    def test_timeit_decorator_with_arguments(self):
        @timeit
        def sample_function(x, y):
            time.sleep(0.1)
            return x + y

        result = sample_function(2, 3)
        self.assertEqual(result, 5)

    def test_timeit_decorator_with_keyword_arguments(self):
        @timeit
        def sample_function(x, y=0):
            time.sleep(0.1)
            return x + y

        result = sample_function(2, y=3)
        self.assertEqual(result, 5)


if __name__ == "__main__":
    unittest.main()
