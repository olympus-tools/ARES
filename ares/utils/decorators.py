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

# standard includes
from functools import wraps

# ares includes
from ares.utils.logger import create_logger


def safely_run(
    default_return=None, message: str = None, log_level: str = None, log=None
):
    """provides try/except functionality via decorator

    Args:
        default_return : default return value in case of failure -> depends on function
        message[str] : logger message to display in case of failure
        log_level[str] : log level to use
        log: specific logger to use, defaults to ares logger
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
