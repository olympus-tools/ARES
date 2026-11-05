r"""
________________________________________________________________________
|                                                                      |
|               $$$$$$\  $$$$$$$\  $$$$$$$$\  $$$$$$\                  |
|              $$  __$$\ $$ |  $$ |$$  _____|$$ /  \__|                |
|              $$ /  $$ |$$ |  $$ |$$ |      $$\   $$ |                |
|              $$$$$$$$ |$$$$$$$  |$$$$$\    \$$$$$$\                  |
|              $$  __$$ |$$  __$$< $$  __|    \____$$\                 |
|              $$ |  $$ |$$ |  $$ |$$ |      $$\   $$ |                |
|              $$$$$$$$ |$$$$$$$  |$$$$$$$$\ \$$$$$$  |                |
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

    https://www.apache.org/licenses/LICENSE-2.0
"""

import logging

import numpy as np

from ares.interface.data.ares_signal import AresSignal
from ares.utils.select_signals_by_source_priority import (
    select_signals_by_source_priority,
)


# TEST: select_signals_by_source_priority
def test_select_signals_by_source_priority_uses_pipeline_order():
    """Tests that the first source passed by the pipeline has highest priority."""
    signals = [
        AresSignal(
            label="vehicle_speed",
            source="secondary",
            timestamps=np.array([0.0]),
            value=np.array([10.0]),
        ),
        AresSignal(
            label="engine_speed",
            source="primary",
            timestamps=np.array([0.0]),
            value=np.array([20.0]),
        ),
        AresSignal(
            label="vehicle_speed",
            source="primary",
            timestamps=np.array([0.0]),
            value=np.array([30.0]),
        ),
    ]

    selected = select_signals_by_source_priority(
        sim_data=signals,
        source_priority=["secondary", "primary"],
    )

    assert [(signal.label, signal.source) for signal in selected] == [
        ("vehicle_speed", "secondary"),
        ("engine_speed", "primary"),
    ]


def test_select_signals_by_source_priority_warns_and_uses_first_unmatched_source(
    caplog,
):
    """Tests that unmatched duplicate labels warn and retain the first candidate."""
    signals = [
        AresSignal(
            label="vehicle_speed",
            source="unlisted_a",
            timestamps=np.array([0.0]),
            value=np.array([10.0]),
        ),
        AresSignal(
            label="vehicle_speed",
            source="unlisted_b",
            timestamps=np.array([0.0]),
            value=np.array([20.0]),
        ),
    ]

    with caplog.at_level(logging.WARNING):
        selected = select_signals_by_source_priority(
            sim_data=signals,
            source_priority=["secondary", "primary"],
        )

    assert selected == [signals[0]]
    assert "vehicle_speed" in caplog.text
    assert "unlisted_a" in caplog.text
    assert "unlisted_b" in caplog.text
    assert "Using the first signal from source 'unlisted_a'" in caplog.text


def test_select_signals_by_source_priority_keeps_unique_unmatched_signal():
    """Tests that a unique signal is retained even when its source is unlisted."""
    signal = AresSignal(
        label="vehicle_speed",
        source="unlisted",
        timestamps=np.array([0.0]),
        value=np.array([10.0]),
    )

    selected = select_signals_by_source_priority(
        sim_data=[signal],
        source_priority=["secondary", "primary"],
    )

    assert selected == [signal]


def test_select_signals_by_source_priority_falls_back_without_pipeline_sources(
    caplog,
):
    """Tests that duplicate labels fall back when the source priority is empty."""
    signals = [
        AresSignal(
            label="vehicle_speed",
            source="source_a",
            timestamps=np.array([0.0]),
            value=np.array([10.0]),
        ),
        AresSignal(
            label="vehicle_speed",
            source="source_b",
            timestamps=np.array([0.0]),
            value=np.array([20.0]),
        ),
    ]

    with caplog.at_level(logging.WARNING):
        selected = select_signals_by_source_priority(signals, [])

    assert selected == [signals[0]]
    assert "source_a" in caplog.text
    assert "source_b" in caplog.text
