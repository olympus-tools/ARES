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
from pathlib import Path
from typing import override

import h5py
import numpy as np
import scipy.io as sio

from ares.interface.data.ares_data_interface import AresDataInterface
from ares.interface.data.ares_signal import AresSignal
from ares.utils.decorators import error_msg, safely_run
from ares.utils.decorators import typechecked_dev as typechecked
from ares.utils.logger import create_logger
from ares.utils.resolve_label_filter import resolve_label_filter

logger = create_logger(__name__)


# TODO: cleanup
# additional functions to load mat 7.3 file (h5)
# file = operator on file in loop
def mat_load_string(file, dataset):
    n_el = dataset.shape[1]
    el_string = list()

    # read string from h5py and decode it (file[file[i][j][0,ii]] to access element)
    for ii in range(n_el):
        el_string.append(bytes(np.array(file[dataset[0, ii]]))[::2].decode())
    el_string = np.asarray(el_string)
    return el_string


def mat_load_numstring(dataset):
    try:
        # sig = bytes(np.array(dataset))[::2].decode()
        samples = bytes(dataset[()])[::2].decode()
    except:
        samples = np.squeeze(dataset[()], axis=None)

        if len(samples.shape) > 1:
            samples = samples.T
    return sampleist - views


def mat_load_num(dataset):
    # remove axis of numpy array (scipy loads only with one shape)
    samples = np.squeeze(dataset[()], axis=None)

    # check dimension (scipy loads in format x,dim - h5py in format dim,x)
    if len(samples.shape) > 1:
        samples = samples.T
    return samples


class MATHandler(AresDataInterface):
    """A class to allow ARES to interact with *.mat files.
    Mat-files can come in in 2 major versions:
    - Version 7.3 = HDF5 based
    - Version 7/6/4 = matlab specific format (legacy)

    To handle both versions the packages:
    - h5py ( for versions 7.3, currently only simple datatypes as arrays are supported )
    - scipy ( for legacy versions )
    are used.

    additional information see:
    https://de.mathworks.com/help/matlab/import_export/mat-file-versions.html?s_tid=srchtitle_site_search_1_mat+files
    https://www.hdfgroup.org/solutions/hdf5/
    """

    def __init__(
        self,
        file_path: Path | None = None,
        data: list[AresSignal] | None = None,
        vstack_pattern: list[str] | None = None,
        **kwargs,
    ):
        """Initialize MATHandler and load available signals.

        Checks if mat is already initialized to avoid dublicate initialization.
        In read mode, loads the mat file.
        In write mode, create an empty h5py instance plus adds signals if any are given.

        Args:
            file_path (Path | None): Path to the mf4 file to load or write.
            data (list[AresSignal] | None): Optional list of AresSignal objects to initialize with
            vstack_pattern (list[str] | None): Pattern (regex) used to stack AresSignal's
            **kwargs (Any): Additional arguments passed.
        """
        AresDataInterface.__init__(
            self,
            file_path=file_path,
            dependencies=kwargs.pop("dependencies", None),
            vstack_pattern=vstack_pattern,
        )
        self.data: list[AresSignal] = list()

        if file_path is None:
            self._available_signals: list[str] = []

            if data:
                self.add(data=data, **kwargs)

        else:
            self.matfile_vers = sio.matlab.matfile_version(file_path)
            self.file_path = str(file_path)
            # FIX: self._available_signals = list(self.channels_db.keys()) | make data a dictionary?

    @override
    @safely_run(
        default_return=None,
        exception_msg="For some reason the .mat file could not be saved.",
        log=logger,
        include_args=["output_path"],
    )
    @typechecked
    def _save(self, output_path: Path, **kwargs) -> None:
        """Save mat file.

        Args:
            output_path (str): Absolute path where the mf4 file should be written.
            **kwargs (Any): Additional arguments passed to MDF.save().
        """
        self._save_mat73(output_path=output_path)

    @typechecked
    def _save_mat73(
        self,
        output_path: Path,
        **kwargs,
    ):
        """Helper function to save file in the modern compressed 7.3 format (hdf5).
        see: https://www.mathworks.com/help/pdf_doc/matlab/matfile_format.pdf (version5 header)
        """
        with h5py.File(output_path, "w", userblock_size=512) as f:
            # HDF5 attribute encoding: MATLAB R2023b-written .mat 7.3 file:
            #  MATLAB_class on groups  → H5T_STRING, NULLPAD (strpad=1), size=len(class_name)
            #                          → numpy S-bytes scalar (h5py maps S-dtype → NULLPAD)
            #
            #  MATLAB_class on datasets → H5T_STRING, NULLTERM (strpad=0), size=8 always
            #                           → ONLY achievable via the low-level h5py.h5a API;
            #                              h5py.string_dtype() and numpy S-dtype both produce NULLPAD
            #
            #  MATLAB_fields           → H5T_VLEN of H5T_STRING(size=1, NULLTERM)
            #                            Each field name is a vlen array of individual S1 chars.
            #                          → numpy object array where each element is np.array([b'T',b'i',...], dtype='S1')
            #                            Low-level HDF5 type for dataset MATLAB_class: NULLTERM, size=8
            _ds_class_tid = h5py.h5t.py_create(np.dtype("S8"))
            _ds_class_tid.set_strpad(h5py.h5t.STR_NULLTERM)
            _ds_class_sid = h5py.h5s.create(h5py.h5s.SCALAR)

            def _write_ds_matlab_class(dataset_id, class_bytes: bytes) -> None:
                """Write MATLAB_class on a dataset as NULLTERM fixed-length 8-byte string.
                Must use low-level API – h5py high-level attrs always writes NULLPAD.
                """
                padded = class_bytes.ljust(8, b"\x00")[:8]
                attr = h5py.h5a.create(
                    dataset_id, b"MATLAB_class", _ds_class_tid, _ds_class_sid
                )
                attr.write(np.frombuffer(padded, dtype="S8"))

            def _mat_fields(*names: str) -> np.ndarray:
                """MATLAB_fields as VLEN-of-S1: each name is an array of individual characters.
                MATLAB stores field names as a variable-length array of single-byte chars,
                not as a flat string. Using a flat fixed-length string causes libmat to
                misread the pointer and crash (access violation in MLClass_to_HDF5Type).
                """
                arr = np.empty(len(names), dtype=object)
                for i, name in enumerate(names):
                    arr[i] = np.array([c.encode("ascii") for c in name], dtype="S1")
                return arr

            # VLEN-of-S1 dtype understood by h5py's attrs.create for correct char-by-char storage
            _vlen_s1_dt = h5py.vlen_dtype(np.dtype("S1"))

            def _write_mat_fields(group, *names: str) -> None:
                """Write MATLAB_fields as H5T_VLEN of H5T_STRING(S1).
                Each field name is stored as a variable-length array of single ASCII chars,
                matching exactly what MATLAB R2023b writes. A flat fixed-length string
                causes libmat's MLClass_to_HDF5Type to crash with an access violation.
                """
                group.attrs.create(
                    "MATLAB_fields", data=_mat_fields(*names), dtype=_vlen_s1_dt
                )

            # internal helper function, creating a matlab "timeseries" – Time, Data, Events
            def add_mat_signal(name, timestamps, data, dtype):
                group = f.create_group(name)
                # MATLAB_class on group: NULLPAD, size = len("timeseries") = 10
                group.attrs["MATLAB_class"] = np.bytes_(b"timeseries")
                _write_mat_fields(group, "Time", "Data", "Events")
                group.create_group("Events")
                # Time dataset: MATLAB_class NULLTERM, size=8
                ti = group.create_dataset("Time", data=timestamps.T)
                _write_ds_matlab_class(
                    ti.id, MATHandler._get_matlab_class(timestamps.dtype)
                )
                if data.ndim <= 2:
                    ds = group.create_dataset("Data", data=data.T)
                elif data.ndim == 3:
                    ds = group.create_dataset("Data", data=data.transpose(2, 1, 0))
                else:
                    raise Exception(
                        "Ares is not supporting more than dimension 3 at the moment."
                    )
                _write_ds_matlab_class(ds.id, MATHandler._get_matlab_class(dtype))

            for signal in self.data:
                # TODO: check if we need the transposed
                # MATLAB v7.3 expects data to be transposed (Column-major)

                add_mat_signal(
                    signal.label, signal.timestamps, signal.value, signal.dtype
                )

        # add matlab specific metadata 128byte header, see matfile_format.pdf or 'hexdump -C -n 128' on *.mat
        # Byte: 0-115 | text | human readable
        date_str = datetime.datetime.now().strftime("%a %b %d %H:%M:%S %Y")
        header = (
            f"MATLAB 7.3 MAT-file, Platform: Python/ARES, Created on: {date_str}".ljust(
                116
            )
        )
        subsystem_offset = (
            b"\x00" * 8
        )  # Byte: 116- 123 | subsystem specific data | all 0 |
        version = 0x0200  # Byte: 124 - 125 | version | 0x0200 or 0x0100 |
        endian = b"IM"  # Byte: 126 - 127 | Endian Indicator | MI BitEndian, IM LittleEndian (Intel/AMD = IM)

        signature = (
            header.encode("ascii")
            + subsystem_offset
            + struct.pack(
                "<H2s", version, endian
            )  # <H2s = < - little endian, H - unsigned short, 2s - 2byte
        )
        if len(signature) != 128:
            raise ValueError(f"Header must be 128 bytes, but got {len(signature)}.")

        # write MAT-signature at the start of the file
        with open(output_path, "r+b") as f:
            f.seek(0)
            f.write(signature)

    @staticmethod
    def _get_matlab_class(dtype: np.dtype):
        """Helper function for _save_mat73.
        Maps a NumPy dtype to the corresponding MATLAB class string.
        """
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

    @override
    @error_msg(
        exception_msg="Error in mf4-handler get function.",
        log=logger,
    )
    @typechecked
    def get(
        self,
        label_filter: list[str] | None = None,
        stepsize: int | None = None,
        vstack_pattern: list[str] | None = None,
        **kwargs,
    ) -> list[AresSignal] | None:
        """Get signals from mat file with optional resampling.

        Args:
            label_filter (list[str] | None): List of signal names or pattern to read from mat file.
                If None, all available signals are read. Defaults to None.
            stepsize (int | None): Step size for resampling signals. If None, no resampling is performed. Defaults to None.
            vstack_pattern (list[str] | None): Pattern (regex) used to stack AresSignal's
            **kwargs (Any): Additional arguments. 'stepsize' (int) triggers resampling.

        Returns:
            list[AresSignal] | None: List of AresSignal objects, optionally resampled to common time vector.
                Returns None if no signals were found.
        """
        # TODO: do we want to load the *.mat-file here or when the __init__ is initialized
        # TODO: what format do we support? (timeseries + structs with timevector?)
        # TODO: implement the whole differentiation under packages?
        if self.matfile_vers[0] == 2:
            with h5py.File(self.file_path, mode="r") as matfile:
                file_content_list = list(matfile.keys())

                # consider label-filter
                if label_filter:
                    file_content_list = resolve_label_filter(
                        label_filter=label_filter, available_elements=file_content_list
                    )

                # init KINDS
                _STRING_KINDS = set("O")
                _NUMERIC_KINDS = set("bifcu")
                _BOTH_KINDS = set("U")

                sampletime: float = 1 / stepsize if stepsize else 0.1
                mat_timeseries = ["Data", "Time", "Events"].sort()

                tmp_data = list()
                for mat_element in file_content_list:
                    if hasattr(matfile[mat_element], "keys"):  # matlab struct
                        struct_content = list(matfile[mat_element].keys())

                        if struct_content.sort() == mat_timeseries:  # matlab timeseries
                            tmp_data.append(
                                AresSignal(
                                    label=mat_element,
                                    timestamps=mat_load_num(
                                        matfile[mat_element]["Time"]
                                    ),
                                    value=mat_load_num(matfile[mat_element]["Data"]),
                                )
                            )
                        else:
                            raise Exception(
                                "Struct in mat-file. Not implemented yet in ARES."
                            )

                    else:  # standard matlab element
                        if matfile[mat_element].dtype.kind in _STRING_KINDS:
                            tmp_var = mat_load_numstring(matfile[mat_element])
                            raise Exception(
                                "String in mat-file. Not implemented yet in ARES."
                            )
                        elif matfile[mat_element].dtype.kind in _NUMERIC_KINDS:
                            tmp_var = mat_load_num(matfile[mat_element])
                            timestamps = np.arange(tmp_var.shape[0]) * sampletime
                            tmp_data.append(
                                AresSignal(
                                    label=mat_element,
                                    timestamps=timestamps,
                                    value=tmp_var,
                                )
                            )
                        elif matfile[mat_element].dtype.kind in _BOTH_KINDS:
                            tmp_var = mat_load_numstring(matfile[mat_element])
                            raise Exception(
                                "NumnericString in mat-file. Not implemented yet in ARES."
                            )
                        else:
                            raise Exception(
                                "Unknown type in mat-file. Not implemented yet in ARES."
                            )

        elif self.matfile_vers[0] == 1:
            # TODO: implement the ARES way
            tmp_data = sio.loadmat(self.file_path, **kwargs)
            raise Exception(
                "Support for mat-files saved with version7 or lower are not implemented yet in ARES."
            )

        if not tmp_data:
            return None

        vstack_pattern = (
            self._vstack_pattern
            if vstack_pattern is None
            else (self._vstack_pattern or []) + vstack_pattern
        )

        if vstack_pattern:
            logger.debug(
                f"Vertical stacking will be applied considering regex: {vstack_pattern}."
            )
            tmp_data = self._vstack(data=tmp_data, vstack_pattern=vstack_pattern)

        if stepsize:
            logger.debug(f"Resampling all signals to: {stepsize} ms.")
            return self._resample(data=tmp_data, stepsize=stepsize)
        else:
            return tmp_data

    @override
    @error_msg(
        exception_msg="Error in mat-handler add function.",
        log=logger,
    )
    @typechecked
    def add(self, data: list[AresSignal], **kwargs) -> None:
        """Add AresSignal objects to mat file.

        Converts AresSignal objects to asammdf Signal format and appends them to the mat file.
        Supports scalar signals (1D), 1D array signals (2D), and 2D array signals (3D).

        Args:
            data (list[AresSignal]): List of AresSignal objects to append to mat file.
                - ndim == 1: Scalar value per time step
                - ndim == 2: 1D array per time step (shape: cycles, array_size)
                - ndim == 3: 2D array per time step (shape: cycles, rows, cols)
            **kwargs (Any): Additional arguments:
        """
        self.data.extend(data)
