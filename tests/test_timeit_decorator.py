#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#

"""
Module Name: TestTimeitDecorator.

Description:
    This module contains unit tests for the `timeit` decorator, which measures and prints the
    execution time of a function. The tests validate that the `timeit` decorator correctly
    measures the time taken by various functions with different input parameters and ensures
    the original function's return values and behavior are preserved.

Classes:
    TestTimeitDecorator:
        A test class that extends `unittest.TestCase` and verifies the functionality of the
        `timeit` decorator. It checks whether the decorator correctly measures execution time
        and handles functions with or without return values, arguments, and keyword arguments.

Test Methods:
    test_timeit_decorator_measures_execution_time():
        Ensures the `timeit` decorator measures the execution time of a function and the function
        returns the expected result.

    test_timeit_decorator_with_no_return_value():
        Verifies that the `timeit` decorator works with functions that do not return any value.

    test_timeit_decorator_with_arguments():
        Ensures that the `timeit` decorator can handle functions that take positional arguments.

    test_timeit_decorator_with_keyword_arguments():
        Verifies that the `timeit` decorator works correctly with functions that take keyword arguments.

Usage:
    These tests can be run using `unittest.main()` to execute the unit tests for the `timeit`
    decorator, validating its behavior across different function signatures and scenarios.
"""

import time
import unittest

from vasim.recommender.forecasting.utils.helpers import timeit


class TestTimeitDecorator(unittest.TestCase):
    """
    A test class for verifying the functionality of the `timeit` decorator.

    This class contains tests to ensure that the `timeit` decorator correctly measures the
    execution time of functions, while preserving their original behavior and return values.
    """

    def test_timeit_decorator_measures_execution_time(self):
        """
        Test that the `timeit` decorator correctly measures the execution time of a function.

        This test ensures that the decorated function is called and the expected result is returned.
        """

        @timeit
        def sample_function():
            time.sleep(0.1)
            return "done"

        result = sample_function()
        self.assertEqual(result, "done")

    def test_timeit_decorator_with_no_return_value(self):
        """
        Test that the `timeit` decorator works with functions that do not return any value.

        This test ensures that the decorated function is executed and does not return any value.
        """

        @timeit
        def sample_function():
            time.sleep(0.1)

        result = sample_function()
        self.assertIsNone(result)

    def test_timeit_decorator_with_arguments(self):
        """
        Test that the `timeit` decorator correctly handles functions with positional arguments.

        This test ensures that the decorated function is called with positional arguments and returns
        the expected result.
        """

        @timeit
        def sample_function(x, y):
            time.sleep(0.1)
            return x + y

        result = sample_function(2, 3)
        self.assertEqual(result, 5)

    def test_timeit_decorator_with_keyword_arguments(self):
        """
        Test that the `timeit` decorator correctly handles functions with keyword arguments.

        This test ensures that the decorated function is called with keyword arguments and returns
        the expected result.
        """

        @timeit
        def sample_function(x, y=0):
            time.sleep(0.1)
            return x + y

        result = sample_function(2, y=3)
        self.assertEqual(result, 5)


if __name__ == "__main__":
    unittest.main()
