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

import struct
from pathlib import Path

import numpy as np
import pytest
from mat_interface.mat_interface import MatInterface


def test_get_matlab_class():
    """Test mapping of numpy dtypes to MATLAB classes."""
    assert MatInterface._get_matlab_class(np.dtype(np.float64)) == b"double"
    assert MatInterface._get_matlab_class(np.dtype(np.float32)) == b"single"
    assert MatInterface._get_matlab_class(np.dtype(np.int32)) == b"int32"
    assert MatInterface._get_matlab_class(np.dtype(np.uint8)) == b"uint8"
    assert MatInterface._get_matlab_class(np.dtype(np.bool_)) == b"logical"
    assert (
        MatInterface._get_matlab_class(np.dtype(np.complex128)) == b"double"
    )  # Fallback


def test_write_header(tmp_path):
    """Verify the 128-byte MATLAB 7.3 header is correctly written."""
    test_file = tmp_path / "test_header.mat"
    signals = [
        {
            "label": "sig",
            "timestamps": np.array([0.0, 1.0]),
            "value": np.array([1.0, 2.0]),
        }
    ]
    MatInterface._write73(test_file, signals)

    with open(test_file, "rb") as f:
        header = f.read(128)

    assert len(header) == 128
    assert header.startswith(b"MATLAB 7.3 MAT-file")
    assert header[126:128] == b"IM"  # Little-endian indicator
    version = struct.unpack("<H", header[124:126])[0]
    assert version == 0x0200


def test_round_trip_1d(tmp_path):
    """Test writing and reading back 1D signals."""
    test_file = tmp_path / "test_1d.mat"
    signals = [
        {
            "label": "sig_double",
            "timestamps": np.linspace(0, 1, 10),
            "value": np.sin(np.linspace(0, 1, 10)),
        },
        {
            "label": "sig_int",
            "timestamps": np.linspace(0, 1, 5),
            "value": np.array([1, 2, 3, 4, 5], dtype=np.int32),
        },
    ]

    MatInterface._write73(test_file, signals)
    read_signals = MatInterface.get(test_file)
    assert len(read_signals) == 2

    # Check sig_double
    sig_double = next(s for s in read_signals if s["label"] == "sig_double")
    np.testing.assert_array_almost_equal(
        sig_double["timestamps"], signals[0]["timestamps"]
    )
    np.testing.assert_array_almost_equal(sig_double["value"], signals[0]["value"])

    # Check sig_int
    sig_int = next(s for s in read_signals if s["label"] == "sig_int")
    np.testing.assert_array_almost_equal(
        sig_int["timestamps"], signals[1]["timestamps"]
    )
    np.testing.assert_array_equal(sig_int["value"], signals[1]["value"])


def test_round_trip_2d(tmp_path):
    """Test writing and reading back 2D signals."""
    test_file = tmp_path / "test_2d.mat"
    val_2d = np.random.rand(5, 3)  # 5 samples, 3 channels
    signals = [{"label": "sig_2d", "timestamps": np.arange(5), "value": val_2d}]

    MatInterface._write73(test_file, signals)
    read_signals = MatInterface.get(test_file)

    sig_2d = read_signals[0]
    assert sig_2d["value"].shape == (5, 3)
    np.testing.assert_array_almost_equal(sig_2d["value"], val_2d)


def test_round_trip_3d(tmp_path):
    """Test writing and reading back 3D signals."""
    test_file = tmp_path / "test_3d.mat"
    val_3d = np.random.rand(4, 3, 2)  # 4 samples, 3x2 matrix per sample
    signals = [{"label": "sig_3d", "timestamps": np.arange(4), "value": val_3d}]

    MatInterface._write73(test_file, signals)
    read_signals = MatInterface.get(test_file)

    sig_3d = read_signals[0]
    assert sig_3d["value"].shape == (4, 3, 2)
    np.testing.assert_array_almost_equal(sig_3d["value"], val_3d)


def test_label_filter(tmp_path):
    """Test reading with label filter."""
    test_file = tmp_path / "test_filter.mat"
    signals = [
        {"label": "a", "timestamps": np.array([0]), "value": np.array([1])},
        {"label": "b", "timestamps": np.array([0]), "value": np.array([2])},
    ]
    MatInterface._write73(test_file, signals)

    read_a = MatInterface.get(test_file, label_filter=["a"])
    assert len(read_a) == 1
    assert read_a[0]["label"] == "a"


def test_unsupported_dimensions(tmp_path):
    """Verify ValueError for >3 dimensions."""
    test_file = tmp_path / "test_4d.mat"
    signals = [
        {
            "label": "sig_4d",
            "timestamps": np.array([0]),
            "value": np.zeros((1, 1, 1, 1)),
        }
    ]
    with pytest.raises(ValueError, match="does not support more than 3 dimensions"):
        MatInterface._write73(test_file, signals)


def test_round_trip_v7(tmp_path):
    """Test writing and reading back 1D signals in v7 format."""
    test_file = tmp_path / "test_v7.mat"
    signals = [
        {
            "label": "sig_float",
            "timestamps": np.linspace(0, 5, 10),
            "value": np.cos(np.linspace(0, 5, 10)),
        },
        {
            "label": "sig_bool",
            "timestamps": np.linspace(0, 1, 2),
            "value": np.array([True, False], dtype=bool),
        },
    ]

    MatInterface.write(test_file, signals, format="v7")
    read_signals = MatInterface.get(test_file)
    assert len(read_signals) == 2

    # Check sig_float
    sig_float = next(s for s in read_signals if s["label"] == "sig_float")
    np.testing.assert_array_almost_equal(
        sig_float["timestamps"], signals[0]["timestamps"]
    )
    np.testing.assert_array_almost_equal(sig_float["value"], signals[0]["value"])

    # Check sig_bool
    sig_bool = next(s for s in read_signals if s["label"] == "sig_bool")
    np.testing.assert_array_almost_equal(
        sig_bool["timestamps"], signals[1]["timestamps"]
    )
    np.testing.assert_array_equal(sig_bool["value"], signals[1]["value"])


def test_read_v7_flat_signals_example():
    """Test reading flat signals from an existing v7 MAT file."""
    file_path = Path("examples/data/mat_v7_flat_signals.mat")
    # Use label_filter to get specific signals we know exist
    signals = MatInterface.get(file_path, label_filter=["sig_a_f32", "sig_b_f32"])

    assert len(signals) == 2

    sig_a = next(s for s in signals if s["label"] == "sig_a_f32")
    sig_b = next(s for s in signals if s["label"] == "sig_b_f32")

    assert sig_a["value"].shape == (11,)
    assert sig_a["value"].dtype == np.float32
    assert sig_a["timestamps"].shape == (11,)

    assert sig_b["value"].shape == (11, 3)
    assert sig_b["value"].dtype == np.float32
    assert sig_b["timestamps"].shape == (11,)


def test_read_v7_timeseries_example():
    """Test reading timeseries structs from an existing v7 MAT file."""
    file_path = Path("examples/data/mat_v7_flat_timeseries.mat")
    # Use label_filter to get specific signals we know exist
    signals = MatInterface.get(file_path, label_filter=["ts_sig_a_f32", "ts_sig_b_f32"])

    assert len(signals) == 2

    sig_a = next(s for s in signals if s["label"] == "ts_sig_a_f32")
    sig_b = next(s for s in signals if s["label"] == "ts_sig_b_f32")

    assert sig_a["label"] == "ts_sig_a_f32"
    assert sig_a["timestamps"].shape == (11,)
    assert sig_a["value"].shape == (11,)
    assert sig_a["value"].dtype == np.float32

    assert sig_b["label"] == "ts_sig_b_f32"
    assert sig_b["timestamps"].shape == (11,)
    assert sig_b["value"].shape == (11, 3)
    assert sig_b["value"].dtype == np.float32
