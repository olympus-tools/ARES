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

import re

from ares.utils.decorators import typechecked_dev as typechecked
from ares.utils.logger import create_logger

logger = create_logger(__name__)


@typechecked
def resolve_label_filter(
    label_filter: list[str],
    available_elements: list[str],
) -> list[str]:
    """Resolve regex-pattern in "label_filter". Function is a general approach for all ares interaces (e.g. data/parameter).

    Args:
        label_filter (list[str]): List of element names/search pattern to retrieve.
        available_elements (list [str]): List of available elements (parameter/signals/etc.) to use given label_filter on.

    Returns:
        list[str]: List of element names to extract from interace.
    """
    result_list: list[str] = []
    for regex in label_filter:
        pattern = re.compile(regex)
        found_labels = [
            element for element in available_elements if pattern.search(element)
        ]
        if not found_labels:
            logger.warning(
                f"Label filter '{regex}' did not match any entry in available elements."
            )
        result_list.extend(found_labels)

    return list(set(result_list))
