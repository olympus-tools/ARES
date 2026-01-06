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
import os
import sys
from functools import wraps

from ares.utils.logger import create_logger


def safely_run(
    default_return=None, message: str = None, log_level: str = None, log=None
):
    """provides try/except functionality via decorator

    Args:
        default_return (Any): default return value in case of failure -> depends on function
        message (str | None): logger message to display in case of failure
        log_level (str | None): log level to use
        log (Any): specific logger to use, defaults to ares logger
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
                # INFO: execution of func failed -> collect debug information
                logger.error(f"Error while running function {func.__name__}: {e}")

                # set default return
                ret = default_return
            return ret

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
