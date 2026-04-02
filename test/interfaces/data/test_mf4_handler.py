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

import os
from pathlib import Path

import numpy as np
import pytest
from asammdf.blocks.utils import MdfException

from ares.interface.data.ares_signal import AresSignal
from ares.interface.data.mf4_handler import MF4Handler


def test_ares_mf4handler_file_init_read():
    """
    Test if mf4handler can be initialized with mf4-file mode "read".
    """
    mf4_filepath = Path(
        os.path.join(
            os.path.dirname(__file__),
            "../../../examples/data/data_example_1.mf4",
        )
    )

    if mf4_filepath.is_file():
        test_data = MF4Handler(
            file_path=mf4_filepath,
        )


def test_ares_mf4handler_file_init_write():
    """
    Test if mf4handler can be initialized with mf4-file mode "write".
    """
    mf4_filepath = Path(os.path.join(os.path.dirname(__file__), "test_file.mf4"))
    test_data_write01 = MF4Handler(file_path=None, signals=[])
    test_data_write01._save(mf4_filepath)

    if not mf4_filepath.is_file():
        assert "Argh. No mf-4-file was created. Check mf4_handler implementation."
    else:
        mf4_filepath.unlink()

    test_data_write02 = MF4Handler(file_path=None, signals=[])
    test_data_write02._save(mf4_filepath)

    if not mf4_filepath.is_file():
        assert "Argh. No mf-4-file was created. Check mf4_handler implementation."
    else:
        mf4_filepath.unlink()

    # WARN: The following part in the test leads to an recursion in asammdf. This is on purpose!
    with pytest.raises(MdfException):
        test_data_read = MF4Handler(file_path=mf4_filepath)


def test_ares_mf4handler_file_read_get():
    """
    Test if mf4handler can read signals from mf4-files.
    """
    mf4_filepath = Path(
        os.path.join(
            os.path.dirname(__file__),
            "../../../examples/data/data_example_1.mf4",
        )
    )

    if mf4_filepath.is_file():
        test_data = MF4Handler(
            file_path=mf4_filepath,
        )

    test_signal = test_data.get(["input_value"])
    test_signals = test_data.get([".*_"])

    assert test_signal is not None, "get() must return signals for existing label."
    assert len(test_signal) == 1, "Wrong number of signals were extracted."
    assert test_signal[0].label == "input_value", "The wrong signal was extracted."
    assert test_signals is not None, "get() must return signals for regex pattern."
    assert len(test_signals) != 1, (
        "Too few singals were extracted. Regex pattern should extract all available signals."
    )


def test_ares_mf4handler_file_write_get():
    """
    Test if mf4handler can read signals from created mf4-file.
    """
    mf4_filepath = Path(os.path.join(os.path.dirname(__file__), "test_file.mf4"))

    test_signal = AresSignal(
        label="test_signal",
        timestamps=np.array([1, 2, 3, 4], dtype=np.float32),
        value=np.array([1, 2, 3, 4], dtype=np.int64),
    )

    test_data_write = MF4Handler(file_path=None, data=[test_signal])
    test_signal_read = test_data_write.get()

    assert test_signal_read is not None, "get() must return signals after write init."
    assert len(test_signal_read) == 1, (
        "Wrong number of signals were extracted after write."
    )
    assert test_signal_read[0].label == "test_signal", (
        "The wrong signal label was written."
    )

    test_data_write._save(mf4_filepath)
    if not mf4_filepath.is_file():
        assert "Argh. No mf-4-file was created. Check mf4_handler implementation."
    else:
        mf4_filepath.unlink()


def test_ares_mf4handler_add_explicit():
    """
    Test if mf4handler.add() correctly adds signals when called explicitly after init.
    """
    signal_a = AresSignal(
        label="sig_a",
        timestamps=np.array([0.0, 1.0, 2.0], dtype=np.float32),
        value=np.array([10.0, 20.0, 30.0], dtype=np.float64),
        unit="m/s",
        description="velocity",
    )
    signal_b = AresSignal(
        label="sig_b",
        timestamps=np.array([0.0, 1.0, 2.0], dtype=np.float32),
        value=np.array([1, 2, 3], dtype=np.int32),
    )

    handler = MF4Handler(file_path=None)
    handler.add(data=[signal_a])
    handler.add(data=[signal_b])

    result = handler.get()

    assert result is not None, "get() must return signals after add()."
    labels = [s.label for s in result]
    assert "sig_a" in labels, "sig_a should be present after add()."
    assert "sig_b" in labels, "sig_b should be present after add()."
    assert len(result) == 2, "Exactly two signals should be present."


def test_ares_mf4handler_add_2d_signal():
    """
    Test if mf4handler.add() correctly handles 2D signals (1D array per timestep).
    """
    timestamps = np.array([0.0, 1.0, 2.0, 3.0], dtype=np.float32)
    # shape (4 timesteps, 3 columns) -> ndim == 2
    value_2d = np.array(
        [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]], dtype=np.float32
    )

    signal_2d = AresSignal(
        label="sig_2d",
        timestamps=timestamps,
        value=value_2d,
    )

    handler = MF4Handler(file_path=None, data=[signal_2d])
    result = handler.get()

    assert result is not None, "get() must return signals after adding a 2D signal."
    assert len(result) == 1, "Exactly one signal should be present."
    assert result[0].label == "sig_2d", "Label must match the added 2D signal."


def test_ares_mf4handler_add_3d_signal():
    """
    Test if mf4handler.add() correctly handles 3D signals (2D array per timestep).
    """
    timestamps = np.array([0.0, 1.0, 2.0], dtype=np.float32)
    # shape (3 timesteps, 2 rows, 4 cols) -> ndim == 3
    value_3d = np.ones((3, 2, 4), dtype=np.float32)

    signal_3d = AresSignal(
        label="sig_3d",
        timestamps=timestamps,
        value=value_3d,
    )

    handler = MF4Handler(file_path=None, data=[signal_3d])
    result = handler.get()

    assert result is not None, "get() must return signals after adding a 3D signal."
    assert len(result) == 1, "Exactly one signal should be present."
    assert result[0].label == "sig_3d", "Label must match the added 3D signal."


def test_ares_mf4handler_add_deduplication():
    """
    Test if mf4handler.add() deduplicates signals with the same label,
    keeping the last occurrence.
    """
    signal_first = AresSignal(
        label="dup_signal",
        timestamps=np.array([0.0, 1.0], dtype=np.float32),
        value=np.array([1.0, 2.0], dtype=np.float32),
    )
    signal_last = AresSignal(
        label="dup_signal",
        timestamps=np.array([0.0, 1.0], dtype=np.float32),
        value=np.array([99.0, 100.0], dtype=np.float32),
    )

    handler = MF4Handler(file_path=None, data=[signal_first, signal_last])
    result = handler.get()

    assert result is not None, "get() must return signals."
    dup_signals = [s for s in result if s.label == "dup_signal"]
    assert len(dup_signals) == 1, "Duplicate signals must be deduplicated to one."
    assert np.array_equal(dup_signals[0].value, signal_last.value), (
        "The last occurrence of the duplicate signal must be kept."
    )


def test_ares_mf4handler_get_no_match_returns_none():
    """
    Test if mf4handler.get() returns None when the label filter matches nothing.
    """
    signal = AresSignal(
        label="real_signal",
        timestamps=np.array([0.0, 1.0, 2.0], dtype=np.float32),
        value=np.array([1.0, 2.0, 3.0], dtype=np.float32),
    )

    handler = MF4Handler(file_path=None, data=[signal])
    result = handler.get(label_filter=["nonexistent_signal_xyz"])

    assert result is None, "get() must return None when no signals match the filter."


def test_ares_mf4handler_get_with_stepsize():
    """
    Test if mf4handler.get() correctly resamples signals when stepsize is provided.
    """
    mf4_filepath = Path(
        os.path.join(
            os.path.dirname(__file__),
            "../../../examples/data/data_example_1.mf4",
        )
    )

    if not mf4_filepath.is_file():
        pytest.skip("Example mf4 file not available.")

    handler = MF4Handler(file_path=mf4_filepath)
    result_raw = handler.get()
    result_resampled = handler.get(stepsize=10)

    assert result_raw is not None, "get() without stepsize must return signals."
    assert result_resampled is not None, "get() with stepsize must return signals."
    assert len(result_resampled) == len(result_raw), (
        "Number of signals must not change after resampling."
    )
    # All resampled signals must share the same timestamps
    ref_timestamps = result_resampled[0].timestamps
    for sig in result_resampled[1:]:
        assert np.array_equal(sig.timestamps, ref_timestamps), (
            "All resampled signals must share a common time vector."
        )


def test_ares_mf4handler_get_with_vstack_pattern():
    """
    Test if mf4handler.get() correctly applies vstack_pattern to stack 1D signals to 2D.
    """
    from ares.pydantic_models.workflow_model import VStackPatternElement

    timestamps = np.array([0.0, 1.0, 2.0, 3.0], dtype=np.float32)
    signals = [
        AresSignal(
            label=f"channel_{i}",
            timestamps=timestamps,
            value=np.array([float(i)] * 4, dtype=np.float64),
        )
        for i in range(3)
    ]

    handler = MF4Handler(file_path=None, data=signals)

    vstack = VStackPatternElement(pattern=r"(channel)_(\d+)", signal_name=1, x_axis=2)
    result = handler.get(vstack_pattern=[vstack])

    assert result is not None, "get() with vstack_pattern must return signals."
    stacked = [s for s in result if s.label == "channel"]
    assert len(stacked) == 1, "Exactly one stacked signal 'channel' should be produced."
    assert stacked[0].ndim == 2, "Stacked signal must be 2D."


def test_ares_mf4handler_init_with_label_filter():
    """
    Test if mf4handler initialized with label_filter only returns filtered signals on get().
    """
    mf4_filepath = Path(
        os.path.join(
            os.path.dirname(__file__),
            "../../../examples/data/data_example_1.mf4",
        )
    )

    if not mf4_filepath.is_file():
        pytest.skip("Example mf4 file not available.")

    handler = MF4Handler(file_path=mf4_filepath, label_filter=["input_value"])
    result = handler.get()

    assert result is not None, "get() must return signals when label_filter matches."
    assert len(result) == 1, (
        "Only one signal should be returned with exact label_filter."
    )
    assert result[0].label == "input_value", "The filtered signal label must match."


# ---------------------------------------------------------------------------
# DTYPE_MAP tests
# ---------------------------------------------------------------------------

# All dtypes present in MF4Handler.DTYPE_MAP
_DTYPE_MAP_DTYPES = [
    np.float32,
    np.float64,
    np.bool_,
    np.int8,
    np.int16,
    np.int32,
    np.int64,
    np.uint8,
    np.uint16,
    np.uint32,
    np.uint64,
]


@pytest.mark.parametrize("dtype", _DTYPE_MAP_DTYPES)
def test_ares_mf4handler_dtype_map_2d_roundtrip(dtype):
    """
    Test that every dtype in DTYPE_MAP survives an add() -> get() round-trip
    for a 2D signal (1D array per timestep).
    Each mapped dtype must be accepted by add() without raising and the signal
    must be retrievable by get() with its label intact.
    """
    timestamps = np.array([0.0, 1.0, 2.0, 3.0], dtype=np.float32)
    value_2d = np.array([[1, 2], [3, 4], [5, 6], [7, 8]], dtype=dtype)

    signal = AresSignal(
        label=f"sig_2d_{np.dtype(dtype).name}",
        timestamps=timestamps,
        value=value_2d,
    )

    assert np.dtype(dtype) in MF4Handler.DTYPE_MAP, (
        f"dtype {dtype} must be present in MF4Handler.DTYPE_MAP."
    )

    handler = MF4Handler(file_path=None, data=[signal])
    result = handler.get()

    assert result is not None, (
        f"get() must return signals for 2D signal with dtype {dtype}."
    )
    assert len(result) == 1, f"Exactly one signal expected for dtype {dtype}."
    assert result[0].label == signal.label, (
        f"Signal label must be preserved for dtype {dtype}."
    )


@pytest.mark.parametrize("dtype", _DTYPE_MAP_DTYPES)
def test_ares_mf4handler_dtype_map_3d_roundtrip(dtype):
    """
    Test that every dtype in DTYPE_MAP survives an add() -> get() round-trip
    for a 3D signal (2D array per timestep).
    Each mapped dtype must be accepted by add() without raising and the signal
    must be retrievable by get() with its label intact.
    """
    timestamps = np.array([0.0, 1.0, 2.0], dtype=np.float32)
    value_3d = np.ones((3, 2, 3), dtype=dtype)

    signal = AresSignal(
        label=f"sig_3d_{np.dtype(dtype).name}",
        timestamps=timestamps,
        value=value_3d,
    )

    assert np.dtype(dtype) in MF4Handler.DTYPE_MAP, (
        f"dtype {dtype} must be present in MF4Handler.DTYPE_MAP."
    )

    handler = MF4Handler(file_path=None, data=[signal])
    result = handler.get()

    assert result is not None, (
        f"get() must return signals for 3D signal with dtype {dtype}."
    )
    assert len(result) == 1, f"Exactly one signal expected for dtype {dtype}."
    assert result[0].label == signal.label, (
        f"Signal label must be preserved for dtype {dtype}."
    )


def test_ares_mf4handler_dtype_map_coverage():
    """
    Test that MF4Handler.DTYPE_MAP contains exactly the expected set of dtypes.
    Catches accidental additions or removals from the map.
    """
    expected_dtypes = {
        np.dtype(np.float32),
        np.dtype(np.float64),
        np.dtype(np.bool_),
        np.dtype(np.int8),
        np.dtype(np.int16),
        np.dtype(np.int32),
        np.dtype(np.int64),
        np.dtype(np.uint8),
        np.dtype(np.uint16),
        np.dtype(np.uint32),
        np.dtype(np.uint64),
    }

    assert set(MF4Handler.DTYPE_MAP.keys()) == expected_dtypes, (
        "MF4Handler.DTYPE_MAP does not match the expected set of dtypes. "
        "Update DTYPE_MAP or this test to keep them in sync."
    )


def test_ares_mf4handler_dtype_map_unmapped_dtype_raises():
    """
    Test that add() raises a KeyError when a 2D signal carries a dtype
    that is not present in DTYPE_MAP (e.g. complex128).
    This documents the current, intentional behaviour: unsupported dtypes
    must be converted by the caller before passing to MF4Handler.
    """
    timestamps = np.array([0.0, 1.0, 2.0], dtype=np.float32)
    # complex128 is not in DTYPE_MAP
    value_unmapped = np.array(
        [[1 + 2j, 3 + 4j], [5 + 6j, 7 + 8j], [9 + 10j, 11 + 12j]], dtype=np.complex128
    )

    signal = AresSignal(
        label="sig_unmapped_dtype",
        timestamps=timestamps,
        value=value_unmapped,
    )

    assert np.dtype(np.complex128) not in MF4Handler.DTYPE_MAP, (
        "complex128 must not be in DTYPE_MAP for this test to be valid."
    )

    handler = MF4Handler(file_path=None)
    with pytest.raises(KeyError):
        handler.add(data=[signal])
