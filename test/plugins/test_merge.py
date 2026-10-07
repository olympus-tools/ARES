r"""
________________________________________________________________________
|                                                                      |
|               $$$$$$\  $$$$$$$\  $$$$$$$$\  $$$$$$                  |
|              $$  __$$\ $$ |  $$ |$$  _____|$$  __$$\                 |
|              $$ /  $$ |$$ |  $$ |$$ |      $$ /  \__|                |
|              $$$$$$$$ |$$$$$$$  |$$$$$    \$$$$$$\                  |
|              $$  __$$ |$$  __$$< $$  __|    \____$$\                 |
|              $$ |  $$ |$$ |  $$ |$$ |      $$\   $$ |                |
|              $$$$$$$$\ \$$$$$$  |$$$$$$$$\ \$$$$$$  |                |
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

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import numpy as np

from ares.interface.data.ares_signal import AresSignal
from ares.interface.parameter.ares_parameter import AresParameter
from ares.plugins.merge import (
    ares_plugin,
    get_all_hash_combinations,
    get_common_source_hash_combinations,
)
from ares.pydantic_models.workflow_model import MergeMode


def test_get_all_hash_combinations_returns_cartesian_product():
    """Tests that ALL mode combinations contain every Cartesian product entry."""
    assert get_all_hash_combinations([["a", "b"], ["1", "2"]]) == [
        ["a", "1"],
        ["a", "2"],
        ["b", "1"],
        ["b", "2"],
    ]


def test_get_all_hash_combinations_returns_empty_for_no_inputs():
    """Tests that no merge inputs produce no combinations."""
    assert get_all_hash_combinations([]) == []


def test_get_common_source_hash_combinations_skips_missing_and_deduplicates():
    """Tests that common-source combinations skip missing hashes and duplicates."""
    source = MagicMock()
    source.get_origin_hashes.return_value = {"origin"}
    derived = MagicMock()
    derived.get_origin_hashes.return_value = {"origin"}
    cache = {"source": source, "derived": derived}

    combinations = get_common_source_hash_combinations(
        [["source", "missing"], ["derived"]], cache
    )

    assert combinations == [["source", "derived"]]


def test_ares_plugin_all_mode_creates_parameter_and_data_outputs():
    """Tests that ALL mode merges every selected parameter and data combination."""
    parameter = AresParameter(label="p", value=np.array([1.0]))
    signal = AresSignal(
        label="s",
        timestamps=np.array([0.0]),
        value=np.array([1.0]),
    )
    parameter_source = MagicMock()
    parameter_source.get.return_value = [parameter]
    data_source = MagicMock()
    data_source.stepsize = None
    data_source.get.return_value = [signal]
    plugin_input = SimpleNamespace(
        hash_lists_parameter=[["parameter"]],
        hash_lists_data=[["data"]],
        merge_mode=MergeMode.ALL,
        label_filter_parameter=None,
        transpose_parameter=None,
        label_filter_data=None,
        vstack_pattern_data=None,
        stepsize=None,
        resample_method=None,
        resample_tolerance=None,
    )

    with (
        patch(
            "ares.plugins.merge.AresParamInterface.cache",
            {"parameter": parameter_source},
        ),
        patch("ares.plugins.merge.AresDataInterface.cache", {"data": data_source}),
        patch("ares.plugins.merge.AresParamInterface.create") as create_parameter,
        patch("ares.plugins.merge.AresDataInterface.create") as create_data,
    ):
        ares_plugin(plugin_input)

    create_parameter.assert_called_once()
    create_data.assert_called_once()


def test_ares_plugin_common_source_mode_uses_common_source_helpers():
    """Tests that non-ALL mode delegates combination selection to common-source helpers."""
    plugin_input = SimpleNamespace(
        hash_lists_parameter=[["parameter"]],
        hash_lists_data=[["data"]],
        merge_mode=MergeMode.COMMON_SOURCE,
        label_filter_parameter=None,
        transpose_parameter=None,
        label_filter_data=None,
        vstack_pattern_data=None,
        stepsize=None,
        resample_method=None,
        resample_tolerance=None,
    )

    with (
        patch(
            "ares.plugins.merge.get_common_source_hash_combinations", return_value=[]
        ) as get_common,
        patch("ares.plugins.merge.get_all_hash_combinations") as get_all,
    ):
        ares_plugin(plugin_input)

    assert get_common.call_count == 2
    get_all.assert_not_called()
