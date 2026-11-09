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

from collections.abc import Mapping
from itertools import product
from typing import Any, cast

from ares.interface.data.ares_data_interface import AresDataInterface
from ares.interface.data.ares_signal import AresSignal
from ares.interface.parameter.ares_parameter import AresParameter
from ares.interface.parameter.ares_parameter_interface import AresParamInterface
from ares.pydantic_models.workflow_model import MergeElement, MergeMode
from ares.utils.decorators import typechecked_dev as typechecked
from ares.utils.logger import create_logger

logger = create_logger(name=__name__)


@typechecked
def select_elements_for_merge(
    elements: list[AresSignal | AresParameter],
    existing_elements: list[AresSignal | AresParameter],
    allow_duplicates: bool | None,
) -> list[AresSignal | AresParameter]:
    """Return merge elements according to the duplicate-label configuration.

    Args:
        elements (list[AresSignal | AresParameter]): Signals or parameters to merge.
        existing_elements (list[AresSignal | AresParameter]): Signals or parameters
            already merged.
        allow_duplicates (bool | None): Whether elements with existing labels are
            allowed.

    Returns:
        list[AresSignal | AresParameter]: Original elements when duplicates are
            allowed; otherwise elements with new labels, preserving input order.
    """
    if allow_duplicates is False:
        existing_labels = {element.label for element in existing_elements}
        return [element for element in elements if element.label not in existing_labels]
    else:
        return elements


def get_all_hash_combinations(
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


def get_common_source_hash_combinations(
    hash_lists: list[list[str]],
    cache: Mapping[str, AresParamInterface] | Mapping[str, AresDataInterface],
) -> list[list[str]]:
    """Generate combinations whose hashes share a common source hash.

    Args:
        hash_lists (list[list[str]]): Hashes grouped by merge input.
        cache (Mapping[str, AresParamInterface] | Mapping[str, AresDataInterface]):
            Cache for the interface type being merged.

    Returns:
        list[list[str]]: Unique combinations from at least two merge inputs that
            share an origin hash.
    """
    origin_candidates: dict[str, dict[int, list[str]]] = {}
    for input_index, hash_list in enumerate(hash_lists):
        for hash in hash_list:
            instance = cache.get(hash)
            if instance is None:
                continue
            # TODO: Consolidate both interfaces into a shared interface class in a
            # dedicated ticket (get_origin_hashes) and remove this temporary Any cast.
            origin_hashes = instance.get_origin_hashes(cache=cast(Any, cache))
            for origin_hash in origin_hashes:
                candidates_by_input = origin_candidates.setdefault(origin_hash, {})
                candidates_for_input = candidates_by_input.setdefault(input_index, [])
                candidates_for_input.append(hash)

    combinations: list[list[str]] = []
    for candidates_by_input in origin_candidates.values():
        if len(candidates_by_input) < 2:
            continue

        input_candidates = [
            candidates_by_input[input_index]
            for input_index in sorted(candidates_by_input)
        ]
        for combination in product(*input_candidates):
            combination_list = list(combination)
            if combination_list not in combinations:
                combinations.append(combination_list)

    return combinations


def ares_plugin(plugin_input: MergeElement):
    """ARES plugin that merges multiple ARES outputs into a single combined output.

    Generates all cartesian-product combinations of the input parameter and data
    hash lists, merges each combination into a single :class:`AresParamInterface`
    and :class:`AresDataInterface` instance, and stores the results in the
    respective caches.

    Args:
        plugin_input (MergeElement): Pydantic model containing all plugin configuration
            and data, including ``hash_lists_parameter``, ``hash_lists_data``,
            ``label_filter_parameter``, ``label_filter_data``, and related fields.
    """

    hash_lists_parameter: list[list[str]] = plugin_input.hash_lists_parameter
    hash_lists_data: list[list[str]] = plugin_input.hash_lists_data

    if plugin_input.merge_mode == MergeMode.ALL:
        parameter_dependency_lists = get_all_hash_combinations(hash_lists_parameter)
        data_dependency_lists = get_all_hash_combinations(hash_lists_data)
    else:
        parameter_dependency_lists = get_common_source_hash_combinations(
            hash_lists_parameter, AresParamInterface.cache
        )
        data_dependency_lists = get_common_source_hash_combinations(
            hash_lists_data, AresDataInterface.cache
        )

    logger.info(
        "Merging with the following configuration: "
        f"  Parameter combinations: {len(parameter_dependency_lists)} "
        f"  Data combinations: {len(data_dependency_lists)} "
        f"  Merge mode: {plugin_input.merge_mode} "
        f"  Allow duplicate parameters: {plugin_input.allow_duplicates_parameter} "
        f"  Allow duplicate data: {plugin_input.allow_duplicates_data}"
    )

    # create merged parameters and data for each hash combination
    for parameter_dependency_list in parameter_dependency_lists:
        logger.debug(
            "Merging parameters for each hash combination."
        )  # TODO: offering a better log message

        merge_parameters: list[AresParameter] = []
        for parameter_hash in reversed(parameter_dependency_list):
            parameters = AresParamInterface.cache[parameter_hash].get(
                label_filter=plugin_input.label_filter_parameter,
                transpose=plugin_input.transpose_parameter,
            )
            if parameters is not None:
                parameters_cleared = select_elements_for_merge(
                    elements=parameters,
                    existing_elements=merge_parameters,
                    allow_duplicates=plugin_input.allow_duplicates_parameter,
                )

                merge_parameters.extend(parameters_cleared)

        AresParamInterface.create(
            parameters=merge_parameters,
            dependencies=parameter_dependency_list,
            label_filter=plugin_input.label_filter_parameter,
            transpose=plugin_input.transpose_parameter,
        )

    # create merged data for each hash combination
    for data_dependency_list in data_dependency_lists:
        logger.debug(
            "Merging data for each hash combination."
        )  # TODO: offering a better log message

        merge_data: list[AresSignal] = []

        # this loop is necessary to ensure that the merged data has a unified time array
        stepsize: int = 1 if plugin_input.stepsize is None else plugin_input.stepsize
        for data_hash in data_dependency_list:
            if (
                AresDataInterface.cache[data_hash].stepsize is not None
                and AresDataInterface.cache[data_hash].stepsize < stepsize
            ):
                stepsize = AresDataInterface.cache[data_hash].stepsize

        for data_hash in reversed(data_dependency_list):
            data = AresDataInterface.cache[data_hash].get(
                stepsize=stepsize,
                label_filter=plugin_input.label_filter_data,
                vstack_pattern=plugin_input.vstack_pattern_data,
                resample_method=plugin_input.resample_method,
                resample_tolerance=plugin_input.resample_tolerance,
            )
            if data is not None:
                data_cleared = select_elements_for_merge(
                    elements=data,
                    existing_elements=merge_data,
                    allow_duplicates=plugin_input.allow_duplicates_data,
                )

                merge_data.extend(data_cleared)

        AresDataInterface.create(
            data=merge_data,
            dependencies=data_dependency_list,
            stepsize=stepsize,
            label_filter=plugin_input.label_filter_data,
            vstack_pattern=plugin_input.vstack_pattern_data,
            resample_method=plugin_input.resample_method,
            resample_tolerance=plugin_input.resample_tolerance,
        )
