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

import json
from typing import Any, override

from ares.interface.parameter.ares_parameter import AresParameter
from ares.interface.parameter.ares_parameter_interface import AresParamInterface
from ares.utils.decorators import safely_run
from ares.utils.decorators import typechecked_dev as typechecked
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
        file_path: str | None = None,
        **kwargs,
    ):
        """Initialize JSONParamHandler from file or parameter list.

        Args:
            file_path (str | None): Optional absolute path to the JSON file to load
            **kwargs (Any): Additional arguments.
                - parameters (list[AresParameter]): Optional list of AresParameter objects to initialize with
        """
        super().__init__(file_path=file_path, **kwargs)
        self.parameter: dict[str, dict[str, Any]] = {}

        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.parameter = json.load(f)
            except Exception as e:
                logger.warning(
                    f"Error initializing JSONParamHandler with {file_path}: {e}"
                )
        elif "parameters" in kwargs:
            self.add(kwargs["parameters"])

    @override
    @safely_run(
        default_return=None,
        exception_msg="Error during saving parameter json file.",
        log=logger,
        include_args=["output_path"],
    )
    @typechecked
    def _save(self, output_path: str, **kwargs) -> None:
        """Write parameters to JSON file.

        Args:
            output_path (str): Absolute path where the JSON file should be written
            **kwargs (Any): Additional format-specific arguments
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

    @override
    @typechecked
    def add(self, parameters: list[AresParameter], **kwargs) -> None:
        """Add parameters to the JSON interface.

        Converts AresParameter objects to JSON dictionary format and updates
        the internal parameter dictionary. Updates the instance hash after addition.

        Args:
            parameters (list[AresParameter]): List of AresParameter objects to add to the interface
            **kwargs (Any): Additional format-specific arguments (unused)
        """
        for param in parameters:
            self.parameter[param.label] = {
                "description": param.description
                if param.description is not None
                else "",
                "unit": param.unit if param.unit is not None else "",
                "value": param.value.tolist(),
            }

    @override
    @typechecked
    def get(
        self, label_filter: list[str] | None = None, **kwargs
    ) -> list[AresParameter] | None:
        """Get parameters from the JSON interface.

        Converts internal JSON parameter dictionary to list of AresParameter objects.
        Uses safe dictionary access to handle missing optional fields.

        Args:
            label_filter (list[str] | None): List of parameter names to retrieve from the interface.
                If None, all parameters are returned. Defaults to None.
            **kwargs (Any): Additional format-specific arguments

        Returns:
            list[AresParameter] | None: List of AresParameter objects, or None if no parameters were found
        """
        if label_filter:
            items = {k: v for k, v in self.parameter.items() if k in label_filter}
        else:
            items = self.parameter

        result = [
            AresParameter(
                label=parameter_name,
                value=parameter_value.get("value", 0.0),
                description=parameter_value.get("description", "n/m"),
                unit=parameter_value.get("unit", "n/m"),
            )
            for parameter_name, parameter_value in items.items()
        ]

        return result if result else None
