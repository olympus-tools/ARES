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
from typing import cast

import colorlog

# Context variable for the current workflow element
logger_workflow_element: contextvars.ContextVar[str] = contextvars.ContextVar(
    "workflow_element", default="N/A"
)


class AresLogger(logging.Logger):
    """Logger with ARES-specific configuration metadata."""

    log_dir: Path


class AresContextFilter(logging.Filter):
    """Filter to inject the current workflow element name from contextvars into the log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Injects the current workflow element name into the log record.

        Args:
            record (logging.LogRecord): Log record inherited from calling logger.debug/info/warning/error.

        Returns:
            bool: Always returns True; the injection is valid when executed without exceptions.
        """
        record.workflow_element = logger_workflow_element.get()
        return True


class AresFileHandler(RotatingFileHandler):
    """Rotating file handler that resolves its directory when it writes."""

    def __init__(self, logger_name: str, default_log_dir: Path) -> None:
        """Initialize a delayed handler with the default log file location."""
        self.logger_name = logger_name
        self.default_log_dir = default_log_dir
        default_logfile = default_log_dir / f"{logger_name}.log"
        super().__init__(default_logfile, backupCount=4, maxBytes=4000000, delay=True)

    def emit(self, record: logging.LogRecord) -> None:
        """Write the record below the currently configured root log directory."""
        root_logger = cast(AresLogger, logging.getLogger())
        log_dir = getattr(root_logger, "log_dir", self.default_log_dir)
        logfile = Path(log_dir) / f"{self.logger_name}.log"
        logfile.parent.mkdir(parents=True, exist_ok=True)

        if Path(self.baseFilename) != logfile.resolve():
            self.close()
            self.baseFilename = str(logfile.resolve())

        super().emit(record)


def create_logger(
    name: str | None = None,
    log_dir: Path | None = None,
    level: int = logging.INFO,
) -> AresLogger:
    """Create and configure an ARES logger with console and rotating file handlers.

    Typical usage: ``logger = create_logger()`` or ``logger = create_logger(name=__name__)``.

    Args:
        name (str | None): The name for the logger, typically ``__name__``.
            ``None`` creates or retrieves the root logger. Defaults to None.
        log_dir (Path | None): Directory for log files. Defaults to ``<package>/logs``.
        level (int): The logging level, e.g., ``logging.INFO``. Defaults to ``logging.INFO``.

    Returns:
        logging.Logger: A configured logger instance for ARES.
    """
    root_logger = cast(AresLogger, logging.getLogger())
    default_log_dir = Path(__file__).parent / "../../logs"
    resolved_log_dir = (
        default_log_dir if log_dir is None else Path(log_dir) / "ares_log"
    )

    if name is None:
        logger = root_logger
        logger.setLevel(level)
    else:
        logger = cast(AresLogger, logging.getLogger(name))

    logger.log_dir = resolved_log_dir

    if name is None:
        for registered_logger in logging.Logger.manager.loggerDict.values():
            if isinstance(registered_logger, logging.Logger):
                registered_ares_logger = cast(AresLogger, registered_logger)
                registered_ares_logger.log_dir = resolved_log_dir

    # INFO: Could prevent logs from being propagated to the root logger
    logger.propagate = True

    # Use a StreamHandler to output to stdout --> parallel to streaming to file
    # default: sys.stderr
    stdout_handler = colorlog.StreamHandler(stream=sys.stdout)
    stdout_handler.setLevel(level)
    # Use RotatingFileHandler with Count=4 and 4MB size -> 4 is just a good number + always use logger.INFO
    # INFO: alternatives if project grows: https://betterstack.com/community/guides/logging/how-to-manage-log-files-with-logrotate-on-ubuntu-20-04/
    file_handler = AresFileHandler(
        logger_name="ares_root" if name is None else name,
        default_log_dir=resolved_log_dir,
    )
    file_handler.setLevel(level)

    # Silence third-party DEBUG/INFO records (e.g. numba JIT logs) on all handlers.
    # Filters on handlers intercept propagated records; root-logger filters do not.
    class _ThirdPartyFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            return record.name.startswith("ares") or record.levelno >= logging.WARNING

    third_party_filter = _ThirdPartyFilter()

    # INFO: add contextfilter to custom loggers
    ares_filter = AresContextFilter()
    stdout_handler.addFilter(third_party_filter)
    stdout_handler.addFilter(ares_filter)
    file_handler.addFilter(third_party_filter)
    file_handler.addFilter(ares_filter)

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
