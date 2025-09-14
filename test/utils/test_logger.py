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

import logging
from pathlib import Path

import pytest

from ares.utils.logger import create_logger


def test_logger_instance():
    """
    Tests if create_logger returns a valid logger instance.
    """
    logger = create_logger("test_logger_instance")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_logger_instance"
    assert logger.level == logging.NOTSET
    # assert len(logger.handlers) == 2


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
    logger.info(
        "This is an test message to create the corresponding logfile for testing."
    )
    logdir = Path(__file__).parent.parent.parent / "logs"
    logfile = logdir / f"{log_name}.log"
    assert logfile.exists()
    # Clean up the created log file
    logfile.unlink()


if __name__ == "__main__":
    test_logfile_creation()
