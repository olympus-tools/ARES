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


def test_ares_signal_fs():
    """
    Test the fs property of the ares signal.
    """
    test_signal = AresSignal(
        label="test_signal",
        timestamps=np.array([0, 1, 2, 3], dtype=np.float32),
        value=np.array([0, 1, 2, 3], dtype=np.float32),
    )
    assert isinstance(test_signal.fs, int)
    assert test_signal.fs == 1


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


def test_ares_signal_resample_default():
    """
    Test the resample method in general.
    """
    test_signal = AresSignal(
        label="test_signal",
        timestamps=np.array([0, 1, 2, 3], dtype=np.float32),
        value=np.array([0, 1, 2, 3], dtype=np.float32),
    )
    original_timestamps = test_signal.timestamps.copy()
    original_values = test_signal.value.copy()

    resampled_timestamps = np.array([0.5, 1.5, 2.5], dtype=np.float32)
    signal_resampled = test_signal.resample(resampled_timestamps)

    assert signal_resampled is not None
    assert signal_resampled is not test_signal
    assert np.array_equal(signal_resampled.timestamps, resampled_timestamps)
    assert signal_resampled.value.shape == resampled_timestamps.shape

    assert np.array_equal(test_signal.timestamps, original_timestamps)
    assert np.array_equal(test_signal.value, original_values)


def test_ares_signal_resample_linear():
    """
    Test linear resampling of the ares signal.
    """
    test_signal = AresSignal(
        label="test_signal",
        timestamps=np.array([0, 1, 2, 3], dtype=np.float32),
        value=np.array([0, 1, 2, 3], dtype=np.float32),
    )
    original_timestamps = test_signal.timestamps.copy()
    original_values = test_signal.value.copy()

    resampled_timestamps = np.array([0.5, 1.5, 2.5], dtype=np.float32)
    signal_resampled = test_signal.resample(resampled_timestamps, method="linear")

    assert signal_resampled is not None
    assert signal_resampled is not test_signal

    expected_data = np.array([0.5, 1.5, 2.5], dtype=np.float32)
    assert np.array_equal(signal_resampled.timestamps, resampled_timestamps)
    assert np.array_equal(signal_resampled.value, expected_data)

    assert np.array_equal(test_signal.timestamps, original_timestamps)
    assert np.array_equal(test_signal.value, original_values)


def test_ares_signal_resample_windowedsinc():
    """
    Test windowed-sinc resampling of the ares signal.
    """
    test_signal = AresSignal(
        label="test_signal",
        timestamps=np.array([0, 1, 2, 3], dtype=np.float32),
        value=np.array([0, 1, 2, 3], dtype=np.float32),
    )
    original_timestamps = test_signal.timestamps.copy()
    original_values = test_signal.value.copy()

    resampled_timestamps = np.array([0.5, 1.5, 2.5], dtype=np.float32)
    signal_resampled = test_signal.resample(resampled_timestamps, method="windowedsinc")

    assert signal_resampled is not None
    assert signal_resampled is not test_signal
    assert np.array_equal(signal_resampled.timestamps, resampled_timestamps)

    assert np.array_equal(test_signal.timestamps, original_timestamps)
    assert np.array_equal(test_signal.value, original_values)


def test_ares_signal_resample_windowedsinc_sine():
    """
    Test windowed-sinc resampling with a sine wave (bandlimited signal).
    """
    fs = 100.0
    t = np.arange(0, 5, 1 / fs, dtype=np.float32)
    freq = 5.0
    sine = np.sin(2 * np.pi * freq * t).astype(np.float32)

    test_signal = AresSignal(
        label="sine",
        timestamps=t,
        value=sine,
    )

    resampled_t = np.arange(0.0, 5, 1 / (fs * 2), dtype=np.float32)
    signal_resampled = test_signal.resample(resampled_t, method="windowedsinc")

    assert signal_resampled is not None
    expected = np.sin(2 * np.pi * freq * resampled_t).astype(np.float32)
    assert np.allclose(signal_resampled.value, expected, atol=1e-1)


def test_ares_signal_resample_cubic():
    """
    Test cubic resampling method of the ares signal.
    """
    test_signal = AresSignal(
        label="test_signal",
        timestamps=np.array([0, 1, 2, 3], dtype=np.float32),
        value=np.array([0, 1, 2, 3], dtype=np.float32),
    )
    original_timestamps = test_signal.timestamps.copy()
    original_values = test_signal.value.copy()

    resampled_timestamps = np.array([0.5, 1.5, 2.5], dtype=np.float32)
    signal_resampled = test_signal.resample(resampled_timestamps, method="cubic")

    assert signal_resampled is not None
    assert signal_resampled is not test_signal
    assert np.array_equal(signal_resampled.timestamps, resampled_timestamps)
    assert np.allclose(signal_resampled.value, np.array([0.5, 1.5, 2.5]))

    assert np.array_equal(test_signal.timestamps, original_timestamps)
    assert np.array_equal(test_signal.value, original_values)


def _make_multidim_signal(n_timestamps=10, n_channels=3):
    """Helper to create a multi-dimensional signal with known values."""
    timestamps = np.arange(n_timestamps, dtype=np.float32)
    values = np.arange(n_timestamps * n_channels, dtype=np.float32).reshape(
        n_timestamps, n_channels
    )
    return AresSignal(label="multidim", timestamps=timestamps, value=values)


def test_ares_signal_resample_linear_multidim():
    """
    Test linear resampling preserves shape for multi-dimensional signals.
    """
    test_signal = _make_multidim_signal(10, 3)

    resampled_timestamps = np.array([0.5, 1.5, 2.5, 3.5], dtype=np.float32)
    signal_resampled = test_signal.resample(resampled_timestamps, method="linear")

    assert signal_resampled is not None
    expected_shape = (len(resampled_timestamps), 3)
    assert signal_resampled.value.shape == expected_shape, (
        f"Expected shape {expected_shape}, got {signal_resampled.value.shape}"
    )

    expected = np.array(
        [[1.5, 2.5, 3.5], [4.5, 5.5, 6.5], [7.5, 8.5, 9.5], [10.5, 11.5, 12.5]],
        dtype=np.float32,
    )
    assert np.allclose(signal_resampled.value, expected)


def test_ares_signal_resample_cubic_multidim():
    """
    Test cubic resampling preserves shape for multi-dimensional signals.
    """
    test_signal = _make_multidim_signal(10, 3)

    resampled_timestamps = np.array([0.5, 1.5, 2.5, 3.5], dtype=np.float32)
    signal_resampled = test_signal.resample(resampled_timestamps, method="cubic")

    assert signal_resampled is not None
    expected_shape = (len(resampled_timestamps), 3)
    assert signal_resampled.value.shape == expected_shape, (
        f"Expected shape {expected_shape}, got {signal_resampled.value.shape}"
    )

    expected = np.array(
        [[1.5, 2.5, 3.5], [4.5, 5.5, 6.5], [7.5, 8.5, 9.5], [10.5, 11.5, 12.5]],
        dtype=np.float32,
    )
    assert np.allclose(signal_resampled.value, expected)


def test_ares_signal_resample_windowedsinc_multidim():
    """
    Test windowed-sinc resampling preserves shape for multi-dimensional signals.
    """
    test_signal = _make_multidim_signal(10, 3)

    resampled_timestamps = np.array([0.5, 1.5, 2.5, 3.5], dtype=np.float32)
    signal_resampled = test_signal.resample(
        resampled_timestamps, method="windowedsinc"
    )

    assert signal_resampled is not None
    expected_shape = (len(resampled_timestamps), 3)
    assert signal_resampled.value.shape == expected_shape, (
        f"Expected shape {expected_shape}, got {signal_resampled.value.shape}"
    )


def test_ares_signal_resample_3d():
    """
    Test resampling preserves shape for 3D signals.
    """
    n_timestamps = 10
    timestamps = np.arange(n_timestamps, dtype=np.float32)
    values = np.arange(n_timestamps * 2 * 3, dtype=np.float32).reshape(
        n_timestamps, 2, 3
    )
    test_signal = AresSignal(label="3d", timestamps=timestamps, value=values)

    resampled_timestamps = np.array([0.5, 1.5, 2.5], dtype=np.float32)
    signal_resampled = test_signal.resample(resampled_timestamps, method="linear")

    assert signal_resampled is not None
    expected_shape = (len(resampled_timestamps), 2, 3)
    assert signal_resampled.value.shape == expected_shape, (
        f"Expected shape {expected_shape}, got {signal_resampled.value.shape}"
    )


def test_ares_signal_wrong_timestamps_type():
    """
    Test if integer timestamps are cast and accepted.
    """
    signal = AresSignal(
        label="test_signal",
        timestamps=np.array([1, 2, 3, 4], dtype=int),
        value=np.array([1, 2, 3, 4], dtype=np.float32),
    )

    assert np.issubdtype(signal.timestamps.dtype, np.float32)
    assert np.array_equal(signal.timestamps, np.array([1, 2, 3, 4], dtype=np.float32))


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
    # test_ares_signal_resample()
    test_ares_signal_resample_windowedsinc_sine()
