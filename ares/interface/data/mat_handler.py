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

from pathlib import Path
from typing import Any, override

import numpy as np
import scipy.io as sio
from mat73_interface.mat73_interface import Mat73Interface

from ares.interface.data.ares_data_interface import AresDataInterface
from ares.interface.data.ares_signal import AresSignal
from ares.utils.decorators import error_msg, safely_run
from ares.utils.decorators import typechecked_dev as typechecked
from ares.utils.logger import create_logger

logger = create_logger(__name__)

# define obsolete mat fields thar are always skipped during reading and define default timestamp
OBSOLETE_MATFIELDS = ["__header__", "__version__", "__globals__"]
TIMESTAMP = "timestamps"


class MATHandler(AresDataInterface):
    """A class to allow ARES to interact with *.mat files.

    Mat-files can come in in 2 major versions:
    - Version 7.3 = HDF5 based with specific matlab header
    - Version 7/6/4 = matlab specific format (legacy)

    To handle both versions the packages:
    - h5py ( version 7.3 )
    - scipy ( version 7/6/4 )
    are used.

    note: for version 7.3 based on h5py and own ares-package MAT73Interface was implemented.
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
        In write mode, collects given signals and writes them to a mat-file.

        Currently the following formats of stored data in mats are supported:
            read:
                - 'flat' signal structure (shared timevector for all signals)
                - 'flat' timeseries structure (each signal has its own timevector)
                - 'struct' signal structure each with signals (shared timevector per struct)
                - 'struct' timeseries structure each with timeseries structs
            write:
                - 'timeseries'-struct with fields 'Time','Data' (see MAT73Interface for more information)

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
        self._available_signals: list[str] = []

        if file_path is None:
            if data:
                self.add(data=data, **kwargs)
        else:
            self.matfile_vers = sio.matlab.matfile_version(file_path)
            self.file_path = str(file_path)

    @override
    @safely_run(
        default_return=None,
        exception_msg="For some reason the .mat file could not be saved.",
        log=logger,
        include_args=["output_path"],
    )
    @typechecked
    def _save(self, output_path: Path, **kwargs) -> None:
        """Save mat file. Default is version 7.3.

        Args:
            output_path (str): Absolute path where the mat file should be written.
            **kwargs (Any): Additional arguments passed to MAt73Interface.write() or scipy.savemat().
        """
        file_format = kwargs.pop("method", "mat73")

        if file_format == "mat73":
            signals = [
                {
                    "label": signal.label,
                    "timestamps": signal.timestamps,
                    "value": signal.value,
                }
                for signal in self.data
            ]

            Mat73Interface.write(output_path, signals)
            logger.info(f"Successfully saved mat data file: {output_path}")
        elif file_format == "mat7":
            # default scipy write options: https://docs.scipy.org/doc/scipy/reference/generated/scipy.io.savemat.html
            kw = dict(
                oned_as="column",
                long_field_names=True,
                do_compression=True,
            )

            mat_data_dict = {}
            for signal in self.data:
                mat_data_dict[signal.label] = {
                    "Time": signal.timestamps,
                    "Data": signal.value,
                    "Events": np.array([]),  # Empty array for MATLAB compatibility
                }
            sio.savemat(output_path, mat_data_dict, **kw)
        else:
            raise Exception(
                f"Unknown mat file-format: {file_format} given. Not implemented."
            )

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
            **kwargs (Any): Additional arguments.
                'stepsize' (int): triggers resampling
                'struct_name' (list[str]): read from specific structs

        Returns:
            list[AresSignal] | None: List of AresSignal objects, optionally resampled to common time vector.
                Returns None if no signals were found.
        """
        mat_data = []
        struct_name = kwargs.pop("struct_name", None)
        vstack_pattern = (
            self._vstack_pattern
            if vstack_pattern is None
            else (self._vstack_pattern or []) + vstack_pattern
        )

        if self.matfile_vers[0] == 2:
            # read mat via MAT73Interface
            signals_data = Mat73Interface.get_signals(
                file_path=Path(self.file_path),
                label_filter=label_filter,
                struct_name=struct_name,
            )

            # extend available signals variable
            self._available_signals.extend(sig["label"] for sig in signals_data)

            for sig in signals_data:
                label = sig["label"]
                value = sig["value"]
                timestamps = sig["timestamps"]

                mat_data.append(
                    AresSignal(label=label, value=value, timestamps=timestamps)
                )

        elif self.matfile_vers[0] == 1:
            # helper functions for scipy
            def _get_timeseries(
                tmp_data: dict[str,Any], label_filter: list[str]
            ) -> list[AresSignal]:
                """Read timeseries struct from mat file."""
                mat_data: list[AresSignal] = list()
                mat_data.extend(
                    AresSignal(
                        label=signal_name,
                        timestamps=signal_dict.get("Time"),
                        value=signal_dict.get("Data"),
                    )
                    for signal_name, signal_dict in tmp_data.items()
                    if signal_name not in OBSOLETE_MATFIELDS  # skip mat-fields
                    and signal_name
                    not in label_filter  # skip signals not in label-filter
                    and type(signal_dict) == dict  # check 'timeseries'-struct
                    and "Time" in signal_dict
                    and "Data" in signal_dict
                )
                return mat_data

            def _get_signals(
                tmp_data: dict[str,Any], timestamps: np.ndarray, label_filter: list[str]
            ) -> list[AresSignal]:
                """Read flat signals from mat file."""
                mat_data: list[AresSignal] = list()
                mat_data.extend(
                    AresSignal(
                        label=signal_name, timestamps=timestamps, value=signal_value
                    )
                    for signal_name, signal_value in tmp_data.items()
                    if signal_name not in OBSOLETE_MATFIELDS  # skip mat-fields
                    and signal_name
                    not in label_filter  # skip signals not in label-filter
                )
                return mat_data

            # read mat via scipy
            # define standard flags to guarantee readability
            kwargs = {**kwargs}
            kwargs.setdefault("simplify_cells", True)
            tmp_data = sio.loadmat(self.file_path, **kwargs)

            # differentiate between struct-mode, plain-mode, timeseries
            if struct_name:
                tmp_data.update([tmp_data.get(struct) for struct in struct_name])

            # check for timessignal -> timeseries or plain-mode
            timestamps = tmp_data.get(TIMESTAMP, None)
            if timestamps is None:
                mat_data = _get_timeseries(
                    tmp_data, label_filter if label_filter else []
                )
            else:
                mat_data = _get_signals(
                    tmp_data, timestamps, label_filter if label_filter else []
                )

            # extend available signals variable
            [
                self._available_signals.append(signal_name)
                for signal_name in tmp_data.keys()
                if signal_name not in OBSOLETE_MATFIELDS
            ]

        if not mat_data:
            return None

        if vstack_pattern:
            logger.debug(
                f"Vertical stacking will be applied considering regex: {vstack_pattern}."
            )
            mat_data = self._vstack(data=mat_data, vstack_pattern=vstack_pattern)

        if stepsize:
            logger.debug(f"Resampling all signals to: {stepsize} ms.")
            return self._resample(data=mat_data, stepsize=stepsize)
        else:
            return mat_data

    @override
    @error_msg(
        exception_msg="Error in mat-handler add function.",
        log=logger,
    )
    @typechecked
    def add(self, data: list[AresSignal], **kwargs) -> None:
        """Add AresSignal objects to mat file.

        Args:
            data (list[AresSignal]): List of AresSignal objects to append to mat file.
            **kwargs (Any): Additional arguments:
        """
        self.data.extend(data)
        [self._available_signals.append(signal.label) for signal in data]
