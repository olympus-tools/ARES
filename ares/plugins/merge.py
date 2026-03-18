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

from itertools import product

from ares.interface.data.ares_data_interface import AresDataInterface
from ares.interface.data.ares_signal import AresSignal
from ares.interface.parameter.ares_parameter import AresParameter
from ares.interface.parameter.ares_parameter_interface import AresParamInterface
from ares.utils.logger import create_logger

logger = create_logger(__name__)


def get_hash_combinations(
    hash_lists: list[list[str]],
) -> list[list[str]]:
    """Generate all hash combinations from cartesian product of hash lists.

    Args:
        hash_lists (list[list[str]]): List of lists containing hash strings.

    Returns:
        list[list[str]]: List of hash combinations, where each combination is a list of hashes.
    """
    if not hash_lists:
        return []

    hash_combinations = []
    for hash_combination in product(*hash_lists):
        hash_combinations.append(list(hash_combination))

    return hash_combinations


def ares_plugin(plugin_input):
    """ARES plugin that merges multiple ARES outputs into a single output.

    Args:
        plugin_input (dict): Dictionary containing all plugin configuration and data.
            wf_element_name (str): Name of the workflow element.
            parameter_hash_list (list[list[str]]): List of parameter hash combinations for plugin input.
            data_hash_list (list[list[str]]): List of data hash combinations for plugin input.
            ...: Other fields from WorkflowElement as needed.

    Returns:
        None
    """

    parameter_hash_lists: list[list[str]] = plugin_input.get("parameter_hash_lists", [])
    data_hash_lists: list[list[str]] = plugin_input.get("data_hash_lists", [])

    # generate all hash combinations using cartesian product
    parameter_dependency_lists = get_hash_combinations(parameter_hash_lists)
    data_dependency_lists = get_hash_combinations(data_hash_lists)

    # create merged parameters and data for each hash combination
    for parameter_dependency_list in parameter_dependency_lists:
        logger.debug(
            "Merging parameters for each hash combination."
        )  # TODO: offering a better log message

        merge_parameters: list[AresParameter] = []
        for parameter_hash in parameter_dependency_list:
            params = AresParamInterface.cache[parameter_hash].get(
                label_filter=plugin_input.get("label_filter_parameter"),
            )
            if params is not None:
                merge_parameters.extend(params)

        AresParamInterface.create(
            parameters=merge_parameters,
            dependencies=parameter_dependency_list,
            label_filter=plugin_input.get("label_filter_parameter"),
        )

    # create merged data for each hash combination
    for data_dependency_list in data_dependency_lists:
        logger.debug(
            "Merging data for each hash combination."
        )  # TODO: offering a better log message

        merge_data: list[AresSignal] = []
        for data_hash in data_dependency_list:
            data = AresDataInterface.cache[data_hash].get(
                stepsize=plugin_input.get("stepsize"),
                label_filter=plugin_input.get("label_filter_data"),
                vstack_pattern=plugin_input.get("vstack_pattern_data"),
            )
            if data is not None:
                merge_data.extend(data)

        AresDataInterface.create(
            data=merge_data,
            dependencies=data_dependency_list,
            source_name=plugin_input.get("wf_element_name"),
            stepsize=plugin_input.get("stepsize"),
            label_filter=plugin_input.get("label_filter_data"),
            vstack_pattern=plugin_input.get("vstack_pattern_data"),
        )
