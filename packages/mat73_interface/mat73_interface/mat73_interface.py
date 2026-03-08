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

import datetime
import struct
import warnings
from pathlib import Path

import h5py
import numpy as np


class Mat73Interface:
    """A standalone interface for reading and writing MATLAB 7.3 MAT-files (HDF5 based).

    The Mat73Interface is based on python standard interfaces to guarantee easy usage and minimum dependencies.

    additional information see:
    https://de.mathworks.com/help/matlab/import_export/mat-file-versions.html?s_tid=srchtitle_site_search_1_mat+files
    https://www.hdfgroup.org/solutions/hdf5/
    """

    @staticmethod
    def write(
        output_path: Path,
        signals: list[dict[str, str | np.typing.NDArray[np.generic]]],
    ) -> None:
        """Write signals to a MAT 7.3 file (HDF5).
        Each signal is stored as a top-level HDF5 group containing three members:
        - ``Time``   – 1-D dataset, timestamps (double)
        - ``Data``   – 1-D or N-D dataset, signal values
        - ``Events`` – empty group (reserved for MATLAB compatibility)

        The group carries ``MATLAB_class = "timeseries"`` and ``MATLAB_fields``
        attributes so that MATLAB's ``load()`` recognises the layout.
        note:
            MATLAB's ``load()`` will return each signal as a **struct** with fields
            ``Time``, ``Data``, and ``Events``.
            The struct represents the base of a MATLAB ``timeseries``.
            A true ``timeseries`` object requires MATLAB's MCOS object serialisation,
            which cannot be produced from Python.  To convert after loading in MATLAB::
            'ts = timeseries(sig.Data, sig.Time, 'Name', 'my_signal');'
        Args:
            output_path (Path): Path to the output file.
            signals (list[dict]): List of dicts, each with:
                - ``'label'``      (str):        signal name
                - ``'timestamps'`` (np.ndarray): 1-D time vector
                - ``'value'``      (np.ndarray): 1-D / 2-D / 3-D value array
        """
        with h5py.File(output_path, "w", userblock_size=512) as h5file:  # type: ignore[reportGeneralTypeIssues]
            # HDF5 attribute encoding for MATLAB compatibility (hdf5 tweaked to match *.mat expectations)
            _ds_class_tid = h5py.h5t.py_create(np.dtype("S8"))
            _ds_class_tid.set_strpad(h5py.h5t.STR_NULLTERM)
            _ds_class_sid = h5py.h5s.create(h5py.h5s.SCALAR)
            _vlen_s1_dt = h5py.vlen_dtype(np.dtype("S1"))  # pyright: ignore[reportAttributeAccessIssue]

            # helper functions for writing
            def _write_ds_matlab_class(dataset_id, class_bytes: bytes) -> None:
                """Add matlab-class attributes to represent datatype."""
                padded_bytes = class_bytes.ljust(8, b"\x00")[:8]
                attribute = h5py.h5a.create(  # type: ignore
                    dataset_id, b"MATLAB_class", _ds_class_tid, _ds_class_sid
                )
                attribute.write(np.frombuffer(padded_bytes, dtype="S8"))

            def _mat_fields(*names: str) -> np.ndarray:
                """Helper function for '_write_mat_fields'. Write names as ascii array."""
                array = np.empty(len(names), dtype=object)
                for i, name in enumerate(names):
                    array[i] = np.array([c.encode("ascii") for c in name], dtype="S1")
                return array

            def _write_mat_fields(group, *names: str) -> None:
                """Initialize timeseries-struct with given names."""
                group.attrs.create(
                    "MATLAB_fields",
                    data=_mat_fields(*names),
                    dtype=_vlen_s1_dt,
                )

            # write HDF5 content
            for signal in signals:
                label: str = signal["label"]
                timestamps: np.typing.NDArray[np.generic] = signal["timestamps"]
                value: np.typing.NDArray[np.generic] = signal["value"]
                dtype = value.dtype

                # initialize matlab group (add important metadata)
                group = h5file.create_group(label)
                group.attrs["MATLAB_class"] = np.bytes_(b"timeseries")
                _write_mat_fields(group, "Time", "Data", "Events")
                group.create_group("Events")

                # write timestamp
                timestamps_single = timestamps.astype(np.float32)
                ti = group.create_dataset("Time", data=timestamps_single.T)
                _write_ds_matlab_class(ti.id, b"single")

                # write signal data
                if value.ndim <= 2:
                    ds = group.create_dataset("Data", data=value.T)
                elif value.ndim == 3:
                    ds = group.create_dataset("Data", data=value.transpose(2, 1, 0))
                else:
                    raise ValueError(
                        "Mat73Interface does not support more than 3 dimensions."
                    )
                _write_ds_matlab_class(ds.id, Mat73Interface._get_matlab_class(dtype))

        # add MATLAB specific 128-byte header
        date_str = datetime.datetime.now().strftime("%a %b %d %H:%M:%S %Y")
        # byte: 0-115 | text | human readable
        header = (
            f"MATLAB 7.3 MAT-file, Platform: Python/ARES, Created on: {date_str}".ljust(
                116
            )
        )
        subsystem_offset = (
            b"\x00" * 8
        )  # byte: 116- 123 | subsystem specific data | all 0 |
        version = 0x0200  # byte: 124 - 125 | version | 0x0200 or 0x0100 |
        endian = b"IM"  # byte: 126 - 127 | Endian Indicator | MI BitEndian, IM LittleEndian (Intel/AMD = IM)
        signature = (
            header.encode("ascii")
            + subsystem_offset
            + struct.pack("<H2s", version, endian)
        )

        if len(signature) != 128:
            raise ValueError(f"Header must be 128 bytes, but got {len(signature)}.")
        with open(output_path, "r+b") as h5file:
            h5file.seek(0)
            h5file.write(signature)

    @staticmethod
    def get_signals(
        file_path: Path,
        label_filter: list[str] | None = None,
        struct_name: list[str] | None = None,
    ) -> list[dict[str, str | np.typing.NDArray[np.generic]]]:
        """Read signals from a MAT 7.3 file.

        Supports two modes (defined via struct_name):
            - flat   : signals exist at the highest layer
            - struct : signals are divided into structs each with providing its own timestamp

        where each mode can read two types of signals:
            - **timeseries struct layout**: each signal is a struct containing "Time","Data"
            - **flat signal arrays**: each signal is a array whereas one array represents the shared timestamp

        Note: MATLAB MCOS ``timeseries`` *objects* (``MATLAB_object_decode==3``)
        store their data in an opaque ``#refs#`` pool and cannot be decoded
        without a full MATLAB OOP deserialiser.
        Therefore not the 'real' MATLAB timeseries supported (same holds for scipy).

        Assumptions:
        Considering the ''flat'' signal structure the assumption that the shared timevector is called either
            - timestamps
            - time
        is made.

        Args:
            file_path (Path): Path to the MAT file.
            label_filter (list[str] | None): List of signal names to read.
            struct_name (list[str] | None): List of structs which contain the signals to extract.

        Returns:
            list[dict]: List of ``{'label', 'timestamps', 'value'}`` dicts.
            list[str]: List of all signalnames found in mat-file.
        """
        _HDF5_INTERNAL = {"#refs#", "#subsystem#"}
        _NUMERIC_KINDS = set("bifcu")
        _TIMESERIES_KEYS = {
            "Data",
            "Time",
        }  # Events can be ignored, only important for writing
        _TIMESTAMP_NAMES = {"timestamps", "time"}

        # helper functions for reading
        def _is_timeseries_group(obj) -> bool:
            """Droup = plain-struct Time/Data groups."""
            if not hasattr(obj, "keys"):
                return False
            if obj.attrs.get("MATLAB_object_decode") is not None:
                # MCOS object – cannot decode without MATLAB OOP deserialiser
                return False
            return _TIMESERIES_KEYS.issubset(set(obj.keys()))

        def _is_numeric_dataset(obj) -> bool:
            """Dataset = numeric"""
            return (
                isinstance(obj, h5py.Dataset) # type: ignore
                and obj.attrs.get("MATLAB_object_decode") is None
                and obj.dtype.kind in _NUMERIC_KINDS
            )

        def _read_from_group(group) -> list[dict]:
            """Decode all signals from an HDF5 group (root or struct sub-group).
            MCOS objects, char arrays, non-timeseries structs ares skipped silently.
            """
            result = []

            candidate_keys = [k for k in group.keys() if k not in _HDF5_INTERNAL]
            if label_filter is not None:
                candidate_keys = [k for k in candidate_keys if k in label_filter]

            # Lazily resolve the shared flat timestamp vector within this group
            _ts: np.ndarray | None = None
            _ts_resolved = False

            def _get_flat_timestamps() -> np.ndarray | None:
                nonlocal _ts, _ts_resolved
                if _ts_resolved:
                    return _ts
                _ts_resolved = True
                for k in group.keys():
                    if k.lower() in _TIMESTAMP_NAMES and isinstance(
                        group[k], h5py.Dataset # type: ignore
                    ):
                        _ts = Mat73Interface._mat_load_num(group[k])
                        break
                return _ts

            for key in candidate_keys:
                element = group[key]

                if _is_timeseries_group(element):
                    # Layout A / C – group with Time + Data sub-datasets
                    result.append(
                        {
                            "label": key,
                            "timestamps": Mat73Interface._mat_load_num(element["Time"]),
                            "value": Mat73Interface._mat_load_num(element["Data"]),
                        }
                    )
                elif _is_numeric_dataset(element):
                    # Layout B / D – flat numeric dataset; skip timestamp key itself
                    if key.lower() in _TIMESTAMP_NAMES:
                        continue
                    result.append(
                        {
                            "label": key,
                            "timestamps": _get_flat_timestamps(),
                            "value": Mat73Interface._mat_load_num(element),
                        }
                    )

            return result

        # read HDF5 (mat-file)
        with h5py.File(file_path, mode="r") as matfile: # type: ignore
            signals = []
            if struct_name:
                for struct in struct_name:
                    if struct not in matfile:
                        warnings.warn(
                            f"Struct group '{struct}' not found in {file_path}. ",
                            RuntimeWarning,
                        )
                        continue
                    signals.extend(_read_from_group(matfile[struct]))
            else:
                signals.extend(_read_from_group(matfile))
        return signals

    # static, general helper functions
    @staticmethod
    def _get_matlab_class(dtype: np.dtype) -> bytes:
        """Maps a NumPy dtype to the corresponding MATLAB class string."""
        if np.issubdtype(dtype, np.float64):
            return b"double"
        elif np.issubdtype(dtype, np.float32):
            return b"single"
        elif np.issubdtype(dtype, np.int8):
            return b"int8"
        elif np.issubdtype(dtype, np.uint8):
            return b"uint8"
        elif np.issubdtype(dtype, np.int16):
            return b"int16"
        elif np.issubdtype(dtype, np.uint16):
            return b"uint16"
        elif np.issubdtype(dtype, np.int32):
            return b"int32"
        elif np.issubdtype(dtype, np.uint32):
            return b"uint32"
        elif np.issubdtype(dtype, np.int64):
            return b"int64"
        elif np.issubdtype(dtype, np.uint64):
            return b"uint64"
        elif np.issubdtype(dtype, np.bool_):
            return b"logical"
        else:
            return b"double"

    @staticmethod
    def _mat_load_num(
        dataset: h5py.Dataset, # type: ignore
    ) -> np.ndarray:
        """Load numerical data from h5py dataset and adjust dimensions."""
        samples = np.squeeze(dataset[()], axis=None)
        if len(samples.shape) > 1:
            samples = samples.T
        return samples

    # INFO: the following functions are currently not used, useful to read more complex data
    @staticmethod
    def _mat_load_string(file: h5py.File, dataset: h5py.Dataset) -> np.ndarray: # type: ignore
        """Load string data from h5py dataset."""
        n_el = dataset.shape[1]
        el_string = []
        for ii in range(n_el):
            el_string.append(bytes(np.array(file[dataset[0, ii]]))[::2].decode())
        return np.asarray(el_string)

    @staticmethod
    def _mat_load_numstring(dataset: h5py.Dataset) -> np.ndarray | str: # type: ignore
        """Load numeric string data from h5py dataset."""
        try:
            samples = bytes(dataset[()])[::2].decode()
        except Exception:
            samples = np.squeeze(dataset[()], axis=None)
            if len(samples.shape) > 1:
                samples = samples.T
        return samples
