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

DEBUG = False  # Enalble for debug plots


# INFO: Helper functions
def _make_multidim_signal(n_timestamps=10, n_channels=3):
    """Helper to create a multi-dimensional signal with known values."""
    timestamps = np.arange(n_timestamps, dtype=np.float32)
    values = np.arange(n_timestamps * n_channels, dtype=np.float32).reshape(
        n_timestamps, n_channels
    )
    return AresSignal(label="multidim", timestamps=timestamps, value=values)


# TEST: AresSignal initialization
def test_ares_signal_init():
    """
    Test if ares signal can be initialized with data and has correct attributes.
    """
    test_signal = AresSignal(
        label="test_signal",
        timestamps=np.array([1, 2, 3, 4], dtype=np.float32),
        value=np.array([1, 2, 3, 4], dtype=np.int64),
    )

    assert test_signal.label == "test_signal"
    assert isinstance(test_signal.timestamps, np.ndarray)
    assert np.issubdtype(test_signal.timestamps.dtype, np.float32)
    assert len(test_signal.timestamps) == 4
    assert isinstance(test_signal.value, np.ndarray)
    assert np.issubdtype(test_signal.value.dtype, np.int64)
    assert len(test_signal.value) == 4
    assert isinstance(test_signal.fs, np.float32)
    assert test_signal.fs == 1


@pytest.mark.parametrize(
    "label, timestamps, data",
    [
        (
            "test_signal1",
            np.arange(1, 5, 1, dtype=np.float32),
            np.ones((4), dtype=np.float32),
        ),
        (
            "test_signal2",
            np.array([10, 12, 13, 14, 15], dtype=np.float32),
            np.array([1, 2, 3, 4, 5], dtype=np.int32),
        ),
    ],
)
def test_ares_signal_init_parametrized(label, timestamps, data):
    """
    Tests different signal types and lengths.

    Args:
        label (str): Signal label under test.
        timestamps (np.ndarray): Timestamp array for the signal.
        data (np.ndarray): Value array for the signal.
    """
    test_signal = AresSignal(label=label, timestamps=timestamps, value=data)
    data_length = len(timestamps)

    assert test_signal.label == label
    assert isinstance(test_signal.timestamps, np.ndarray)
    assert np.issubdtype(test_signal.timestamps.dtype, np.float32)
    assert len(test_signal.timestamps) == data_length
    assert isinstance(test_signal.value, np.ndarray)
    assert len(test_signal.value) == data_length
    assert isinstance(test_signal.fs, np.float32)


# TEST: AresSignal input validation
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


def test_ares_signal_resample_non_numeric():
    """
    Test that non-numeric, non-boolean signals return None.
    """
    test_signal = AresSignal(
        label="complex",
        timestamps=np.array([0, 1, 2, 3], dtype=np.float32),
        value=np.array([1 + 2j, 3 + 4j, 5 + 6j, 7 + 8j]),
    )

    resampled_timestamps = np.array([0.5, 1.5, 2.5], dtype=np.float32)
    signal_resampled = test_signal.resample(resampled_timestamps)
    assert signal_resampled is None


# TEST: AresSignal resampling
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
    original_timestamps = test_signal.timestamps.copy()
    original_values = test_signal.value.copy()

    resampled_t = np.arange(0.0, 5, 1 / (fs * 1.88), dtype=np.float32)
    signal_resampled_up = test_signal.resample(resampled_t, method="windowedsinc")

    signal_resampled = signal_resampled_up.resample(t, method="windowedsinc")

    if DEBUG:
        import matplotlib.pyplot as plt

        fig = plt.figure()
        axes1 = fig.add_subplot(111)
        axes1.plot(
            signal_resampled_up.timestamps,
            signal_resampled_up.value,
            marker=".",
            color="blue",
            label="resampled up",
        )
        axes1.plot(
            test_signal.timestamps,
            test_signal.value,
            marker="o",
            color="red",
            alpha=0.5,
            label="original",
        )
        axes1.plot(
            signal_resampled.timestamps,
            signal_resampled.value,
            marker=".",
            color="green",
            alpha=0.5,
            label="resampled back",
        )
        axes1.set_xlabel("Time (s)")
        axes1.set_ylabel("Value")
        axes1.set_title("Sinus - windowed sinc resampling")
        axes1.legend()
        plt.show()

    assert signal_resampled is not None
    expected = np.sin(2 * np.pi * freq * resampled_t).astype(np.float32)
    assert np.allclose(signal_resampled_up.value, expected, atol=1e-1)
    assert np.allclose(signal_resampled.value, test_signal.value, atol=1e-1)
    assert np.array_equal(test_signal.timestamps, original_timestamps)
    assert np.array_equal(test_signal.value, original_values)


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


def test_ares_signal_resample_linear_multidim():
    """
    Test linear resampling preserves shape for multi-dimensional signals.
    """
    test_signal = _make_multidim_signal(10, 3)

    resampled_timestamps = np.array([0.5, 1.5, 2.5, 3.5], dtype=np.float32)
    signal_resampled = test_signal.resample(resampled_timestamps, method="linear")

    assert signal_resampled is not None
    expected_shape = (len(resampled_timestamps), 3)
    assert signal_resampled.value.shape == expected_shape

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
    assert signal_resampled.value.shape == expected_shape

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
    signal_resampled = test_signal.resample(resampled_timestamps, method="windowedsinc")

    assert signal_resampled is not None
    expected_shape = (len(resampled_timestamps), 3)
    assert signal_resampled.value.shape == expected_shape


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
    assert signal_resampled.value.shape == expected_shape


def test_ares_signal_resample_nearest_bool():
    """
    Test that bool signals are resampled with nearest-neighbor (not interpolated).
    """
    test_signal = AresSignal(
        label="bool_step",
        timestamps=np.array([0, 1, 2, 3, 4, 5], dtype=np.float32),
        value=np.array([False, False, True, True, False, False], dtype=bool),
    )
    original_timestamps = test_signal.timestamps.copy()
    original_values = test_signal.value.copy()

    resampled_timestamps = np.array([0.5, 1.5, 2.5, 3.5, 4.5], dtype=np.float32)
    signal_resampled = test_signal.resample(resampled_timestamps)

    assert signal_resampled is not None
    assert signal_resampled is not test_signal
    assert np.array_equal(signal_resampled.timestamps, resampled_timestamps)
    assert signal_resampled.value.dtype == np.bool_

    expected = np.array([False, True, True, False, False])
    assert np.array_equal(signal_resampled.value, expected)

    assert np.array_equal(test_signal.timestamps, original_timestamps)
    assert np.array_equal(test_signal.value, original_values)


def test_ares_signal_resample_nearest_int():
    """
    Test that integer signals are resampled with nearest-neighbor (not interpolated).
    """
    test_signal = AresSignal(
        label="int_step",
        timestamps=np.array([0, 1, 2, 3, 4, 5], dtype=np.float32),
        value=np.array([0, 0, 5, 5, 10, 10], dtype=np.int32),
    )
    original_timestamps = test_signal.timestamps.copy()
    original_values = test_signal.value.copy()

    resampled_timestamps = np.array([0.5, 1.5, 2.5, 3.5, 4.5], dtype=np.float32)
    signal_resampled = test_signal.resample(resampled_timestamps, method="linear")

    assert signal_resampled is not None
    assert signal_resampled is not test_signal
    assert np.array_equal(signal_resampled.timestamps, resampled_timestamps)
    assert np.issubdtype(signal_resampled.value.dtype, np.integer)

    expected = np.array([0, 5, 5, 10, 10], dtype=np.int32)
    assert np.array_equal(signal_resampled.value, expected)

    assert np.array_equal(test_signal.timestamps, original_timestamps)
    assert np.array_equal(test_signal.value, original_values)


def test_ares_signal_resample_nearest_bool_multidim():
    """
    Test nearest-neighbor resampling preserves shape for multi-dim bool signals.
    """
    n_timestamps = 10
    timestamps = np.arange(n_timestamps, dtype=np.float32)
    values = np.zeros((n_timestamps, 3), dtype=bool)
    values[3:7, 0] = True
    values[5:9, 1] = True
    values[1:4, 2] = True

    test_signal = AresSignal(label="bool_multidim", timestamps=timestamps, value=values)

    resampled_timestamps = np.array([0.5, 2.5, 4.5, 6.5, 8.5], dtype=np.float32)
    signal_resampled = test_signal.resample(resampled_timestamps)

    assert signal_resampled is not None
    expected_shape = (len(resampled_timestamps), 3)
    assert signal_resampled.value.shape == expected_shape
    assert signal_resampled.value.dtype == np.bool_


def test_ares_signal_resample_nearest_int_multidim():
    """
    Test nearest-neighbor resampling preserves shape for multi-dim int signals.
    """
    n_timestamps = 10
    timestamps = np.arange(n_timestamps, dtype=np.float32)
    values = np.zeros((n_timestamps, 3), dtype=np.int32)
    values[2:5, 0] = 10
    values[5:8, 1] = 20
    values[0:3, 2] = 30

    test_signal = AresSignal(label="int_multidim", timestamps=timestamps, value=values)

    resampled_timestamps = np.array([0.5, 2.5, 4.5, 6.5, 8.5], dtype=np.float32)
    signal_resampled = test_signal.resample(resampled_timestamps, method="windowedsinc")

    assert signal_resampled is not None
    expected_shape = (len(resampled_timestamps), 3)
    assert signal_resampled.value.shape == expected_shape
    assert np.issubdtype(signal_resampled.value.dtype, np.integer)


# TEST: AresSignal single-sample timestamps and dtype casting
def test_ares_signal_init_single_timestamp():
    """
    Test that a signal with a single timestamp is accepted and kept.
    """
    test_signal = AresSignal(
        label="single",
        timestamps=np.array([5.0], dtype=np.float32),
        value=np.array([42.0], dtype=np.float32),
    )

    assert test_signal.timestamps.shape == (1,)
    assert np.issubdtype(test_signal.timestamps.dtype, np.float32)
    assert np.array_equal(test_signal.timestamps, np.array([5.0], dtype=np.float32))


def test_ares_signal_init_single_timestamp_cast():
    """
    Test that a single integer timestamp is cast to float32.
    """
    test_signal = AresSignal(
        label="single_cast",
        timestamps=np.array([3], dtype=np.int64),
        value=np.array([7], dtype=np.float32),
    )

    assert np.issubdtype(test_signal.timestamps.dtype, np.float32)
    assert np.array_equal(test_signal.timestamps, np.array([3.0], dtype=np.float32))


def test_ares_signal_dtype_cast_changes_dtype():
    """
    Test that dtype_cast converts the value array to the target dtype.
    """
    test_signal = AresSignal(
        label="dtype_cast",
        timestamps=np.array([0, 1, 2, 3], dtype=np.float32),
        value=np.array([1, 2, 3, 4], dtype=np.float32),
    )

    test_signal.dtype_cast(np.float64)

    assert test_signal.value.dtype == np.float64
    assert np.array_equal(test_signal.value, np.array([1, 2, 3, 4], dtype=np.float64))


def test_ares_signal_dtype_cast_same_dtype_unchanged():
    """
    Test that dtype_cast to the current dtype does not modify the value.
    """
    test_signal = AresSignal(
        label="dtype_cast_same",
        timestamps=np.array([0, 1, 2, 3], dtype=np.float32),
        value=np.array([1, 2, 3, 4], dtype=np.int32),
    )

    test_signal.dtype_cast(np.int32)

    assert test_signal.value.dtype == np.int32
    assert np.array_equal(test_signal.value, np.array([1, 2, 3, 4], dtype=np.int32))


# TEST: AresSignal resample validation
def test_ares_signal_resample_unsupported_method():
    """
    Test that an unsupported resample method returns None.
    """
    test_signal = AresSignal(
        label="bad_method",
        timestamps=np.array([0, 1, 2, 3], dtype=np.float32),
        value=np.array([0, 1, 2, 3], dtype=np.float32),
    )

    resampled = test_signal.resample(
        timestamps_resampled=np.array([0.5, 1.5, 2.5], dtype=np.float32),
        method="spline",
    )

    assert resampled is None


# TEST: AresSignal cut
def test_ares_signal_cut_by_index():
    """
    Test cutting a signal by sample index range.
    """
    test_signal = AresSignal(
        label="cut_index",
        timestamps=np.array([0, 1, 2, 3, 4], dtype=np.float32),
        value=np.array([10, 20, 30, 40, 50], dtype=np.float32),
    )

    cut_signal = test_signal.cut(start=1, end=3, mode="index")

    assert np.array_equal(cut_signal.value, np.array([20, 30, 40], dtype=np.float32))
    assert np.array_equal(cut_signal.timestamps, np.array([1, 2, 3], dtype=np.float32))


def test_ares_signal_cut_invalid_mode():
    """
    Test that an invalid cut mode raises an exception.
    """
    test_signal = AresSignal(
        label="cut_invalid",
        timestamps=np.array([0, 1, 2, 3], dtype=np.float32),
        value=np.array([0, 1, 2, 3], dtype=np.float32),
    )

    with pytest.raises(RuntimeError):
        test_signal.cut(start=0, end=1, mode="bogus")


# TEST: AresSignal padding
def test_ares_signal_padding_non_positive_returns_self():
    """
    Test that padding with zero or negative samples returns the signal unchanged.
    """
    test_signal = AresSignal(
        label="pad_zero",
        timestamps=np.array([0, 1, 2, 3], dtype=np.float32),
        value=np.array([0, 1, 2, 3], dtype=np.float32),
    )

    assert test_signal.padding(samples_to_add=0) is test_signal
    assert test_signal.padding(samples_to_add=-5) is test_signal


def test_ares_signal_padding_appends_samples():
    """
    Test that padding appends samples and extends the timestamps.
    """
    test_signal = AresSignal(
        label="pad",
        timestamps=np.array([0, 1, 2, 3], dtype=np.float32),
        value=np.array([0, 1, 2, 3], dtype=np.float32),
    )

    padded_signal = test_signal.padding(samples_to_add=2)

    assert padded_signal is not test_signal
    assert len(padded_signal.value) == 6
    assert len(padded_signal.timestamps) == 6
    assert np.array_equal(
        padded_signal.value, np.array([0, 1, 2, 3, 0, 0], dtype=np.float32)
    )
    assert np.allclose(
        padded_signal.timestamps,
        np.array([0, 1, 2, 3, 4, 5], dtype=np.float32),
    )


def test_ares_signal_padding_multidim_with_pad_value():
    """
    Test padding of a multi-dimensional signal with a custom pad value.
    """
    test_signal = AresSignal(
        label="pad_md",
        timestamps=np.arange(3, dtype=np.float32),
        value=np.array([[1, 2], [3, 4], [5, 6]], dtype=np.float32),
    )

    padded_signal = test_signal.padding(
        samples_to_add=1, pad_value=np.array([9, 9], dtype=np.float32)
    )

    assert padded_signal.value.shape == (4, 2)
    assert np.array_equal(
        padded_signal.value, np.array([[1, 2], [3, 4], [5, 6], [9, 9]])
    )
    assert len(padded_signal.timestamps) == 4
