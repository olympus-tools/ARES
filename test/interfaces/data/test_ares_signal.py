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

import numpy as np
import pytest

from ares.interface.data.ares_signal import AresSignal


def test_ares_signal_init():
    """
    Test if ares signal can be initialized with data.
    """
    test_signal = AresSignal(
        label="test_signal",
        timestamps=np.array([1, 2, 3, 4], dtype=np.float32),
        value=np.array([1, 2, 3, 4], dtype=np.int64),
    )

    assert test_signal.label == "test_signal"
    assert isinstance(test_signal.timestamps, np.ndarray), (
        "timestamps element of signal is no numpy array."
    )
    assert np.issubdtype(test_signal.timestamps.dtype, np.float32), (
        "timetamps array of signal is not of type float32."
    )
    assert len(test_signal.timestamps) == 4, "Ops, timstamps length is false."
    assert isinstance(test_signal.value, np.ndarray), (
        "data element of signal no numpy array."
    )
    assert np.issubdtype(test_signal.value.dtype, np.int64)
    assert len(test_signal.value) == 4, "Ops, data length is false."


@pytest.mark.parametrize(
    "label, timestamps, data",
    [
        (
            "test_signal1",
            np.zeros((4), dtype=np.float32),
            np.ones((4), dtype=np.float32),
        ),
        (
            "test_signal2",
            np.array([10, 12, 13, 14, 15], dtype=np.float32),
            np.array([1, 2, 3, 4, 5], dtype=np.int32),
        ),
    ],
)
def test_ares_ares_signal(label, timestamps, data):
    """
    Tests different signal types and lengths.
    """
    test_signal = AresSignal(label=label, timestamps=timestamps, value=data)
    data_length = len(timestamps)

    assert test_signal.label == label
    assert isinstance(test_signal.timestamps, np.ndarray), (
        "timestamps element of signal is no numpy array."
    )
    assert np.issubdtype(test_signal.timestamps.dtype, np.float32), (
        "timetamps array of signal is not of type float32."
    )
    assert len(test_signal.timestamps) == data_length, "Ops, timstamps length is false."
    assert isinstance(test_signal.value, np.ndarray), (
        "data element of signal no numpy array."
    )
    assert len(test_signal.value) == data_length, "Ops, data length is false."


def test_ares_signal_resample():
    """
    Test the resample method of the ares signal.
    """
    test_signal = AresSignal(
        label="test_signal",
        timestamps=np.array([0, 1, 2, 3], dtype=np.float32),
        value=np.array([0, 1, 2, 3], dtype=np.float32),
    )
    resampled_timestamps = np.array([0.5, 1.5, 2.5], dtype=np.float32)
    test_signal.resample(resampled_timestamps)
    expected_data = np.array([0.5, 1.5, 2.5], dtype=np.float32)
    assert np.array_equal(test_signal.timestamps, resampled_timestamps)
    assert np.array_equal(test_signal.value, expected_data)


def test_ares_signal_wrong_timestamps_type():
    """
    Test if TypeError is raised for wrong timestamps type.
    """
    with pytest.raises(TypeError):
        AresSignal(
            label="test_signal",
            timestamps=np.array([1, 2, 3, 4], dtype=int),
            value=np.array([1, 2, 3, 4], dtype=np.float32),
        )


def test_ares_signal_wrong_dimension():
    """
    Test if ValueError is raised for wrong dimension.
    """
    with pytest.raises(ValueError):
        AresSignal(
            label="test_signal",
            timestamps=np.array([[1, 2], [3, 4]], dtype=np.float32),
            value=np.array([1, 2, 3, 4], dtype=np.float32),
        )
    with pytest.raises(ValueError):
        AresSignal(
            label="test_signal",
            timestamps=np.array([1, 2, 3, 4], dtype=np.float32),
            value=np.array([[1, 2], [3, 4]], dtype=np.float32),
        )


if __name__ == "__main__":
    test_ares_signal_resample()
