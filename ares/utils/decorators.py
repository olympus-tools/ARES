r"""
________________________________________________________________________
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

# standard includes
import inspect
import logging
import os
import sys
import traceback
from functools import wraps
from typing import Any, Callable, Type

from ares.utils.logger import create_logger


def safely_run(
    default_return: Any = None,
    exception_msg: str | None = None,
    exception_map: dict[type[Exception], str] | None = None,
    log_level: str = "WARNING",
    log: logging.Logger | None = None,
    include_args: list[str] | None = None,
) -> Callable:
    """provides try/except functionality via decorator

    Args:
        default_return[Any] : default return value in case of failure -> depends on function, default = None
        exception_msg[str] : default logger message to display in case of failure, default = None
        exception_map [dict[Exception,str]] : dictionary with specific error-messages considering the exception, default = None
        log_level[str] : log level to use, default = WARNING
        log[Logger]: specific logger to use, defaults to ares logger
        include_args[list[str]]: function arguments to include in logger message

    Returns:
        Callable: The decorated function with try/except.
    """
    logger = create_logger() if log is None else log

    def wrap(func: Callable) -> Callable:
        @wraps(func)  # preserve original func metadata
        def wrapper(*args, **kwargs):
            logger.debug(f"Safely running function {func.__qualname__} triggered.")
            try:
                ret = func(*args, **kwargs)
                logger.debug(f"Successfully run function {func.__qualname__}.")
            except Exception as e:
                log_func = getattr(logger, log_level.lower(), logger.warning)

                # INFO: execution of func failed -> collect debug information
                log_message = f"{func.__qualname__}: " + (
                    exception_msg
                    if exception_msg is not None
                    else "Something went wrong. Trying to continue... see trace for details.\n"
                )

                if exception_map:
                    for exec_type, specific_msg in exception_map.items():
                        if isinstance(e, exec_type):
                            log_message = specific_msg
                            break

                input_details = ""
                if include_args:
                    try:
                        # Map *args and **kwargs to the function's signature
                        sig = inspect.signature(func)
                        bound_args = sig.bind(*args, **kwargs)
                        bound_args.apply_defaults()  # Include default values if arguments weren't passed

                        # Filter to only the arguments requested in include_args
                        captured = {
                            k: v
                            for k, v in bound_args.arguments.items()
                            if k in include_args
                        }

                        if captured:
                            input_details = f" | Context: {captured}"

                    except Exception as inspect_err:
                        # Safety net: Don't let logging logic crash the app
                        input_details = f" | (Failed to inspect args: {inspect_err})"

                if input_details != "":
                    log_message = f"{log_message} | input-details {input_details}"

                # use traceback to format exception and log it
                full_trace = traceback.format_exc()
                log_func(f"{log_message}Exception trace:\n{full_trace}")

                ret = default_return
            return ret

        return wrapper

    return wrap


def error_msg(
    exception_msg: str,
    exception_type: Type[Exception] | None = None,
    exception_map: dict[type[Exception], str] | None = None,
    log: logging.Logger | None = None,
    include_args: list[str] | None = None,
) -> Callable:
    """
    Wraps a function to provide context to errors without suppressing them.

    If the decorated function raises an exception, this decorator catches it,
    logs the failure, and raises a new exception (chained to the original)
    with the provided context message.

    Args:
        exceptions_msg (str): meaningful error context to display to the user.
        exception_msg (str): meaningful error context to display to the user.
        exception_type (Type[Exception]): The type of error to raise. Defaults to None (original exception is used)
        exception_map [dict[Exception,str]] : dictionary with specific error-messages considering the exception, default = None
        log[Logger]: specific logger to use, defaults to ares logger
        include_args[list[str]]: function arguments to include in logger message

    Returns:
        Callable: The decorated function with try/except.
    """
    logger = create_logger() if log is None else log

    def wrap(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                log_message = exception_msg

                if exception_map:
                    for exec_type, specific_msg in exception_map.items():
                        if isinstance(e, exec_type):
                            log_message = specific_msg
                            break

                input_details = ""
                if include_args:
                    try:
                        # Map *args and **kwargs to the function's signature
                        sig = inspect.signature(func)
                        bound_args = sig.bind(*args, **kwargs)
                        bound_args.apply_defaults()  # Include default values if arguments weren't passed

                        # Filter to only get the arguments requested in include_args
                        captured = {
                            k: v
                            for k, v in bound_args.arguments.items()
                            if k in include_args
                        }

                        if captured:
                            input_details = f" | Context: {captured}"

                    except Exception as inspect_err:
                        input_details = f" | (Failed to inspect args: {inspect_err})"

                if input_details != "":
                    log_message = f"{log_message} | input-details {input_details}"
                logger.exception(log_message)

                if exception_type is not None:
                    raise exception_type(f"{log_message} | original msg:{e}") from e
                raise type(e)(f"{log_message} | original msg:{e}") from e

        return wrapper

    return wrap


def typechecked_dev(func):
    """Applies typeguard's @typechecked only in development mode.

    In production or frozen environments (PyInstaller), this decorator
    does nothing, allowing the code to run without runtime type checking.

    Use ARES_DISABLE_TYPEGUARD=1 to disable type checking explicitly.

    Args:
        func (Callable): The function to decorate.

    Returns:
        Callable: The decorated function (with or without type checking).
    """
    # Check if we're in a frozen (PyInstaller) environment or if explicitly disabled
    is_frozen = getattr(sys, "frozen", False)
    is_disabled = os.environ.get("ARES_DISABLE_TYPEGUARD", "0") == "1"

    if is_frozen or is_disabled:
        # Return function unchanged
        return func
    else:
        # Apply typeguard in development
        from typeguard import typechecked

        return typechecked(func)
