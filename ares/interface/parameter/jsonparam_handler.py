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

import json
from typing import Any, Dict, List, Optional

from typeguard import typechecked

from ares.interface.parameter.ares_parameter import AresParameter
from ares.interface.parameter.ares_parameter_interface import AresParamInterface
from ares.utils.logger import create_logger

logger = create_logger(__name__)


class JSONParamHandler(AresParamInterface):
    """JSON AresParameter interface for ARES ParameterHandler.

    This class provides ARES-specific interface functionality for JSON parameter files,
    allowing seamless integration into ARES workflows with flyweight pattern
    based on content hash.

    Implements flyweight pattern via __new__ - identical JSON files
    will automatically return the same cached instance.
    """

    @typechecked
    def __init__(
        self,
        file_path: Optional[str] = None,
        **kwargs,
    ):
        """Initialize JSONParamHandler from file or parameter list.

        Args:
            file_path: Optional absolute path to the JSON file to load
            parameters: Optional list of AresParameter objects to initialize with
        """
        super().__init__(**kwargs)
        self.parameter: Dict[str, Dict[str, Any]] = {}

        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.parameter = json.load(f)
            except Exception as e:
                logger.warning(
                    f"Error initializing JSONParamHandler with {file_path}: {e}"
                )
        elif "parameters" in kwargs:
            try:
                self.add(kwargs["parameters"])
            except Exception as e:
                logger.warning(
                    f"Error initializing JSONParamHandler with parameters: {e}"
                )

    @typechecked
    def _save(self, output_path: str, **kwargs) -> None:
        """Write parameters to JSON file.

        Args:
            output_path: Absolute path where the JSON file should be written
            **kwargs: Additional format-specific arguments
                - indent (int): Number of spaces for indentation (default: 2)
                - ensure_ascii (bool): Escape non-ASCII characters (default: False)
        """
        try:
            indent = kwargs.get("indent", 2)
            ensure_ascii = kwargs.get("ensure_ascii", False)

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(
                    self.parameter,
                    f,
                    indent=indent,
                    ensure_ascii=ensure_ascii,
                    sort_keys=True,
                )
        except Exception as e:
            logger.error(f"Error saving parameters to {output_path}: {e}")
            return None

    @typechecked
    def add(self, parameters: List[AresParameter], **kwargs) -> None:
        """Add parameters to the JSON interface.

        Converts AresParameter objects to JSON dictionary format and updates
        the internal parameter dictionary. Updates the instance hash after addition.

        Args:
            parameters: List of AresParameter objects to add to the interface
            **kwargs: Additional format-specific arguments (unused)
        """
        try:
            for param in parameters:
                self.parameter[param.label] = {
                    "description": param.description
                    if param.description is not None
                    else "",
                    "unit": param.unit if param.unit is not None else "",
                    "value": param.value.tolist(),
                }
        except Exception as e:
            logger.error(f"Error adding parameters: {e}")

    @typechecked
    def get(self, **kwargs) -> List[AresParameter]:
        """Get parameters from the JSON interface.

        Converts internal JSON parameter dictionary to list of AresParameter objects.
        Uses safe dictionary access to handle missing optional fields.

        Args:
            **kwargs: Additional format-specific arguments
                - filter_labels (List[str]): Optional list of labels to filter

        Returns:
            List[AresParameter]: List of AresParameter objects, or empty list on error
        """
        try:
            filter_labels = kwargs.get("filter_labels", None)

            if filter_labels:
                items = {k: v for k, v in self.parameter.items() if k in filter_labels}
            else:
                items = self.parameter

            return [
                AresParameter(
                    label=parameter_name,
                    value=parameter_value.get("value", 0.0),
                    description=parameter_value.get("description", "n/m"),
                    unit=parameter_value.get("unit", "n/m"),
                )
                for parameter_name, parameter_value in items.items()
            ]
        except Exception as e:
            logger.error(f"Error getting parameters: {e}")
            return []
