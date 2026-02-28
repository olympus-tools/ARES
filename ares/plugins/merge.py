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

from ares.interface.data.ares_data_interface import AresDataInterface
from ares.interface.parameter.ares_parameter_interface import AresParamInterface
from ares.utils.logger import create_logger

logger = create_logger(__name__)


def ares_plugin(plugin_input):
    """ARES plugin that merges multiple ARES outputs into a single output.

    Args:
        plugin_input (dict): A dictionary containing the following keys:
            - "inputs" (list): A list of input file paths to be merged.
            - "output" (str): The output file path for the merged result.

    Returns:
        None
    """

    if plugin_input["input"]:
        element_lists: (
            list[list[AresParamInterface]] | list[list[AresDataInterface]]
        ) = plugin_input.get("input", None)
    elif plugin_input["parameter"]:
        element_lists: (
            list[list[AresParamInterface]] | list[list[AresDataInterface]]
        ) = plugin_input.get("parameter", None)

    # determine type of merge based on first element in first element-list
    if isinstance(element_lists[0][0], AresDataInterface):
        logger.info("Merging ares data-elements...")
        master_element = AresDataInterface.create()
    elif isinstance(element_lists[0][0], AresParamInterface):
        logger.info("Merging ares parameter-elements...")
        master_element = AresParamInterface.create()
    else:
        raise ValueError(
            f"Type {type(element_lists[0][0])} of merge-element is currently not supported."
        )

    for element_list in element_lists:
        for element in element_list:
            master_element.add(element.get())
