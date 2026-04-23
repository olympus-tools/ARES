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

Copyright 2025 olympus-tools contributors. Dependencies and licenses
are listed in the NOTICE file:

    https://github.com/olympus-tools/ARES/blob/master/NOTICE

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License:

    https://github.com/olympus-tools/ARES/blob/master/LICENSE
"""
# TODO:use: https://pypi.org/project/python-json-logger/ -> ?

import contextvars
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

import colorlog

# Context variable for the current workflow element
logger_workflow_element: contextvars.ContextVar[str] = contextvars.ContextVar(
    "workflow_element", default="N/A"
)


class AresContextFilter(logging.Filter):
    """
    Filter to inject the current workflow element name from contextvars into the log record.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Function to mutate logger record to contain workflow_element name.
        Args:
            record (LogRecord) : LogRecord element inherited through calling logger.debug/info/warning/error.
        Returns:
            True: function returns always True, injection is valid when it runs without exceptions.
        """
        record.workflow_element = logger_workflow_element.get()
        return True


def create_logger(
    name: str | None = None,
    logdir: Path | None = None,
    level: int = logging.INFO,
) -> logging.Logger:
    """
    Creates and configures a logger that outputs logs in JSON format.
    Usage should be to call just: "logger = create_logger()"

    Args:
        name (str | None), default = None: The name for the logger, typically __name__. None creates the root logger.
        logdir (Path | None): Directory for log files. Defaults to <package>/logs.
        level (int), default = logging.INFO: The logging level, e.g., logging.INFO.

    Returns:
        logging.Logger: A configured logger instance for ARES.
    """
    if logdir is None:
        logdir = Path(__file__).parent / "../../logs"
    else:
        logdir = Path(logdir) / "ares_log"

    logdir.mkdir(parents=True, exist_ok=True)

    if name is None:
        logger = logging.getLogger()
        logfile = Path(logdir, "ares_root.log")
        logger.setLevel(level)
    else:
        logger = logging.getLogger(name)
        logfile = Path(logdir, f"{name}.log")

    logger.addFilter(AresContextFilter())

    # INFO: Could prevent logs from being propagated to the root logger
    logger.propagate = True

    # Use a StreamHandler to output to stdout --> parallel to streaming to file
    # default: sys.stderr
    stdout_handler = colorlog.StreamHandler(stream=sys.stdout)
    stdout_handler.setLevel(level)
    # Use RotatingFileHandler with Count=4 and 4MB size -> 4 is just a good number + always use logger.INFO
    # INFO: alternatives if project grows: https://betterstack.com/community/guides/logging/how-to-manage-log-files-with-logrotate-on-ubuntu-20-04/
    file_handler = RotatingFileHandler(logfile, backupCount=4, maxBytes=4000000)
    file_handler.setLevel(level)

    fmt_plain = "%(levelname)-8s | %(asctime)s | %(workflow_element)s | %(filename)s:%(lineno)s >> %(message)s"
    fmt_color = "%(log_color)s" + fmt_plain
    datefmt = "%d.%m.%Y %H:%M:%S"

    color_formatter = colorlog.ColoredFormatter(
        fmt=fmt_color,
        datefmt=datefmt,
        reset=True,
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_black",
        },
        secondary_log_colors={},
        style="%",
    )

    file_formatter = logging.Formatter(
        fmt=fmt_plain,
        datefmt=datefmt,
    )

    stdout_handler.setFormatter(color_formatter)
    file_handler.setFormatter(file_formatter)

    if name is None:
        logger.addHandler(stdout_handler)

    logger.addHandler(file_handler)

    return logger
