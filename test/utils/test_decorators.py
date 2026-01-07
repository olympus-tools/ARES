r"""
_______________________________________________________________________
|                                                                      |
|               $$$$$$\  $$$$$$$\  $$$$$$$$\  $$$$$$\                  |
|              $$  __$$\ $$  __$$\ $$  _____|$$  __$$\                 |
|              $$ /  $$ |$$ |  $$ |$$ |      $$ /  \__|                |
|              $$$$$$$$ |$$$$$$$  |$$$$$\    \$$$$$$\                  |
|              $$  __$$ |$$  __$$< $$  __|    \____$$\                 |
|              $$ |  $$ |$$ |  $$ |$$ |      $$\   $$ |                |
|              $$ |  $$ |$$ |  $$ |$$$$$$$$\ \$$$$$$  |                |
|              \__|  \__|\__|  \__|\________| \______/                 |
|                                                                      |
|              Automated Rapid Embedded Simulation (c)                 |
|______________________________________________________________________|

Copyright 2025 Andrä Carotta

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

For details, see: https://github.com/olympus-tools/ARES#7-license
"""

import logging

import pytest

from ares.utils.decorators import error_msg, safely_run


# TEST: safely_run
def test_safely_run_success():
    """
    Tests that the decorated function returns the correct value when it runs successfully.
    """

    @safely_run(default_return="error")
    def safely_run_success():
        return "success"

    assert safely_run_success() == "success"


def test_safely_run_exception():
    """
    Tests that the decorated function returns the default_return value when it raises an exception.
    """

    @safely_run(default_return="error")
    def safely_run_exception():
        raise ValueError("This is a test exception")

    assert safely_run_exception() == "error"


def test_safely_run_logging(caplog):
    """
    Tests that a message is logged when the decorated function raises an exception.
    """

    @safely_run(default_return="error", message="HELP WANTED")
    def safely_run_logging():
        raise ValueError("This is a test exception")

    safely_run_logging()
    assert (
        "Error while running function safely_run_logging: This is a test exception"
        in caplog.text
    )
    assert "HELP WANTED" in caplog.text


@pytest.mark.parametrize(
    "test_log_level", ["INFO", "WARNING", "ERROR", "CRITICAL", "BOOM"]
)
def test_safely_run_logging(caplog, test_log_level):
    """
    Tests that the decorator respects the requested log_level (e.g., WARNING).
    """
    caplog.set_level(logging.INFO)

    @safely_run(default_return="error", log_level=test_log_level)
    def safely_run_logging():
        raise ValueError("This is a test exception")

    safely_run_logging()

    assert len(caplog.records) > 0
    if test_log_level != "BOOM":
        assert caplog.records[-1].levelname == test_log_level
    else:
        assert caplog.records[-1].levelname == "WARNING"


def test_safely_run_with_args():
    """
    Tests that the decorator works with functions that have arguments and keyword arguments.
    """

    @safely_run(default_return="error")
    def safely_run_with_args(a, b, c="d"):
        return f"{a}-{b}-{c}"

    assert safely_run_with_args("a", "b") == "a-b-d"
    assert safely_run_with_args("a", "b", c="e") == "a-b-e"


def test_safely_run_with_args_exception():
    """
    Tests that the decorator works with functions that have arguments and keyword arguments and raises an exception.
    """

    @safely_run(default_return="error")
    def safely_run_with_args_exception(a, b, c="d"):
        raise ValueError("This is a test exception - ARES")

    assert safely_run_with_args_exception("a", "b") == "error"
    assert safely_run_with_args_exception("a", "b", c="e") == "error"


# TEST: error_msg
def test_happy_path_execution():
    """Ensure the function runs normally when no error occurs."""

    @error_msg("This should not trigger")
    def add(a, b):
        return a + b

    assert add(2, 3) == 5


def test_argument_passing():
    """Ensure args and kwargs are passed correctly to the wrapped function."""

    @error_msg("Args failed")
    def greet(name, greeting="Hello"):
        return f"{greeting}, {name}"

    assert greet("Ares", greeting="Hi") == "Hi, Ares"


def test_catches_and_reraises_with_context():
    """
    Ensure the decorator catches the error, wraps it in the custom message,
    and raises the default exception type (RuntimeError).
    """

    @error_msg("Critical failure in database")
    def fail_function():
        raise ValueError("Connection refused")

    # verify the TYPE of error raised is RuntimeError (default)
    with pytest.raises(RuntimeError) as exc_info:
        fail_function()

    # verify the MESSAGE contains both our context and the original error
    msg = str(exc_info.value)
    assert "Critical failure in database" in msg
    assert "Original exception trace: Connection refused" in msg


def test_exception_chaining_is_preserved():
    """
    Ensure 'raise ... from e' is used. This allows debuggers to see
    the original traceback.
    """
    original_error = ZeroDivisionError("Math is hard")

    @error_msg("Calculation failed")
    def divide():
        raise original_error

    with pytest.raises(RuntimeError) as exc_info:
        divide()

    # The __cause__ attribute stores the original exception when using 'from'
    assert exc_info.value.__cause__ is original_error


def test_custom_exception_type():
    """Ensure the user can specify a specific exception class to raise."""

    class MyCustomError(Exception):
        pass

    @error_msg("Custom error context", exception_type=MyCustomError)
    def fail_custom():
        raise KeyError("missing_key")

    with pytest.raises(MyCustomError):
        fail_custom()


def test_metadata_preservation():
    """Ensure @wraps is working (docstrings and function names are kept)."""

    @error_msg("Metadata context")
    def meaningful_name():
        """This is a docstring."""
        pass

    assert meaningful_name.__name__ == "meaningful_name"
    assert meaningful_name.__doc__ == "This is a docstring."
