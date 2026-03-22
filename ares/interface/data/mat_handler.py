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
from typing import override

from mati.mati import MatInterface, MatSignal

from ares.interface.data.ares_data_interface import AresDataInterface
from ares.interface.data.ares_signal import AresSignal
from ares.pydantic_models.workflow_model import VStackPatternElement
from ares.utils.decorators import error_msg, safely_run
from ares.utils.decorators import typechecked_dev as typechecked
from ares.utils.logger import create_logger

logger = create_logger(__name__)


class MATHandler(AresDataInterface):
    """A class to allow ARES to interact with *.mat files.

    Mat-files can come in in 2 major versions:
    - Version 7.3 = HDF5 based with specific matlab header
    - Version 7/6/4 = matlab specific format (legacy)

    To handle both versions the packages:
    - h5py ( version 7.3 )
    - scipy ( version 7/6/... )
    are used.

    note: for version 7.3 based on h5py and own ares-package MAT73Interface was implemented.
    """

    def __init__(
        self,
        file_path: Path | None = None,
        data: list[AresSignal] | None = None,
        vstack_pattern: list[VStackPatternElement] | None = None,
        stepsize: int | None = None,
        label_filter: list[str] | None = None,
        **kwargs,
    ):
        """Initialize MATHandler and load available signals.

        Checks if mat is already initialized to avoid dublicate initialization.
        In read mode, loads the mat file.
        In write mode, collects given signals and writes them to a mat-file.

        Note:
        The package 'MatInterface' is used.
        In default the data is written in mat version 7.3 in the following format:
            - 'timeseries'-struct with fields 'Time','Data'
        Reading supports all versions and different data-formats are supported.
        For more information see the docs of MatInterface.

        Args:
            file_path (Path | None): Path to the mf4 file to load or write.
            data (list[AresSignal] | None): Optional list of AresSignal objects to initialize with
            vstack_pattern (list[str] | None): Pattern (regex) used to stack AresSignal's
            stepsize (int | None): Optional step size for resampling signals when reading.
            label_filter (list[str] | None): Optional list of signal names or patterns to filter
            **kwargs (Any): Additional arguments passed.
        """
        AresDataInterface.__init__(
            self,
            file_path=file_path,
            dependencies=kwargs.pop("dependencies", None),
            vstack_pattern=vstack_pattern,
            stepsize=stepsize,
            label_filter=label_filter,
        )
        self.data: list[AresSignal] = []
        self._available_signals: list[str] = []

        if file_path is None:
            if data:
                self.add(data=data, **kwargs)
        else:
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
        """Save mat file. Default from MatInterface is version 7.3.

        Args:
            output_path (str): Absolute path where the mat file should be written.
            **kwargs (Any): Additional arguments passed to MatInterface.write().
        """
        signals: list[MatSignal] = [
            {
                "label": signal.label,
                "timestamps": signal.timestamps,
                "value": signal.value,
            }
            for signal in self.data
        ]

        MatInterface.write(output_path, signals, **kwargs)
        logger.info(f"Successfully saved mat data file: {output_path}")

    @override
    @error_msg(
        exception_msg="Error in mat-handler get function.",
        log=logger,
    )
    @typechecked
    def get(
        self,
        label_filter: list[str] | None = None,
        stepsize: int | None = None,
        vstack_pattern: list[VStackPatternElement] | None = None,
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
                'struct_list' (list[str]): read from specific structs

        Returns:
            list[AresSignal] | None: List of AresSignal objects, optionally resampled to common time vector.
                Returns None if no signals were found.
        """
        vstack_pattern = (
            self._vstack_pattern
            if vstack_pattern is None
            else (self._vstack_pattern or []) + vstack_pattern
        )

        label_filter = (
            self._label_filter
            if label_filter is None
            else (self._label_filter or []) + label_filter
        )

        stepsize = self._stepsize if stepsize is None else stepsize

        # check for already loaded signals - otherwise try to load
        missing_signals: list[str] = [
            signal_label
            for signal_label in (label_filter or [])
            if signal_label not in self._available_signals
        ]

        # extend available signals
        if missing_signals or label_filter is None:
            new_signals: list[MatSignal] = MatInterface.get(
                file_path=Path(self.file_path),
                label_filter=missing_signals if label_filter is not None else None,
                **kwargs,
            )

            self._available_signals.extend(
                sig["label"]
                for sig in new_signals
                if sig["label"] not in self._available_signals
            )

            # transform standarized matinterface to AresSignal
            for sig in new_signals:
                label = sig["label"]
                value = sig["value"]
                timestamps = sig["timestamps"]

                self.data.append(
                    AresSignal(label=label, value=value, timestamps=timestamps)
                )
        mat_data: list[AresSignal] = [
            signal
            for signal in self.data
            if (not label_filter or signal.label in label_filter)
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
        # TODO: write available_signals as set
        # Assuming self._available_signals is a set
        # for signal in data:
        #     if signal.label not in self._available_signals:
        #         self.data.append(signal)
        #         self._available_signals.add(signal.label)
        for signal in data:
            if signal.label not in self._available_signals:
                self.data.append(signal)
                self._available_signals.append(signal.label)
