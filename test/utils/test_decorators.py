"""
Tests for the decorators functions.
"""

from ares.utils.decorators import safely_run


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

    @safely_run(default_return="error", message="An error occurred")
    def safely_run_logging():
        raise ValueError("This is a test exception")

    safely_run_logging()
    assert (
        "Error while running function safely_run_logging: This is a test exception"
        in caplog.text
    )


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

