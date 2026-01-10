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
import logging
import os
import sys
from functools import wraps
from typing import Any, Type

from ares.utils.logger import create_logger


def safely_run(
    default_return: Any = None,
    message: str | None = None,
    exception_map: dict[type[Exception], str] | None = None,
    log_level: str = "WARNING",
    log: logging.Logger | None = None,
):
    """provides try/except functionality via decorator

    Args:
        default_return[Any] : default return value in case of failure -> depends on function, default = None
        message[str] : default logger message to display in case of failure, default = None
        exception_map [dict[Exception,str]] : dictionary with specific error-messages considering the exception, default = None
        log_level[str] : log level to use, default = WARNING
        log[Logger]: specific logger to use, defaults to ares logger

    Returns:
        Callable: The decorated function with try/except.
    """
    logger = create_logger() if log is None else log

    def wrap(func):
        @wraps(func)  # preserve original func metadata
        def wrapper(*args, **kwargs):
            logger.debug(f"Safely running function {func.__name__} triggered.")
            try:
                ret = func(*args, **kwargs)
                logger.debug(f"Successfully run function {func.__name__}.")
            except Exception as e:
                log_func = getattr(logger, log_level.lower(), logger.warning)

                # INFO: execution of func failed -> collect debug information
                log_message = (
                    message
                    if message is not None
                    else f"Error while running function {func.__name__}"
                )

                if exception_map:
                    for exec_type, specific_msg in exception_map.items():
                        if isinstance(e, exec_type):
                            log_message = specific_msg
                            break

                log_func(f"{log_message}: {e}")

                ret = default_return
            return ret

        return wrapper

    return wrap


def error_msg(
    message: str,
    exception_type: Type[Exception] = RuntimeError,
    log: logging.Logger | None = None,
):
    """
    Wraps a function to provide context to errors without suppressing them.

    If the decorated function raises an exception, this decorator catches it,
    logs the failure, and raises a new exception (chained to the original)
    with the provided context message.

    Args:
        message (str): meaningful error context to display to the user.
        exception_type (Type[Exception]): The type of error to raise. Defaults to RuntimeError.
        log[Logger]: specific logger to use, defaults to ares logger

    Returns:
        Callable: The decorated function with try/except.
    """
    logger = create_logger() if log is None else log

    def wrap(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                full_error_msg = f"{message} | Original exception trace: {str(e)}"

                logger.error(full_error_msg)
                raise exception_type(full_error_msg) from e

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
