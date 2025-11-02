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

import importlib
import logging
from abc import ABC

from ares.utils.decorators import safely_run
from ares.utils.logger import create_logger

logger = create_logger(__file__)


class AresPlugin(ABC):
    def __init__(self, log: logging.Logger | None = None):
        self.log = log

    def execute(self):
        pass


@safely_run(
    default_return=None, message="Error during loading custom ares-module.", log=logger
)
def load_external_class(
    custom_plugin_import: str, custom_class_name: str
) -> type[AresPlugin] | None:
    # dynamically import module (*.py)
    logger.debug(f"Loading external/custom plugin: {custom_plugin_import}.")
    custom_module = importlib.import_module(custom_plugin_import)

    # import custom class
    logger.debug(f"Loading plugin class {custom_class_name}.")
    custom_class = getattr(custom_module, custom_class_name)

    return custom_class
