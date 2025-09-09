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

# Copyright (c) 2025 Andrä Carotta
#
# Licensed under the MIT License. See the LICENSE file for details.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# You may obtain a copy of the License at
# https://github.com/AndraeCarotta/ares/blob/master/LICENSE

"""
# TODO:use: https://pypi.org/project/python-json-logger/ -> ?

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

import colorlog


def create_logger(name: str = "", level: int = logging.INFO) -> logging.Logger:
    """
    Creates and configures a logger that outputs logs in JSON format.
    Usage should be to call just: "logger = create_logger()"

    Args:
        name (str), default = 'ares_root': The name for the logger, typically __name__.
        level (int), default = logging.INFO: The logging level, e.g., logging.INFO.

    Returns:
        logging.Logger: A configured logger instance for ARES.
    """
    # create/get logdir: "logs"
    logdir = Path(__file__).parent / "../../logs"
    logdir.mkdir(parents=True, exist_ok=True)
    logfile = Path(logdir, f"{name}.log")
    # create logger -> root or "name"
    if name == "":
        logger = logging.getLogger()
        logfile = Path(logdir, "ares_root.log")
    else:
        logger = logging.getLogger(name)
        logfile = Path(logdir, f"{name}.log")

    # set loglevel
    logger.setLevel(level)

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

    # set color formatter for stdout/stderr and formatter for files -> no color support
    color_formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(levelname)s | %(asctime)s | %(filename)s%(lineno)s >> %(message)s",
        datefmt="%H:%M:%S",
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

    # formatter for files
    file_formatter = logging.Formatter(
        fmt="%(levelname)s | %(asctime)s | %(filename)s%(lineno)s >> %(message)s",
        datefmt="%H:%M:%S",
    )

    stdout_handler.setFormatter(color_formatter)
    file_handler.setFormatter(file_formatter)
    # set handler
    logger.addHandler(stdout_handler)
    logger.addHandler(file_handler)

    return logger
