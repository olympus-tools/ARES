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

from typing import Any

import numpy as np

from ares.interface.data.ares_data_interface import AresDataInterface
from ares.interface.data.ares_signal import AresSignal
from ares.interface.parameter.ares_parameter import AresParameter
from ares.interface.parameter.ares_parameter_interface import AresParamInterface


def plugin_example_1(plugin_input: dict[str, Any]):
    """ARES plugin function demonstrating combinatorial parameter and data interface creation.

    This example shows how to create AresDataInterface and AresParamInterface objects
    with proper dependency tracking. All parameter variants are combined with all data
    variants in a cartesian product, creating separate interfaces for each combination.

    Each combination gets its own hash based on the dependencies (parameter hash + data hash),
    allowing the workflow to track which outputs were generated from which input combinations.

    Args:
        plugin_input (dict[str, Any]): Dictionary containing all plugin configuration and data:
            - wf_element_name: str - Name of the workflow element
            - parameter: list[list[AresParamInterface]] - Nested list of parameter interfaces
            - input: list[list[AresDataInterface]] - Nested list of data interfaces
            - plugin_path: str - Path to this plugin file
            - type: str - Element type ("plugin" or "sim_unit")
            - element_workflow: list[str] - Workflow element sequence
    """
    element_parameter_lists: list[list[AresParamInterface]] = plugin_input.get(
        "parameter", []
    )
    element_data_lists: list[list[AresDataInterface]] = plugin_input.get("input", [])

    new_params = [
        AresParameter(
            label="plugin_example_1_parameter",
            value=np.array([1.0]),
            unit="m",
            description="Additional parameter from plugin_example_1",
        )
    ]

    new_signals = [
        AresSignal(
            label="plugin_example_1_signal",
            timestamps=np.array([0.0, 0.1, 0.2, 0.3, 0.4], dtype=np.float32),
            value=np.array([0.0, 1.0, 0.0, -1.0, 0.0]),
            unit="V",
            description="Additional signal from plugin_example_1",
        )
    ]

    for element_parameter_list in element_parameter_lists:
        for element_parameter_obj in element_parameter_list:
            for element_data_list in element_data_lists:
                for element_data_obj in element_data_list:
                    dependencies = [element_parameter_obj.hash, element_data_obj.hash]

                    combined_params = new_params.copy()
                    combined_params.extend(element_parameter_obj.get())
                    AresParamInterface.create(
                        parameters=combined_params, dependencies=dependencies
                    )

                    combined_signals = new_signals.copy()
                    combined_signals.extend(element_data_obj.get())
                    AresDataInterface.create(
                        data=combined_signals,
                        dependencies=dependencies,
                        source_name=plugin_input.get("wf_element_name"),
                    )
