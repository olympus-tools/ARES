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

Copyright 2025 olympus-tools contributors. Contributors to this project
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

from pathlib import Path
from typing import override

from param_dcm.param_dcm import ParamDCM

from ares.interface.parameter.ares_parameter import AresParameter
from ares.interface.parameter.ares_parameter_interface import AresParamInterface
from ares.utils.decorators import error_msg, safely_run
from ares.utils.decorators import typechecked_dev as typechecked
from ares.utils.logger import create_logger

logger = create_logger(__name__)


class DCMHandler(ParamDCM, AresParamInterface):
    """DCM Parameter interface for ARES ParameterHandler.

    This class extends ParamDCM with ARES-specific interface functionality,
    allowing seamless integration into ARES workflows with flyweight pattern
    based on content hash.

    Implements flyweight pattern via __new__ - identical dcm files
    will automatically return the same cached instance.
    """

    @typechecked
    def __init__(self, file_path: Path | None = None, **kwargs):
        """Initialize DCMHandler and optionally load a dcm file.

        Args:
            file_path (Path | None): Optional absolute path to the dcm file to load
            **kwargs: Additional arguments (e.g., parameters - not used in DCMHandler)
        """
        AresParamInterface.__init__(self, file_path=file_path, **kwargs)
        ParamDCM.__init__(self, file_path=file_path)

    @override
    @safely_run(
        default_return=None,
        exception_msg="For some reason the .dcm file could not be saved.",
        log=logger,
        include_args=["output_path"],
    )
    @typechecked
    def _save(self, output_path: Path, **kwargs) -> None:
        """Write parameters to dcm file.

        Args:
            output_path (str): Absolute path where the dcm file should be written
            **kwargs: Additional format-specific arguments
        """
        self.write(output_path)
        logger.info(f"Successfully saved dcm parameter file: {output_path}")

    @override
    @error_msg(
        exception_msg="Error in dcm-handler add function.",
        log=logger,
        include_args=["parameters"],
    )
    @typechecked
    def add(self, parameters: list[AresParameter], **kwargs) -> None:
        """Add parameters to the dcm interface.

        Converts AresParameter objects to dcm dictionary format and updates
        the internal parameter dictionary. Updates the instance hash after addition.

        Args:
            parameters (list[AresParameter]): List of AresParameter objects to add to the interface
            **kwargs: Additional format-specific arguments (unused)
        """
        for param in parameters:
            self.parameter[param.label] = {
                "description": param.description,
                "name_breakpoints_1": param.name_breakpoints_1,
                "name_breakpoints_2": param.name_breakpoints_2,
                "unit": param.unit,
                "value": param.value.tolist(),
            }

    @override
    @error_msg(
        exception_msg="Error in dcm-handler get function.",
        log=logger,
        include_args=["label_filter"],
    )
    @typechecked
    def get(
        self, label_filter: list[str] | None = None, **kwargs
    ) -> list[AresParameter] | None:
        """Get parameters from the dcm interface.

        Converts internal dcm parameter dictionary to list of AresParameter objects.
        Uses safe dictionary access to handle missing optional fields.

        Args:
            label_filter (list[str] | None): List of parameter names to retrieve from the interface.
                If None, all parameters are returned. Defaults to None.
            **kwargs: Additional format-specific arguments

        Returns:
            list[AresParameter] | None: List of AresParameter objects, or None if no parameters were found
        """
        if label_filter:
            items = {}
            for label in label_filter:
                if label in self.parameter:
                    items[label] = self.parameter[label]
                    logger.debug(f"Parameter '{label}' found in DCM parameter file.")
                else:
                    logger.warning(
                        f"Parameter '{label}' not found in DCM parameter file."
                    )
        else:
            items = self.parameter

        result = [
            AresParameter(
                label=parameter_name,
                value=parameter_value.get("value", 0.0),
                name_breakpoints_1=parameter_value.get("name_breakpoints_1", None),
                name_breakpoints_2=parameter_value.get("name_breakpoints_2", None),
                description=parameter_value.get("description", None),
                unit=parameter_value.get("unit", None),
            )
            for parameter_name, parameter_value in items.items()
        ]

        return result if result else None
