import struct
import numpy as np
import pytest
from pathlib import Path
from mat73_interface.mat73_interface import Mat73Interface


def test_get_matlab_class():
    """Test mapping of numpy dtypes to MATLAB classes."""
    assert Mat73Interface._get_matlab_class(np.dtype(np.float64)) == b"double"
    assert Mat73Interface._get_matlab_class(np.dtype(np.float32)) == b"single"
    assert Mat73Interface._get_matlab_class(np.dtype(np.int32)) == b"int32"
    assert Mat73Interface._get_matlab_class(np.dtype(np.uint8)) == b"uint8"
    assert Mat73Interface._get_matlab_class(np.dtype(np.bool_)) == b"logical"
    assert (
        Mat73Interface._get_matlab_class(np.dtype(np.complex128)) == b"double"
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
    Mat73Interface.write(test_file, signals)

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

    Mat73Interface.write(test_file, signals)
    read_signals = Mat73Interface.get_signals(test_file)

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

    Mat73Interface.write(test_file, signals)
    read_signals = Mat73Interface.get_signals(test_file)

    sig_2d = read_signals[0]
    assert sig_2d["value"].shape == (5, 3)
    np.testing.assert_array_almost_equal(sig_2d["value"], val_2d)


def test_round_trip_3d(tmp_path):
    """Test writing and reading back 3D signals."""
    test_file = tmp_path / "test_3d.mat"
    val_3d = np.random.rand(4, 3, 2)  # 4 samples, 3x2 matrix per sample
    signals = [{"label": "sig_3d", "timestamps": np.arange(4), "value": val_3d}]

    Mat73Interface.write(test_file, signals)
    read_signals = Mat73Interface.get_signals(test_file)

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
    Mat73Interface.write(test_file, signals)

    read_a = Mat73Interface.get_signals(test_file, label_filter=["a"])
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
        Mat73Interface.write(test_file, signals)


def test_struct_read(tmp_path):
    """Test reading signals nested in a struct."""
    import h5py

    test_file = tmp_path / "test_struct.mat"

    # Manually create a file with a struct (group)
    with h5py.File(test_file, "w") as f:
        s1 = f.create_group("my_struct")
        sig = s1.create_group("nested_sig")
        # Layout A: Time and Data datasets
        sig.create_dataset("Time", data=np.array([0.0, 1.0]))
        sig.create_dataset("Data", data=np.array([10.0, 20.0]))

    read_signals = Mat73Interface.get_signals(test_file, struct_name=["my_struct"])
    assert len(read_signals) == 1
    assert read_signals[0]["label"] == "nested_sig"
    np.testing.assert_array_equal(read_signals[0]["value"], [10.0, 20.0])
