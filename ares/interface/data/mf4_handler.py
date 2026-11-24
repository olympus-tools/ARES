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
from pathlib import Path
from typing import ClassVar, override

import numpy as np
from asammdf import MDF, Signal, Source

from ares.interface.data.ares_data_interface import AresDataInterface
from ares.interface.data.ares_signal import AresSignal
from ares.pydantic_models.workflow_model import VStackPatternElement
from ares.utils.decorators import error_msg, safely_run
from ares.utils.logger import create_logger
from ares.utils.typechecked_dev import typechecked_dev as typechecked

logger = create_logger(name=__name__)

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
        file_path: Path | None = None,
        data: list[AresSignal] | None = None,
        vstack_pattern: list[VStackPatternElement] | None = None,
        stepsize: int | None = None,
        label_filter: list[str] | None = None,
        resample_method: str | None = None,
        resample_tolerance: int | None = None,
        **kwargs,
    ):
        """Initialize MF4Handler and load available channels.

        Checks if asammdf MDF is already initialized to avoid duplicate initialization.
        In read mode, loads the mf4 file.
        In write mode, creates an empty MDF instance plus adds signals if any are given.

        Args:
            file_path (Path | None): Path to the mf4 file to load or write.
            data (list[AresSignal] | None): Optional list of AresSignal objects to initialize with
            vstack_pattern ( list[VStackPatternElement]| None): Pattern (regex) used to stack AresSignal's
            stepsize (int | None): Accepted for compatibility; pass to ``get()`` to
                resample signals.
            label_filter (list[str] | None): Optional list of signal names or patterns to filter
            resample_method (str | None): Accepted for compatibility; pass to ``get()``
                to select the resampling method.
            resample_tolerance (int | None): Accepted for compatibility; pass to
                ``get()`` to set the resampling tolerance.
            **kwargs (Any): Additional arguments passed to asammdf's MDF constructor.
        """

        AresDataInterface.__init__(
            self,
            file_path=file_path,
            dependencies=kwargs.pop("dependencies", None),
            vstack_pattern=vstack_pattern,
            label_filter=label_filter,
        )

        if file_path is None:
            super().__init__(**kwargs)
            self._available_signals: list[str] = []

            if data:
                self.add(data=data, **kwargs)

        else:
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
    def _save(self, output_path: Path, **kwargs) -> None:
        """Save mf4 file with timestamp in header comment.

        Wrapper for asammdf's MDF.save() that adds a timestamp to the file header.

        Args:
            output_path (Path): Absolute path where the mf4 file should be written.
            **kwargs (Any): Additional arguments passed to MDF.save().
        """

        kwargs.pop("meta_data", None)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.header.comment = f"File last saved on: {timestamp}"
        result_path = self.save(output_path, **kwargs)
        logger.info(f"Successfully saved mf4 data file: {result_path.resolve()}.")

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
        resample_tolerance: int | None = None,
        resample_method: str | None = None,
        vstack_pattern: list[VStackPatternElement] | None = None,
        source_priority: list[str] | None = None,
        **kwargs,
    ) -> list[AresSignal] | None:
        """Get signals from mf4 file with optional resampling.

        Args:
            label_filter (list[str] | None): List of signal names or pattern to read from mf4 file.
                If None, all available signals are read. Defaults to None.
            stepsize (int | None): Step size for resampling signals in milliseconds.
                If None, no resampling is performed. Defaults to None.
            resample_tolerance (int | None): Maximum allowed absolute deviation in number
                of timesteps between the current signal time vector (within common overlap)
                and the generated resample time vector. If all signals are within tolerance,
                resampling is skipped. Defaults to None.
            resample_method (str | None): Resampling method forwarded to AresSignal.resample().
                Supported values depend on AresSignal, e.g. "linear", "cubic", "windowedsinc".
                Defaults to None (treated as "linear").
            vstack_pattern (list[VStackPatternElement] | None): Pattern (regex) used to stack AresSignal's.
            source_priority (list[str] | None): Source names ordered from highest to lowest
                priority. If given, only one signal per label is kept before resampling.
                Defaults to None (all occurrences are kept).
            **kwargs (Any): Additional arguments.

        Returns:
            list[AresSignal] | None: List of AresSignal objects, optionally resampled to common time vector.
                Returns None if no signals were found.
        """
        vstack_pattern = (
            self._vstack_pattern
            if vstack_pattern is None
            else (self._vstack_pattern or []) + vstack_pattern
        )

        label_filter = self._label_filter if label_filter is None else label_filter

        tmp_data = (
            self._get_signals(label_filter=self._available_signals, **kwargs)
            if label_filter is None
            else self._get_signals(
                label_filter=self._resolve_label_filter(label_filter=label_filter),
            )
        )

        if not tmp_data:
            return None

        if vstack_pattern:
            logger.debug(
                f"Vertical stacking will be applied considering regex: {vstack_pattern}."
            )
            tmp_data = self._vstack(data=tmp_data, vstack_pattern=vstack_pattern)

        if source_priority is not None:
            tmp_data = self._select_by_source_priority(
                sim_data=tmp_data,
                source_priority=source_priority,
                exceptions=self._get_origin_sources(),
            )

        if stepsize:
            logger.debug(f"Resampling all signals to: {stepsize} ms.")
            return self._resample(
                data=tmp_data,
                stepsize=stepsize,
                resample_method=resample_method,
                resample_tolerance=resample_tolerance,
            )
        else:
            return tmp_data

    @override
    @typechecked
    def get_sources(self) -> set[str | None]:
        """Return the distinct source fields of all available signals.

        Reads the sources from the channel metadata, so no samples are decoded.

        Returns:
            set[str | None]: Unique source values, including None for signals
                without a source; empty if no signals are available.
        """
        labels = (
            self._available_signals
            if self._label_filter is None
            else self._resolve_label_filter(label_filter=self._label_filter)
        )
        sources: set[str | None] = set()
        for label in labels:
            for group_index, channel_index in self.whereis(label):
                source = self.groups[group_index].channels[channel_index].source
                sources.add(source.path if source is not None else None)
        return sources

    def _resolve_label_filter(
        self,
        label_filter: list[str],
    ) -> list[str]:
        """internal function implementation of utility function "resolve_label_filter()".
        Function overrides general implementation in "ares_data_interface" and uses the 'search()'
        provided by the asammdf package. It uses the 'search()' provided by the asammdf package.

        Args:
            label_filter (list[str]): List of signal names/search pattern to retrieve.

        Returns:
            list[str]: List of signal names to extract from given data interace.
        """
        signal_list: list[str] = []
        for regex in label_filter:
            found_labels = self.search(regex, mode="regex")
            if not found_labels:
                logger.debug(
                    f"Label filter '{regex}' did not match any signal in mf4 file."
                )
            else:
                signal_list.extend(found_labels)

        return list(set(signal_list))

    @typechecked
    def _get_signals(
        self,
        label_filter: list[str],
        **kwargs,
    ) -> list[AresSignal]:
        """Helper function for get() that handles multiple occurrences of signals in mf4 files.

        Uses asammdf's whereis() function to locate signals and selects all
        occurrences when a signal name appears multiple times. Unmatched signals
        are skipped.

        Note:
            Per default asammdf's select() with raw=True is used to get the original timestamps, values.
            See the class docstring for the asammdf API reference.

        Args:
            label_filter (list[str]): List of signal names to retrieve from the mf4 file.
            **kwargs (Any): Additional arguments passed to asammdf's select() method.

        Returns:
            list[AresSignal]: List of AresSignal objects extracted from the mf4 file.
                Contains every occurrence of each signal that was found.
        """

        raw = kwargs.pop("raw", True)

        selected_channels: list[tuple[None, int, int]] = []

        for channel_name in label_filter:
            occurrence = self.whereis(channel_name)
            if occurrence:
                logger.debug(
                    f"Signal '{channel_name}' has {len(occurrence)} occurrences in mf4 data file."
                )
                selected_channels.extend(
                    (None, gp_idx, cn_idx) for gp_idx, cn_idx in occurrence
                )

        found_signals = (
            super().select(selected_channels, raw=raw) if selected_channels else []
        )

        ares_signals = []
        for signal in found_signals:
            if hasattr(signal.samples.dtype, "names") and signal.samples.dtype.names:
                value = signal.samples[signal.name]
            else:
                value = signal.samples

            ares_signals.append(
                AresSignal(
                    label=signal.name,
                    timestamps=signal.timestamps,
                    value=value,
                    unit=signal.unit if hasattr(signal, "unit") else None,
                    description=signal.comment if hasattr(signal, "comment") else None,
                    source=signal.source.path
                    if hasattr(signal, "source") and signal.source is not None
                    else None,
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
        Supports scalar signals (1D) and array signals with any number of
        dimensions greater than one.

        asammdf requires all signals of one channel group to share a single time axis.
        Therefore the signals are grouped by source name and exact timestamps array.
        Each group is written with its own append() call (common_timebase=True, so no
        resampling happens) and gets its own Source. Groups of the same source share
        the source name; the Source comment holds a per-source time axis index and a
        description of the time axis. The channel group comment equals the Source comment.

        Signals sharing a label are all written (e.g. the same signal from different
        sources). Resolving duplicate labels is the responsibility of the caller,
        e.g. the merge plugin via ``allow_duplicates_data``.

        Args:
            data (list[AresSignal]): List of AresSignal objects to append to mf4 file.
                Signals may have different time axes.
                - ndim == 1: Scalar value per time step
                - ndim > 1: Array per time step (shape: cycles, *array_shape)
            **kwargs (Any): Not used, accepted for interface compatibility.
        """
        # 1. Group signals by source name and exact time axis (order of first occurrence)
        signal_groups: list[dict] = []
        for signal in data:
            if signal.ndim < 1:
                logger.warning(
                    f"Unsupported signal dimension of signal '{signal.label}': {signal.ndim}."
                )
                continue

            source_name = signal.source or "ARES_DEFAULT_SOURCE"

            matching_group = None
            for group in signal_groups:
                same_source = group["source_name"] == source_name
                same_timestamps = np.array_equal(group["timestamps"], signal.timestamps)
                if same_source and same_timestamps:
                    matching_group = group
                    break

            if matching_group is None:
                matching_group = {
                    "source_name": source_name,
                    "timestamps": signal.timestamps,
                    "fs": signal.fs,
                    "signals": [],
                }
                signal_groups.append(matching_group)

            matching_group["signals"].append(signal)

        # 2. Write each group as its own channel group with its own Source
        time_axis_count_per_source: dict[str, int] = {}
        for group in signal_groups:
            source_name = group["source_name"]
            timestamps = group["timestamps"]
            fs = group["fs"]

            time_axis_index = time_axis_count_per_source.get(source_name, 0) + 1
            time_axis_count_per_source[source_name] = time_axis_index
            time_axis_description = (
                f"{len(timestamps)} samples"
                f", t=[{float(timestamps[0]):g}, {float(timestamps[-1]):g}] s"
                f", fs={fs:g} Hz"
            )

            comment = (
                f"Data source: {source_name} | "
                f"time axis {time_axis_index}: {time_axis_description}"
            )

            source = Source(
                name=source_name,
                path=source_name,
                comment=comment,
                source_type=1,
                bus_type=1,
            )

            signals_to_write = []
            for signal in group["signals"]:
                # guard: append() is called with common_timebase=True
                if not np.array_equal(signal.timestamps, timestamps):
                    error_text = (
                        f"Signal '{signal.label}' does not match the time axis of its "
                        f"signal group (source '{source_name}'). asammdf requires a "
                        "uniform time axis within one signal group."
                    )
                    logger.error(error_text)
                    raise ValueError(error_text)

                if signal.ndim == 1:
                    samples = signal.value
                else:
                    dtype_str = self.DTYPE_MAP[signal.dtype]
                    types = [(signal.label, f"{signal.shape[1:]}{dtype_str}")]
                    samples = np.rec.fromarrays([signal.value], dtype=np.dtype(types))

                signals_to_write.append(
                    Signal(
                        samples=samples,
                        timestamps=timestamps,
                        name=signal.label,
                        unit=signal.unit if signal.unit else "",
                        comment=signal.description if signal.description else "",
                        source=source,
                        encoding="utf-8",
                    )
                )

            self.append(signals_to_write, comment=comment, common_timebase=True)

        for label in dict.fromkeys(signal.label for signal in data):
            if label not in self._available_signals:
                self._available_signals.append(label)
