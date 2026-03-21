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
from typing import Any, Iterable, Literal, TypedDict

import h5py
import numpy as np
import scipy.io as sio

DEFAULT_TIMESTAMP = "timestamps"  # default name of "timestamps" for flat signals


class MatSignal(TypedDict):
    label: str
    timestamps: np.ndarray
    value: np.ndarray


class MatInterface:
    """A standalone interface for reading and writing MATLAB MAT-files supporting
        - v7.3 files (HDF5 based)
        - v7.0/6.0 files (via scipy)

    The MatInterface is based on python standard interfaces to guarantee easy usage and minimum dependencies.

    additional information see:
    https://de.mathworks.com/help/matlab/import_export/mat-file-versions.html?s_tid=srchtitle_site_search_1_mat+files
    https://www.hdfgroup.org/solutions/hdf5/
    https://docs.scipy.org/doc/scipy/reference/generated/scipy.io.loadmat.html
    """

    @staticmethod
    def write(
        output_path: Path,
        signals: list[MatSignal],
        format: Literal["v7.3", "v7"] = "v7.3",
        **kwargs,
    ) -> None:
        """Write signals to a MAT 7.3 (HDF5) or lower.

        Args:
            output_path (Path): Path to the output file.
            signals (list[dict]): List of dicts, each with:
                - ``'label'``      (str):        signal name
                - ``'timestamps'`` (np.ndarray): 1-D time vector
                - ``'value'``      (np.ndarray): 1-D / 2-D / 3-D value array
        """
        if format == "v7.3":
            MatInterface._write73(output_path=output_path, signals=signals, **kwargs)
        elif format == "v7":
            MatInterface._write7(output_path=output_path, signals=signals, **kwargs)

    @staticmethod
    def get(
        file_path: Path,
        label_filter: list[str] | None = None,
        struct_list: list[str] | None = None,
        **kwargs,
    ) -> list[MatSignal]:
        """Read signals from a MAT 7.3 (HDF5) or lower.

        Supports two modes (defined via struct_list):
            - flat   : signals exist at the highest layer
            - struct : signals are divided into structs each with providing its own timestamp

        where each mode can read two types of signals:
            - **timeseries struct layout**: each signal is a struct containing "Time","Data"
            - **flat signal arrays**: each signal is a array whereas one array represents the shared timestamp

        Note: MATLAB MCOS ``timeseries`` *objects* (``MATLAB_object_decode==3``)
        store their data in an opaque ``#refs#`` pool and cannot be decoded
        without a full MATLAB OOP deserialiser.
        Therefore not the 'real' MATLAB timeseries supported.

        Assumptions:
        Considering the ''flat'' signal structure the assumption that the shared timevector is called
            - timestamps
        is made.

        Args:
            file_path (Path): Path to the MAT file.
            label_filter (list[str] | None): List of signal names to read.
            struct_list (list[str] | None): List of structs which contain the signals to extract.

        Returns:
            list[dict]: List of ``{'label', 'timestamps', 'value'}`` dicts.
        """
        matfile_version = sio.matlab.matfile_version(file_path)

        if matfile_version[0] == 2:
            signal_data = MatInterface._get73(
                file_path=file_path,
                label_filter=label_filter,
                struct_list=struct_list,
                **kwargs,
            )
        elif matfile_version[0] == 1:
            signal_data = MatInterface._get7(
                file_path=file_path,
                label_filter=label_filter,
                struct_list=struct_list,
                **kwargs,
            )
        else:
            raise ValueError(f"Unsupported/Unknown matfile-version {matfile_version}.")
        return signal_data

    # MAT 7.0 functions (scipy wrapper)
    @staticmethod
    def _write7(output_path: Path, signals: list[MatSignal]) -> None:
        """Write signals to a MAT 7.0 file via scipy.

        Args:
            output_path (Path): Path to the output file.
            signals (list[dict]): List of dicts, each with:
                - ``'label'``      (str):        signal name
                - ``'timestamps'`` (np.ndarray): 1-D time vector
                - ``'value'``      (np.ndarray): 1-D / 2-D / 3-D value array
        """
        # defaults for saving with scipy.sio
        kw = dict(
            oned_as="column",
            long_field_names=True,
            do_compression=True,
        )

        mat_data_dict = {}
        for signal in signals:
            mat_data_dict[signal["label"]] = {
                "Time": signal["timestamps"],
                "Data": signal["value"],
                "Events": np.array([]),  # Empty array for MATLAB compatibility
            }
        sio.savemat(output_path, mat_data_dict, **kw)

    @staticmethod
    def _get7(
        file_path: Path,
        label_filter: list[str] | None = None,
        struct_list: list[str] | None = None,
        **kwargs,
    ) -> list[MatSignal]:
        """Read signals from a MAT 7.0 or lower file via scipy.io package.

        Args:
            file_path (Path): Path to the MAT file.
            label_filter (list[str] | None): List of signal names to read.
            struct_list (list[str] | None): List of structs which contain the signals to extract.
            **kwargs : additional arguments passed to scipy "loadmat"

        Returns:
            list[dict]: List of ``{'label', 'timestamps', 'value'}`` dicts.
        """
        _OBSOLETE_MATFIELDS = [
            "__header__",
            "__version__",
            "__globals__",
        ]  # define obsolete mat fields thar are always skipped during reading and define default timestamp
        _TIMESTAMP = DEFAULT_TIMESTAMP
        mat_data: list[MatSignal] = []

        # helper functions for scipy (transform to standard format)
        def _get_timeseries(
            tmp_data: dict[str, Any], label_filter: list[str]
        ) -> list[MatSignal]:
            """Read timeseries struct from mat file."""
            nonlocal mat_data
            signals_to_add: Iterable[MatSignal] = [
                {
                    "label": signal_name,
                    "timestamps": signal_dict.get("Time"),
                    "value": signal_dict.get("Data"),
                }
                for signal_name, signal_dict in tmp_data.items()
                if signal_name not in _OBSOLETE_MATFIELDS  # skip mat-fields
                and (not label_filter or signal_name in label_filter)  # label-filter
                and type(signal_dict) is dict  # check 'timeseries'-struct
                and "Time" in signal_dict
                and "Data" in signal_dict
            ]
            mat_data.extend(signals_to_add)
            return mat_data

        def _get_signals(
            tmp_data: dict[str, Any],
            timestamps: np.ndarray,
            label_filter: list[str],
        ) -> list[MatSignal]:
            """Read flat signals from mat file."""
            nonlocal mat_data
            signals_to_add: Iterable[MatSignal] = [
                {
                    "label": signal_name,
                    "timestamps": timestamps,
                    "value": signal_value,
                }
                for signal_name, signal_value in tmp_data.items()
                if signal_name not in _OBSOLETE_MATFIELDS  # skip mat-fields
                and signal_name != _TIMESTAMP  # skip timestamp itself
                and (not label_filter or signal_name in label_filter)  # label-filter
                and isinstance(signal_value, np.ndarray)  # Ensure it's a numpy array
            ]
            mat_data.extend(signals_to_add)
            return mat_data

        # define standard flags to guarantee readability
        kwargs = {**kwargs}
        kwargs.setdefault("simplify_cells", True)
        tmp_data = sio.loadmat(file_path, **kwargs)

        # differentiate between struct-mode, plain-mode, timeseries
        if struct_list:
            tmp_data.update([tmp_data.get(struct) for struct in struct_list])

        # check for timessignal -> timeseries or plain-mode
        timestamps = tmp_data.get(_TIMESTAMP, None)
        if timestamps is None:
            mat_data = _get_timeseries(tmp_data, label_filter if label_filter else [])
        else:
            mat_data = _get_signals(
                tmp_data, timestamps, label_filter if label_filter else []
            )
        return mat_data

    # MAT 7.3 functions
    @staticmethod
    def _write73(
        output_path: Path,
        signals: list[MatSignal],
    ) -> None:
        """Write signals to a MAT 7.3 file (HDF5).
        Each signal is stored as a top-level HDF5 group containing three members:
        - ``Time``   – 1-D dataset, timestamps (double)
        - ``Data``   – 1-D or N-D dataset, signal values
        - ``Events`` – empty group (reserved for MATLAB compatibility)

        The group carries ``MATLAB_class = "timeseries"`` and ``MATLAB_fields``
        attributes so that MATLAB's ``load()`` recognises the layout.
        Note:
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
                event_group = group.create_group("Events")
                event_group.attrs["MATLAB_class"] = np.bytes_(b"struct")
                _write_mat_fields(event_group)

                # write timestamp
                timestamps_single = timestamps.astype(np.float32)
                ti = group.create_dataset("Time", data=timestamps_single.T)
                _write_ds_matlab_class(ti.id, b"single")

                # bool/logical: MATLAB requires uint8 storage
                if np.issubdtype(dtype, np.bool_):
                    value = value.astype(np.uint8)
                # write signal data
                if value.ndim <= 2:
                    ds = group.create_dataset("Data", data=value.T)
                elif value.ndim == 3:
                    ds = group.create_dataset("Data", data=value.transpose(2, 1, 0))
                else:
                    raise ValueError(
                        "MatInterface does not support more than 3 dimensions."
                    )
                _write_ds_matlab_class(ds.id, MatInterface._get_matlab_class(dtype))

                # bool/logical: MATLAB requires MATLAB_int_decode=1
                if np.issubdtype(dtype, np.bool_):
                    ds.attrs["MATLAB_int_decode"] = np.uint8(1)

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
    def _get73(
        file_path: Path,
        label_filter: list[str] | None = None,
        struct_list: list[str] | None = None,
    ) -> list[MatSignal]:
        """Read signals from a MAT 7.3 file.

        Args:
            file_path (Path): Path to the MAT file.
            label_filter (list[str] | None): List of signal names to read.
            struct_list (list[str] | None): List of structs which contain the signals to extract.

        Returns:
            list[dict]: List of ``{'label', 'timestamps', 'value'}`` dicts.
        """
        _HDF5_INTERNAL = {"#refs#", "#subsystem#"}
        _NUMERIC_KINDS = set("bifcu")
        _TIMESERIES_KEYS = {
            "Data",
            "Time",
        }  # Events can be ignored, only important for writing
        _TIMESTAMP_NAMES = {DEFAULT_TIMESTAMP}

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
                isinstance(obj, h5py.Dataset)  # type: ignore
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

            # resolve the shared flat timestamp vector
            _ts: np.ndarray | None = None
            _ts_resolved = False

            def _get_flat_timestamps() -> np.ndarray | None:
                nonlocal _ts, _ts_resolved
                if _ts_resolved:
                    return _ts
                _ts_resolved = True
                for k in group.keys():
                    if k.lower() in _TIMESTAMP_NAMES and isinstance(
                        group[k],
                        h5py.Dataset,  # type: ignore
                    ):
                        _ts = MatInterface._mat_load_num(group[k])
                        break
                return _ts

            for key in candidate_keys:
                element = group[key]

                if _is_timeseries_group(element):
                    # Layout A / C – group with Time + Data sub-datasets
                    result.append(
                        {
                            "label": key,
                            "timestamps": MatInterface._mat_load_num(element["Time"]),
                            "value": MatInterface._mat_load_num(element["Data"]),
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
                            "value": MatInterface._mat_load_num(element),
                        }
                    )

            return result

        # read HDF5 (mat-file)
        with h5py.File(file_path, mode="r") as matfile:  # type: ignore
            signals = []
            if struct_list:
                for struct in struct_list:
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
        dataset: h5py.Dataset,  # type: ignore
    ) -> np.ndarray:
        """Load numerical data from h5py dataset and adjust dimensions."""
        samples = np.squeeze(dataset[()], axis=None)
        if len(samples.shape) > 1:
            samples = samples.T
        return samples

    # INFO: the following functions are currently not used, useful to read more complex data
    @staticmethod
    def _mat_load_string(file: h5py.File, dataset: h5py.Dataset) -> np.ndarray:  # type: ignore
        """Load string data from h5py dataset."""
        n_el = dataset.shape[1]
        el_string = []
        for ii in range(n_el):
            el_string.append(bytes(np.array(file[dataset[0, ii]]))[::2].decode())
        return np.asarray(el_string)

    @staticmethod
    def _mat_load_numstring(dataset: h5py.Dataset) -> np.ndarray | str:  # type: ignore
        """Load numeric string data from h5py dataset."""
        try:
            samples = bytes(dataset[()])[::2].decode()
        except Exception:
            samples = np.squeeze(dataset[()], axis=None)
            if len(samples.shape) > 1:
                samples = samples.T
        return samples
