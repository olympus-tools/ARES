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
import pytest

from ares.interface.data.ares_data_interface import AresDataInterface
from ares.interface.data.ares_signal import AresSignal
from ares.interface.data.mf4_handler import MF4Handler
from ares.interface.parameter.ares_parameter import AresParameter
from ares.interface.parameter.ares_parameter_interface import AresParamInterface
from ares.interface.parameter.jsonparam_handler import JSONParamHandler
from ares.plugins.merge import (
    ares_plugin,
    get_all_hash_combinations,
    get_common_source_hash_combinations,
    select_elements_for_merge,
)
from ares.pydantic_models.workflow_model import MergeMode


def test_select_elements_for_merge_replaces_existing_signals_with_later_ones():
    """Tests that later signals replace already merged signals with the same label."""
    existing = [
        AresSignal(
            label="speed",
            timestamps=np.array([0.0]),
            value=np.array([1.0]),
        )
    ]
    elements = [
        AresSignal(
            label="speed",
            timestamps=np.array([0.0]),
            value=np.array([2.0]),
        ),
        AresSignal(
            label="temperature",
            timestamps=np.array([0.0]),
            value=np.array([20.0]),
        ),
    ]

    result = select_elements_for_merge(elements, existing, allow_duplicates=False)

    assert result == elements


def test_select_elements_for_merge_replaces_parameters_and_preserves_order():
    """Tests parameter replacement while preserving order and in-input duplicates."""
    existing = [
        AresParameter(label="gain", value=np.array([1.0])),
        AresParameter(label="limit", value=np.array([5.0])),
    ]
    elements = [
        AresParameter(label="offset", value=np.array([2.0])),
        AresParameter(label="gain", value=np.array([3.0])),
        AresParameter(label="offset", value=np.array([4.0])),
    ]

    result = select_elements_for_merge(elements, existing, allow_duplicates=False)

    assert result == [existing[1], *elements]


@pytest.mark.parametrize("allow_duplicates", [None, True])
def test_select_elements_for_merge_keeps_duplicates(allow_duplicates):
    """Tests that unset and true options append all elements in input order."""
    existing = [AresParameter(label="gain", value=np.array([1.0]))]
    elements = [AresParameter(label="gain", value=np.array([2.0]))]

    result = select_elements_for_merge(
        elements, existing, allow_duplicates=allow_duplicates
    )

    assert result == [*existing, *elements]


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
        allow_duplicates_data=False,
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


@pytest.mark.parametrize(
    "allow_duplicates, expected_signal_count",
    [(None, 2), (False, 1), (True, 2)],
)
def test_ares_plugin_handles_duplicate_options(allow_duplicates, expected_signal_count):
    """Tests that signal duplicates follow the option while parameters are always
    unique with the later merge input winning."""
    parameters = [
        AresParameter(label="p", value=np.array([1.0])),
        AresParameter(label="p", value=np.array([2.0])),
    ]
    signals = [
        AresSignal(
            label="s",
            timestamps=np.array([0.0]),
            value=np.array([1.0]),
        ),
        AresSignal(
            label="s",
            timestamps=np.array([0.0]),
            value=np.array([2.0]),
        ),
    ]
    parameter_sources = {
        "parameter_1": MagicMock(get=MagicMock(return_value=[parameters[0]])),
        "parameter_2": MagicMock(get=MagicMock(return_value=[parameters[1]])),
    }
    data_sources = {
        "data_1": MagicMock(stepsize=None, get=MagicMock(return_value=[signals[0]])),
        "data_2": MagicMock(stepsize=None, get=MagicMock(return_value=[signals[1]])),
    }
    plugin_input = SimpleNamespace(
        hash_lists_parameter=[["parameter_1"], ["parameter_2"]],
        hash_lists_data=[["data_1"], ["data_2"]],
        merge_mode=MergeMode.ALL,
        allow_duplicates_data=allow_duplicates,
        label_filter_parameter=None,
        transpose_parameter=None,
        label_filter_data=None,
        vstack_pattern_data=None,
        stepsize=None,
        resample_method=None,
        resample_tolerance=None,
    )

    with (
        patch("ares.plugins.merge.AresParamInterface.cache", parameter_sources),
        patch("ares.plugins.merge.AresDataInterface.cache", data_sources),
        patch("ares.plugins.merge.AresParamInterface.create") as create_parameter,
        patch("ares.plugins.merge.AresDataInterface.create") as create_data,
    ):
        ares_plugin(plugin_input)

    merged_parameters = create_parameter.call_args.kwargs["parameters"]
    assert len(merged_parameters) == 1
    assert merged_parameters[0].value.tolist() == [2.0]

    merged_signals = create_data.call_args.kwargs["data"]
    assert len(merged_signals) == expected_signal_count
    # the later merge input must always be the last (winning) occurrence
    assert merged_signals[-1].value.tolist() == [2.0]


@pytest.mark.parametrize(
    "allow_duplicates, expected_sources",
    [(None, ["earlier", "later"]), (True, ["earlier", "later"]), (False, ["later"])],
)
def test_ares_plugin_merged_data_object_respects_duplicate_options(
    allow_duplicates, expected_sources
):
    """Tests the real merged MF4 object: duplicates are kept unless disabled, and
    the later merge input wins when duplicates are disabled."""
    timestamps = np.array([0.0, 0.01], dtype=np.float32)
    earlier = AresSignal(
        label="s",
        timestamps=timestamps,
        value=np.array([1.0, 1.0], dtype=np.float32),
        source="earlier",
    )
    later = AresSignal(
        label="s",
        timestamps=timestamps,
        value=np.array([2.0, 2.0], dtype=np.float32),
        source="later",
    )
    data_cache = {
        "data_1": MagicMock(stepsize=None, get=MagicMock(return_value=[earlier])),
        "data_2": MagicMock(stepsize=None, get=MagicMock(return_value=[later])),
    }
    plugin_input = SimpleNamespace(
        hash_lists_parameter=[],
        hash_lists_data=[["data_1"], ["data_2"]],
        merge_mode=MergeMode.ALL,
        allow_duplicates_data=allow_duplicates,
        label_filter_parameter=None,
        transpose_parameter=None,
        label_filter_data=None,
        vstack_pattern_data=None,
        stepsize=None,
        resample_method=None,
        resample_tolerance=None,
    )

    with (
        patch("ares.plugins.merge.AresDataInterface.cache", data_cache),
        patch.dict(AresDataInterface._handlers, {".mf4": MF4Handler}),
    ):
        ares_plugin(plugin_input)
        merged_objects = [
            obj for key, obj in data_cache.items() if key not in ("data_1", "data_2")
        ]

    assert len(merged_objects) == 1
    merged_signals = merged_objects[0].get(label_filter=["^s$"])
    assert sorted(signal.source for signal in merged_signals) == expected_sources
    if allow_duplicates is False:
        # merged object is resampled to the merge stepsize, so only compare values
        assert set(merged_signals[0].value.tolist()) == {2.0}


def test_ares_plugin_common_source_mode_uses_common_source_helpers():
    """Tests that non-ALL mode delegates combination selection to common-source helpers."""
    plugin_input = SimpleNamespace(
        hash_lists_parameter=[["parameter"]],
        hash_lists_data=[["data"]],
        merge_mode=MergeMode.COMMON_SOURCE,
        allow_duplicates_data=False,
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


def _plugin_input(hash_lists_parameter, hash_lists_data):
    """Builds a merge plugin input without label filters or resampling."""
    return SimpleNamespace(
        hash_lists_parameter=hash_lists_parameter,
        hash_lists_data=hash_lists_data,
        merge_mode=MergeMode.ALL,
        allow_duplicates_data=False,
        label_filter_parameter=None,
        transpose_parameter=None,
        label_filter_data=None,
        vstack_pattern_data=None,
        stepsize=None,
        resample_method=None,
        resample_tolerance=None,
    )


@pytest.mark.parametrize(
    "reused_input, parameters_a, parameters_b",
    [
        # later input fully overrides the earlier one -> result equals input B
        ("b", [("p", 1.0)], [("p", 2.0)]),
        # later input adds nothing new -> result equals input A (pass-through)
        ("a", [("p", 1.0), ("q", 2.0)], [("q", 2.0)]),
    ],
)
def test_ares_plugin_parameter_merge_preserves_ancestry_of_reused_input(
    reused_input, parameters_a, parameters_b
):
    """Tests that a merge result equal to an input reuses the cached instance
    without rewriting its dependencies, so origin hashes stay valid."""
    with (
        patch.dict(AresParamInterface.cache, clear=True),
        patch.dict(AresParamInterface._handlers, {".json": JSONParamHandler}),
    ):
        instance_a = AresParamInterface.create(
            parameters=[
                AresParameter(
                    label=label,
                    value=np.array([value]),
                    source="ARES_DEFAULT_SOURCE",
                )
                for label, value in parameters_a
            ]
        )
        instance_b = AresParamInterface.create(
            parameters=[
                AresParameter(
                    label=label,
                    value=np.array([value]),
                    source="ARES_DEFAULT_SOURCE",
                )
                for label, value in parameters_b
            ]
        )
        inputs = {"a": instance_a, "b": instance_b}

        ares_plugin(_plugin_input([[instance_a.hash], [instance_b.hash]], []))

        reused = inputs[reused_input]
        assert set(AresParamInterface.cache) == {instance_a.hash, instance_b.hash}
        assert reused.dependencies == []
        assert reused.get_origin_hashes(AresParamInterface.cache) == {reused.hash}
        assert get_common_source_hash_combinations(
            [[reused.hash], [reused.hash]], AresParamInterface.cache
        ) == [[reused.hash, reused.hash]]


def test_ares_plugin_data_merge_preserves_ancestry_of_reused_input():
    """Tests that a data merge equal to an input keeps the input's dependencies."""
    timestamps = np.array([0.0, 0.01], dtype=np.float32)

    def signal(label, value):
        return AresSignal(
            label=label,
            timestamps=timestamps,
            value=np.array([value, value], dtype=np.float32),
            source="ARES_DEFAULT_SOURCE",
        )

    with (
        patch.dict(AresDataInterface.cache, clear=True),
        patch.dict(AresDataInterface._handlers, {".mf4": MF4Handler}),
    ):
        instance_a = AresDataInterface.create(data=[signal("s", 1.0)])
        instance_b = AresDataInterface.create(data=[signal("s", 2.0)])

        ares_plugin(_plugin_input([], [[instance_a.hash], [instance_b.hash]]))

        # the merge result equals input B, so no new instance may be created
        assert set(AresDataInterface.cache) == {instance_a.hash, instance_b.hash}
        assert instance_a.dependencies == []
        assert instance_b.dependencies == []
        assert instance_b.get_origin_hashes(AresDataInterface.cache) == {
            instance_b.hash
        }
