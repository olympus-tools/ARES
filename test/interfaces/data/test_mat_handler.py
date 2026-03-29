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

import h5py
import numpy as np
import pytest
from mati.mati import MatInterface

from ares.interface.data.ares_signal import AresSignal
from ares.interface.data.mat_handler import MATHandler

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
TEST_MAT_PATH = Path(os.path.join(os.path.dirname(__file__), "test_file.mat"))
# Reference .mat 7.3 file written by MATLAB R2023b (used for attribute checks)
MATLAB_REFERENCE_MAT = Path(
    os.path.join(
        os.path.dirname(__file__),
        "../../../examples/data/data_example_7.mat",
    )
)


def _make_scalar_signal(
    label="test_signal",
    n=4,
    dtype=np.float64,
) -> AresSignal:
    """Return a simple 1-D scalar AresSignal."""
    return AresSignal(
        label=label,
        timestamps=np.linspace(0.0, 1.0, n, dtype=np.float64),
        value=np.array([1, 2, 3, 4], dtype=dtype)[:n],
    )


def _cleanup(path: Path):
    if path.is_file():
        path.unlink()


# ---------------------------------------------------------------------------
# Init tests
# ---------------------------------------------------------------------------
def test_mat_handler_init_write_mode():
    """MATHandler can be initialised without a file path (write mode)."""
    handler = MATHandler(file_path=None)
    assert handler.data == []


def test_mat_handler_init_write_mode_with_signals():
    """MATHandler can be initialised with signals in write mode."""
    signal = _make_scalar_signal()
    handler = MATHandler(file_path=None, data=[signal])
    assert len(handler.data) == 1
    assert handler.data[0].label == "test_signal"


def test_mat_handler_init_read_mode_existing_file():
    """MATHandler can be initialised with an existing .mat 7.3 file."""
    if not MATLAB_REFERENCE_MAT.is_file():
        pytest.skip("Reference MATLAB file not found, skipping read-mode init test.")
    handler = MATHandler(file_path=MATLAB_REFERENCE_MAT)
    assert handler.file_path == str(MATLAB_REFERENCE_MAT)


# ---------------------------------------------------------------------------
# Write / save tests
# ---------------------------------------------------------------------------
def test_mat_handler_save_creates_file():
    """_save() creates a .mat file on disk."""
    _cleanup(TEST_MAT_PATH)
    try:
        signal = _make_scalar_signal()
        handler = MATHandler(file_path=None, data=[signal])
        handler._save(TEST_MAT_PATH)
        assert TEST_MAT_PATH.is_file(), "Expected .mat file was not created."
    finally:
        _cleanup(TEST_MAT_PATH)


def test_mat_handler_save_produces_valid_hdf5():
    """The written .mat file is a valid HDF5 file."""
    _cleanup(TEST_MAT_PATH)
    try:
        signal = _make_scalar_signal()
        handler = MATHandler(file_path=None, data=[signal])
        handler._save(TEST_MAT_PATH)
        # h5py.File raises OSError if the file is not valid HDF5
        with h5py.File(TEST_MAT_PATH, "r") as f:
            assert len(f.keys()) > 0, "HDF5 file has no top-level groups."
    finally:
        _cleanup(TEST_MAT_PATH)


def test_mat_handler_save_has_mat_signature():
    """The first 128 bytes of the written file contain the MATLAB 7.3 signature."""
    _cleanup(TEST_MAT_PATH)
    try:
        signal = _make_scalar_signal()
        handler = MATHandler(file_path=None, data=[signal])
        handler._save(TEST_MAT_PATH)
        with open(TEST_MAT_PATH, "rb") as f:
            header = f.read(128)
        # Bytes 0-115: human-readable text starting with "MATLAB"
        assert header[:6] == b"MATLAB", "MAT file does not start with 'MATLAB' header."
        # Bytes 126-127: little-endian indicator "IM"
        assert header[126:128] == b"IM", (
            "Endian indicator must be 'IM' (little-endian)."
        )
        # Version field (bytes 124-125): 0x0200
        version = int.from_bytes(header[124:126], "little")
        assert version == 0x0200, f"Expected version 0x0200, got {hex(version)}."
    finally:
        _cleanup(TEST_MAT_PATH)


def test_mat_handler_save_multiple_signals():
    """Multiple signals can be written to the same .mat file."""
    _cleanup(TEST_MAT_PATH)
    try:
        signals = [
            _make_scalar_signal("sig_a", dtype=np.float64),
            _make_scalar_signal("sig_b", dtype=np.float32),
            _make_scalar_signal("sig_c", dtype=np.int32),
        ]
        handler = MATHandler(file_path=None, data=signals)
        handler._save(TEST_MAT_PATH)
        with h5py.File(TEST_MAT_PATH, "r") as f:
            keys = list(f.keys())
        assert "sig_a" in keys
        assert "sig_b" in keys
        assert "sig_c" in keys
    finally:
        _cleanup(TEST_MAT_PATH)


# ---------------------------------------------------------------------------
# HDF5 attribute correctness tests
# ---------------------------------------------------------------------------
class TestMatlabAttributes:
    """Verify that the HDF5 attributes written by MATHandler match MATLAB's expectations."""

    @pytest.fixture(autouse=True)
    def _write_file(self):
        """Write a single-signal .mat file before each test and remove it after."""
        _cleanup(TEST_MAT_PATH)
        signal = _make_scalar_signal("my_signal", dtype=np.float64)
        handler = MATHandler(file_path=None, data=[signal])
        handler._save(TEST_MAT_PATH)
        yield
        _cleanup(TEST_MAT_PATH)

    def test_group_has_matlab_class_timeseries(self):
        """Signal group must have MATLAB_class == b'timeseries'."""
        with h5py.File(TEST_MAT_PATH, "r") as f:
            grp = f["my_signal"]
            mc = grp.attrs["MATLAB_class"]
            assert mc == b"timeseries", f"Expected b'timeseries', got {mc!r}."

    def test_group_matlab_class_is_nullpad(self):
        """MATLAB_class on the group must use NULLPAD padding (strpad=1) as MATLAB writes it."""
        with h5py.File(TEST_MAT_PATH, "r") as f:
            grp = f["my_signal"]
            attr_id = h5py.h5a.open(grp.id, b"MATLAB_class")
            type_id = attr_id.get_type()
            strpad = type_id.get_strpad()
        assert strpad == h5py.h5t.STR_NULLPAD, (
            f"MATLAB_class on group expected NULLPAD ({h5py.h5t.STR_NULLPAD}), got {strpad}."
        )

    def test_group_has_matlab_fields(self):
        """Signal group must have a MATLAB_fields attribute."""
        with h5py.File(TEST_MAT_PATH, "r") as f:
            grp = f["my_signal"]
            assert "MATLAB_fields" in grp.attrs, (
                "MATLAB_fields attribute is missing on group."
            )

    def test_matlab_fields_contains_time_data_events(self):
        """MATLAB_fields must list exactly 'Time', 'Data', and 'Events'."""
        with h5py.File(TEST_MAT_PATH, "r") as f:
            grp = f["my_signal"]
            raw = grp.attrs["MATLAB_fields"]
        # Each element of raw is a numpy array of S1 bytes; join to get field name
        field_names = [b"".join(entry).decode("ascii") for entry in raw]
        assert set(field_names) == {"Time", "Data", "Events"}, (
            f"Expected {{'Time', 'Data', 'Events'}}, got {set(field_names)}."
        )

    def test_matlab_fields_is_vlen_of_s1(self):
        """MATLAB_fields must be stored as H5T_VLEN of H5T_STRING(size=1).
        A flat fixed-length string array causes libmat (MLClass_to_HDF5Type) to
        mis-dereference a pointer and crash MATLAB with an access violation.
        """
        with h5py.File(TEST_MAT_PATH, "r") as f:
            grp = f["my_signal"]
            attr_id = h5py.h5a.open(grp.id, b"MATLAB_fields")
            type_id = attr_id.get_type()
        # Top-level type must be VLEN
        assert type_id.get_class() == h5py.h5t.VLEN, (
            "MATLAB_fields must be H5T_VLEN, not a fixed-length array."
        )
        # Element type must be string of size 1
        super_type = type_id.get_super()
        assert super_type.get_class() == h5py.h5t.STRING, (
            "MATLAB_fields VLEN element must be H5T_STRING."
        )
        assert super_type.get_size() == 1, (
            f"MATLAB_fields VLEN element size must be 1, got {super_type.get_size()}."
        )

    def test_time_dataset_has_matlab_class(self):
        """'Time' dataset must have a MATLAB_class attribute."""
        with h5py.File(TEST_MAT_PATH, "r") as f:
            assert "MATLAB_class" in f["my_signal"]["Time"].attrs

    def test_data_dataset_has_matlab_class(self):
        """'Data' dataset must have a MATLAB_class attribute."""
        with h5py.File(TEST_MAT_PATH, "r") as f:
            assert "MATLAB_class" in f["my_signal"]["Data"].attrs

    def test_data_dataset_matlab_class_is_nullterm(self):
        """MATLAB_class on a dataset must use NULLTERM padding (strpad=0) with size=8."""
        with h5py.File(TEST_MAT_PATH, "r") as f:
            ds = f["my_signal"]["Data"]
            attr_id = h5py.h5a.open(ds.id, b"MATLAB_class")
            type_id = attr_id.get_type()
            strpad = type_id.get_strpad()
            size = type_id.get_size()
        assert strpad == h5py.h5t.STR_NULLTERM, (
            f"MATLAB_class on dataset expected NULLTERM ({h5py.h5t.STR_NULLTERM}), got {strpad}."
        )
        assert size == 8, (
            f"MATLAB_class on dataset must be fixed-length 8 bytes, got {size}."
        )

    def test_time_dataset_matlab_class_is_nullterm(self):
        """MATLAB_class on the 'Time' dataset must use NULLTERM padding with size=8."""
        with h5py.File(TEST_MAT_PATH, "r") as f:
            ds = f["my_signal"]["Time"]
            attr_id = h5py.h5a.open(ds.id, b"MATLAB_class")
            type_id = attr_id.get_type()
            strpad = type_id.get_strpad()
            size = type_id.get_size()
        assert strpad == h5py.h5t.STR_NULLTERM
        assert size == 8


# ---------------------------------------------------------------------------
# MATLAB_class dtype mapping tests
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "dtype, expected_class",
    [
        (np.float64, b"double"),
        (np.float32, b"single"),
        (np.int8, b"int8"),
        (np.uint8, b"uint8"),
        (np.int16, b"int16"),
        (np.uint16, b"uint16"),
        (np.int32, b"int32"),
        (np.uint32, b"uint32"),
        (np.int64, b"int64"),
        (np.uint64, b"uint64"),
        (np.bool_, b"logical"),
    ],
)
def test_get_matlab_class_mapping(dtype, expected_class):
    """_get_matlab_class maps NumPy dtypes to the correct MATLAB class bytes."""
    result = MatInterface._get_matlab_class(np.dtype(dtype))
    assert result == expected_class, (
        f"For dtype {dtype}, expected {expected_class!r}, got {result!r}."
    )


def test_get_matlab_class_fallback_to_double():
    """_get_matlab_class falls back to b'double' for unrecognised dtypes."""
    result = MatInterface._get_matlab_class(np.dtype(np.complex128))
    assert result == b"double"


# ---------------------------------------------------------------------------
# Round-trip data integrity tests
# ---------------------------------------------------------------------------
def test_round_trip_scalar_float64():
    """Write a float64 signal and read back values + timestamps unchanged."""
    _cleanup(TEST_MAT_PATH)
    try:
        ts = np.array([0.0, 0.1, 0.2, 0.3], dtype=np.float64)
        vals = np.array([10.0, 20.0, 30.0, 40.0], dtype=np.float64)
        signal = AresSignal(label="sig_f64", timestamps=ts, value=vals)
        handler = MATHandler(file_path=None, data=[signal])
        handler._save(TEST_MAT_PATH)

        # Use MATHandler to read it back
        reader = MATHandler(file_path=TEST_MAT_PATH)
        read_signals = reader.get()

        assert read_signals is not None
        assert len(read_signals) == 1
        assert read_signals[0].label == "sig_f64"
        np.testing.assert_array_equal(
            read_signals[0].value,
            vals,
            err_msg="Data values do not match after round-trip.",
        )
        np.testing.assert_array_almost_equal(
            read_signals[0].timestamps,
            ts,
            err_msg="Timestamps do not match after round-trip.",
        )
    finally:
        _cleanup(TEST_MAT_PATH)


def test_round_trip_scalar_int32():
    """Write an int32 signal and verify the stored MATLAB_class and data."""
    _cleanup(TEST_MAT_PATH)
    try:
        ts = np.array([0.0, 1.0, 2.0], dtype=np.float64)
        vals = np.array([-1, 0, 1], dtype=np.int32)
        signal = AresSignal(label="sig_i32", timestamps=ts, value=vals)
        handler = MATHandler(file_path=None, data=[signal])
        handler._save(TEST_MAT_PATH)

        # Use MATHandler to read it back
        reader = MATHandler(file_path=TEST_MAT_PATH)
        read_signals = reader.get()

        assert read_signals is not None
        assert len(read_signals) == 1
        np.testing.assert_array_equal(read_signals[0].value, vals)

        # Still verify the low-level MATLAB_class attribute
        with h5py.File(TEST_MAT_PATH, "r") as f:
            mc = f["sig_i32"]["Data"].attrs["MATLAB_class"]
        # MATLAB_class is read back as bytes; strip padding
        assert mc.rstrip(b"\x00") == b"int32", f"Expected b'int32', got {mc!r}."
    finally:
        _cleanup(TEST_MAT_PATH)


def test_round_trip_2d_signal():
    """Write a 2-D array signal (shape: cycles × array_size) and read back correctly."""
    _cleanup(TEST_MAT_PATH)
    try:
        n_cycles = 5
        arr_size = 3
        ts = np.arange(n_cycles, dtype=np.float64)
        vals = np.arange(n_cycles * arr_size, dtype=np.float64).reshape(
            n_cycles, arr_size
        )
        signal = AresSignal(label="sig_2d", timestamps=ts, value=vals)
        handler = MATHandler(file_path=None, data=[signal])
        handler._save(TEST_MAT_PATH)

        # Use MATHandler to read it back
        reader = MATHandler(file_path=TEST_MAT_PATH)
        read_signals = reader.get()

        assert read_signals is not None
        assert len(read_signals) == 1
        np.testing.assert_array_equal(read_signals[0].value, vals)
    finally:
        _cleanup(TEST_MAT_PATH)


def test_mat_handler_get_with_filter():
    """get() with label_filter only returns matching signals."""
    _cleanup(TEST_MAT_PATH)
    try:
        signals = [
            _make_scalar_signal("sig_1"),
            _make_scalar_signal("sig_2"),
            _make_scalar_signal("other"),
        ]
        handler = MATHandler(file_path=None, data=signals)
        handler._save(TEST_MAT_PATH)

        reader = MATHandler(file_path=TEST_MAT_PATH)
        # Filter for sig_1 and sig_2
        filtered = reader.get(label_filter=["sig_1", "sig_2"])

        assert filtered is not None
        assert len(filtered) == 2
        labels = {s.label for s in filtered}
        assert labels == {"sig_1", "sig_2"}
    finally:
        _cleanup(TEST_MAT_PATH)


def test_mat_handler_get_no_signals():
    """get() returns None when no signals are found after filtering."""
    _cleanup(TEST_MAT_PATH)
    try:
        signal = _make_scalar_signal("unique_signal")
        handler = MATHandler(file_path=None, data=[signal])
        handler._save(TEST_MAT_PATH)

        reader = MATHandler(file_path=TEST_MAT_PATH)
        # Filter for a non-existent signal
        filtered = reader.get(label_filter=["non_existent_signal"])

        assert filtered is None
    finally:
        _cleanup(TEST_MAT_PATH)


def test_mat_handler_get_resampling():
    """get() resamples signals when stepsize is provided."""
    _cleanup(TEST_MAT_PATH)
    try:
        # Create a signal with 100 samples
        timestamps = np.arange(0, 10, 0.1, dtype=np.float64)
        values = np.sin(timestamps, dtype=np.float64)
        signal = AresSignal(label="resample_sig", timestamps=timestamps, value=values)
        handler = MATHandler(file_path=None, data=[signal])
        handler._save(TEST_MAT_PATH)

        reader = MATHandler(file_path=TEST_MAT_PATH)
        # Request resampling to 200 ms (0.2 s). Original sample time is 0.1s. Expected length: 10 / 0.2 = 50
        resampled_signals = reader.get(stepsize=200)

        assert resampled_signals is not None
        assert len(resampled_signals) == 1
        assert resampled_signals[0].label == "resample_sig"
        assert len(resampled_signals[0].timestamps) == 50
        assert len(resampled_signals[0].value) == 50
    finally:
        _cleanup(TEST_MAT_PATH)


# ---------------------------------------------------------------------------
# add() method tests
# ---------------------------------------------------------------------------
def test_mat_handler_add_extends_data():
    """add() appends AresSignal objects to handler.data."""
    handler = MATHandler(file_path=None)
    assert handler.data == []
    sig1 = _make_scalar_signal("s1")
    sig2 = _make_scalar_signal("s2")
    handler.add([sig1])
    assert len(handler.data) == 1
    handler.add([sig2])
    assert len(handler.data) == 2
    assert handler.data[0].label == "s1"
    assert handler.data[1].label == "s2"


def test_mat_handler_init_with_data_calls_add():
    """Passing data= to __init__ is equivalent to calling add() afterwards."""
    sig = _make_scalar_signal("s")
    handler = MATHandler(file_path=None, data=[sig])
    assert len(handler.data) == 1
    assert handler.data[0].label == "s"


# ---------------------------------------------------------------------------
# Structure tests
# ---------------------------------------------------------------------------
def test_saved_group_contains_time_data_events():
    """Each signal group in the written .mat file must have 'Time', 'Data', and 'Events' sub-keys."""
    _cleanup(TEST_MAT_PATH)
    try:
        signal = _make_scalar_signal("my_sig")
        MATHandler(file_path=None, data=[signal])._save(TEST_MAT_PATH)
        with h5py.File(TEST_MAT_PATH, "r") as f:
            grp_keys = set(f["my_sig"].keys())
        assert {"Time", "Data", "Events"} <= grp_keys, (
            f"Expected 'Time', 'Data', 'Events' in group keys, got {grp_keys}."
        )
    finally:
        _cleanup(TEST_MAT_PATH)


def test_saved_events_is_empty_group():
    """The 'Events' entry for each signal must be an HDF5 group (not a dataset)."""
    _cleanup(TEST_MAT_PATH)
    try:
        signal = _make_scalar_signal("ev_sig")
        MATHandler(file_path=None, data=[signal])._save(TEST_MAT_PATH)
        with h5py.File(TEST_MAT_PATH, "r") as f:
            events = f["ev_sig"]["Events"]
            assert isinstance(events, h5py.Group), "'Events' must be an HDF5 group."
    finally:
        _cleanup(TEST_MAT_PATH)
