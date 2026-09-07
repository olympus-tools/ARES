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

import logging
from pathlib import Path

import pytest

from ares.utils.logger import AresFileHandler, create_logger


def test_logger_instance():
    """
    Tests if create_logger returns a valid logger instance.
    """
    logger = create_logger("test_logger_instance")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_logger_instance"
    assert logger.level == logging.NOTSET


@pytest.mark.parametrize(
    "level, message, expected_in_output",
    [
        (logging.DEBUG, "debug message", True),
        (logging.INFO, "info message", True),
        (logging.WARNING, "warning message", True),
        (logging.ERROR, "error message", True),
        (logging.CRITICAL, "critical message", True),
    ],
)
def test_log_levels_capture(caplog, level, message, expected_in_output):
    """
    Tests that messages are logged correctly at different levels.
    """
    caplog.clear()
    logger = create_logger("test_log_levels", level=logging.DEBUG)
    with caplog.at_level(level):
        logger.log(level, message)

    if expected_in_output:
        assert message in caplog.text
    else:
        assert message not in caplog.text


def test_log_level_is_respected(caplog):
    """
    Tests that the logger's level is respected and lower level messages are ignored.
    """
    caplog.clear()
    caplog.set_level(logging.WARNING)
    logger = create_logger("test_log_level_respect", level=logging.WARNING)

    # This message should NOT be captured because its level (INFO) is below WARNING
    logger.info("This is an info message.")
    assert "This is an info message." not in caplog.text

    # This message SHOULD be captured
    logger.warning("This is a warning message.")
    assert "This is a warning message." in caplog.text


def test_logfile_creation():
    """
    Tests if the logger creates a log file.
    """
    log_name = "test_logfile_creation"
    logger = create_logger(log_name)
    logger.setLevel(logging.INFO)
    logger.warning(
        "This is an test message to create the corresponding logfile for testing."
    )
    log_dir = Path(__file__).parent.parent.parent / "logs"
    logfile = log_dir / f"{log_name}.log"
    assert logfile.exists()
    # Clean up the created log file
    logfile.unlink()


def test_existing_logger_uses_root_log_dir(tmp_path):
    """Tests that existing loggers receive the root logger directory."""
    logger = create_logger("test_existing_logger_uses_root_log_dir")
    root_logger = create_logger(log_dir=tmp_path)

    assert logger.log_dir == root_logger.log_dir
    assert all(isinstance(handler, AresFileHandler) for handler in logger.handlers)


def test_log_dir_is_not_created_before_logging(tmp_path):
    """Tests that a log directory is created only when a record is written."""
    log_dir = tmp_path / "ares_log"
    create_logger(log_dir=tmp_path)
    logger = create_logger("test_lazy_log_dir")

    assert not log_dir.exists()

    logger.warning("Create the log directory on first write.")

    assert (log_dir / "test_lazy_log_dir.log").exists()


if __name__ == "__main__":
    test_logfile_creation()
