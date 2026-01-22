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

Copyright 2025 olympus-tools contributors. Contributors to this project
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
import os
from typing import ClassVar, override

import numpy as np
from asammdf import MDF, Signal, Source

from ares.interface.data.ares_data_interface import AresDataInterface
from ares.interface.data.ares_signal import AresSignal
from ares.utils.decorators import error_msg, safely_run
from ares.utils.decorators import typechecked_dev as typechecked
from ares.utils.logger import create_logger

logger = create_logger(__name__)

# define obsolete channels that are ALWAYS skipped
OBSOLETE_SIGNALS = ["time"]


class MF4Handler(MDF, AresDataInterface):
    """A extension of the asammdf.MDF class to allow ARES to interact with mf4's.
    see: https://asammdf.readthedocs.io/en/latest/api.html#asammdf.mdf.MDF
    """

    DTYPE_MAP: ClassVar[dict[np.dtype, str]] = {
        np.dtype(np.float32): "<f4",
        np.dtype(np.float64): "<f8",
        np.dtype(np.bool_): "<u1",
        np.dtype(np.int8): "<i1",
        np.dtype(np.int16): "<i2",
        np.dtype(np.int32): "<i4",
        np.dtype(np.int64): "<i8",
        np.dtype(np.uint8): "<u1",
        np.dtype(np.uint16): "<u2",
        np.dtype(np.uint32): "<u4",
        np.dtype(np.uint64): "<u8",
    }

    @typechecked
    def __init__(
        self,
        file_path: str | None,
        **kwargs,
    ):
        """Initialize MF4Handler and load available channels.

        Checks if asammdf MDF is already initialized to avoid duplicate initialization.
        In read mode, loads the mf4 file.
        In write mode, creates an empty MDF instance plus adds signals if any are given.

        Args:
            file_path (str | None): Path to the mf4 file to load or write.
            **kwargs (Any): Additional arguments passed to asammdf's MDF constructor.
        """

        AresDataInterface.__init__(self, file_path=file_path, **kwargs)

        data = kwargs.pop("data", [])
        if file_path is None or file_path == "":
            super().__init__(**kwargs)
            self._available_signals: list[str] = []

            if data is None:
                return
            else:
                self.add(data=data, **kwargs)
                return

        else:
            if not os.path.isfile(file_path):
                raise FileNotFoundError(
                    "The signal file requested to read doesn't exist. File requested: {file_path}"
                )
            super().__init__(file_path, **kwargs)
            self._available_signals = list(self.channels_db.keys())

            for obs_channel in OBSOLETE_SIGNALS:
                if obs_channel in self._available_signals:
                    self._available_signals.remove(obs_channel)

    @override
    @safely_run(
        default_return=None,
        exception_msg="For some reason the .mf4 file could not be saved.",
        log=logger,
        include_args=["output_path"],
    )
    @typechecked
    def _save(self, output_path: str, **kwargs) -> None:
        """Save mf4 file with timestamp in header comment.

        Wrapper for asammdf's MDF.save() that adds a timestamp to the file header.

        Args:
            output_path (str): Absolute path where the mf4 file should be written.
            **kwargs (Any): Additional arguments passed to MDF.save().
        """

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.header.comment = f"File last saved on: {timestamp}"
        result_path = self.save(output_path, **kwargs)
        logger.info(f"Successfully saved mf4 data file: {result_path}")

    @override
    @error_msg(
        exception_msg="Error in mf4-handler get function.",
        log=logger,
        include_args=["label_filter"],
    )
    @typechecked
    def get(
        self, label_filter: list[str] | None = None, **kwargs
    ) -> list[AresSignal] | None:
        """Get signals from mf4 file with optional resampling.

        Args:
            label_filter (list[str] | None): List of signal names to read from mf4 file.
                If None, all available signals are read. Defaults to None.
            **kwargs (Any): Additional arguments. 'stepsize' (int) triggers resampling.

        Returns:
            list[AresSignal] | None: List of AresSignal objects, optionally resampled to common time vector.
                Returns None if no signals were found.
        """
        stepsize = kwargs.pop("stepsize", None)
        tmp_data = (
            self._get_signals(self._available_signals)
            if label_filter is None
            else self._get_signals(label_filter, **kwargs)
        )

        if not tmp_data:
            return None

        if stepsize is None:
            return tmp_data
        else:
            return self._resample(data=tmp_data, stepsize=stepsize)

    @typechecked
    def _get_signals(self, label_filter: list[str], **kwargs) -> list[AresSignal]:
        """Helper function for get() that handles multiple occurrences of signals in mf4 files.

        Uses asammdf's whereis() function to locate signals and selects the signal
        with the most samples when multiple occurrences exist. Missing signals are
        skipped with a warning instead of causing errors.

        Args:
            label_filter (list[str]): List of signal names to retrieve from the mf4 file.
            **kwargs (Any): Additional arguments passed to asammdf's select() method.

        Returns:
            list[AresSignal]: List of AresSignal objects extracted from the mf4 file.
                Only contains signals that were actually found.
        """

        found_signals: list[Signal] = []

        for channel_name in label_filter:
            logger.debug(f"Processing channel: {channel_name}")
            occurence = self.whereis(channel_name)

            if len(occurence) == 0:
                logger.warning(
                    f"Signal '{channel_name}' not found in mf4 file. Skipping."
                )
                continue

            if len(occurence) == 1:
                logger.debug(
                    f"Signal '{channel_name}' has single occurrence in mf4 data file."
                )
                selected_signal = super().select([channel_name], **kwargs)
                if selected_signal:
                    found_signals.extend(selected_signal)

            else:
                logger.debug(
                    f"Signal '{channel_name}' has {len(occurence)} occurrences in mf4 data file."
                )
                sel_signal = [(None, gp_idx, cn_idx) for gp_idx, cn_idx in occurence]
                all_signals = super().select(sel_signal, **kwargs)
                len_samples = [len(s.samples) for s in all_signals]
                idx = len_samples.index(max(len_samples))
                logger.debug(
                    f"Selected occurrence {idx} with {len_samples[idx]} samples."
                )
                found_signals.append(all_signals[idx])

        ares_signals = []
        for signal in found_signals:
            if hasattr(signal.samples.dtype, "names") and signal.samples.dtype.names:
                value = signal.samples[signal.name]
                logger.debug(
                    f"Array signal '{signal.name}' extracted with shape: {value.shape}"
                )
            else:
                value = signal.samples
                logger.debug(f"Scalar signal '{signal.name}' with shape: {value.shape}")

            ares_signals.append(
                AresSignal(
                    label=signal.name,
                    timestamps=signal.timestamps,
                    value=value,
                    unit=signal.unit if hasattr(signal, "unit") else None,
                    description=signal.comment if hasattr(signal, "comment") else None,
                )
            )

        return ares_signals

    @override
    @error_msg(
        exception_msg="Error in mf4-handler add function.",
        log=logger,
    )
    @typechecked
    def add(self, data: list[AresSignal], **kwargs) -> None:
        """Add AresSignal objects to mf4 file.

        Converts AresSignal objects to asammdf Signal format and appends them to the mf4 file.
        Supports scalar signals (1D), 1D array signals (2D), and 2D array signals (3D).
        Optionally adds source information to data for traceability.

        Args:
            data (list[AresSignal]): List of AresSignal objects to append to mf4 file.
                - ndim == 1: Scalar value per time step
                - ndim == 2: 1D array per time step (shape: cycles, array_size)
                - ndim == 3: 2D array per time step (shape: cycles, rows, cols)
            **kwargs (Any): Additional arguments:
                - source_name (str): Name for the signal source. If not provided,
                  defaults to "ARES_DEFAULT_SOURCE".
        """
        source_name = kwargs.pop("source_name", "ARES_DEFAULT_SOURCE")

        source = Source(
            name=source_name,
            path=source_name,
            comment=f"Data source: {source_name}",
            source_type=1,
            bus_type=1,
        )

        signals_to_write = []
        for sig in data:
            if sig.ndim == 1:
                signals_to_write.append(
                    Signal(
                        samples=sig.value,
                        timestamps=sig.timestamps,
                        name=sig.label,
                        unit=sig.unit if sig.unit else "",
                        comment=sig.description if sig.description else "",
                        source=source,
                        encoding="utf-8",
                    )
                )

            elif sig.ndim in [2, 3]:
                dtype_str = self.DTYPE_MAP[sig.dtype]

                if sig.ndim == 2:
                    array_size = sig.shape[1]
                    dimension_str = f"({array_size},)"
                else:
                    rows, cols = sig.shape[1], sig.shape[2]
                    dimension_str = f"({rows}, {cols})"

                types = [(sig.label, f"{dimension_str}{dtype_str}")]
                samples = np.rec.fromarrays([sig.value], dtype=np.dtype(types))

                signals_to_write.append(
                    Signal(
                        samples=samples,
                        timestamps=sig.timestamps,
                        name=sig.label,
                        unit=sig.unit if sig.unit else "",
                        comment=sig.description if sig.description else "",
                        source=source,
                        encoding="utf-8",
                    )
                )

            else:
                logger.warning(
                    f"Unsupported signal dimension: {sig.ndim}. Supported: 1 (scalar), 2 (1D array/timestep), 3 (2D array/timestep)"
                )

        self.append(signals_to_write)
        [self._available_signals.append(signal.label) for signal in data]
