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

from typing import override

from param_dcm.param_dcm import ParamDCM

from ares.interface.parameter.ares_parameter import AresParameter
from ares.interface.parameter.ares_parameter_interface import AresParamInterface
from ares.utils.decorators import safely_run
from ares.utils.decorators import typechecked_dev as typechecked
from ares.utils.logger import create_logger

logger = create_logger(__name__)


class DCMHandler(ParamDCM, AresParamInterface):
    """DCM Parameter interface for ARES ParameterHandler.

    This class extends ParamDCM with ARES-specific interface functionality,
    allowing seamless integration into ARES workflows with flyweight pattern
    based on content hash.

    Implements flyweight pattern via __new__ - identical DCM files
    will automatically return the same cached instance.
    """

    @typechecked
    def __init__(self, file_path: str | None = None, **kwargs):
        """Initialize DCMHandler and optionally load a DCM file.

        Args:
            file_path (str | None): Optional absolute path to the DCM file to load
            **kwargs: Additional arguments (e.g., parameters - not used in DCMHandler)
        """
        AresParamInterface.__init__(self, file_path=file_path, **kwargs)
        ParamDCM.__init__(self, file_path=file_path)

    @override
    @safely_run(
        default_return=None,
        message="Error during saving parameter dcm file.",
        log=logger,
    )
    def _save(self, output_path: str, **kwargs) -> None:
        """Write parameters to DCM file.

        Args:
            output_path (str): Absolute path where the DCM file should be written
            **kwargs: Additional format-specific arguments
        """
        self.write(output_path)
        logger.info(f"Successfully saved DCM parameter file: {output_path}")

    @override
    def add(self, parameters: list[AresParameter], **kwargs) -> None:
        """Add parameters to the DCM interface.

        Converts AresParameter objects to DCM dictionary format and updates
        the internal parameter dictionary. Updates the instance hash after addition.

        Args:
            parameters (list[AresParameter]): List of AresParameter objects to add to the interface
            **kwargs: Additional format-specific arguments (unused)
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
    def get(
        self, label_filter: list[str] | None = None, **kwargs
    ) -> list[AresParameter]:
        """Get parameters from the DCM interface.

        Converts internal DCM parameter dictionary to list of AresParameter objects.
        Uses safe dictionary access to handle missing optional fields.

        Args:
            label_filter (list[str] | None): List of parameter names to retrieve from the interface.
                If None, all parameters are returned. Defaults to None.
            **kwargs: Additional format-specific arguments

        Returns:
            list[AresParameter]: List of AresParameter objects, or empty list on error
        """
        if label_filter:
            items = {k: v for k, v in self.parameter.items() if k in label_filter}
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
