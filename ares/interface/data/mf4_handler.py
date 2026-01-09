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

Copyright 2025 Andrä Carotta

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

For details, see: https://github.com/olympus-tools/ARES#7-license
"""

import datetime
import os
from typing import override

from asammdf import MDF, Signal, Source

from ares.interface.data.ares_data_interface import AresDataInterface
from ares.interface.data.ares_signal import AresSignal
from ares.utils.decorators import safely_run
from ares.utils.decorators import typechecked_dev as typechecked
from ares.utils.logger import create_logger

logger = create_logger(__name__)

# define obsolete channels that are ALWAYS skipped
OBSOLETE_SIGNALS = ["time"]


class MF4Handler(MDF, AresDataInterface):
    """A extension of the asammdf.MDF class to allow ARES to interact with mf4's.
    see: https://asammdf.readthedocs.io/en/latest/api.html#asammdf.mdf.MDF
    """

    @typechecked
    def __init__(
        self,
        file_path: str | None,
        **kwargs,
    ):
        """Initialize MF4Handler and load available channels.

        Checks if asammdf MDF is already initialized to avoid duplicate initialization.
        In read mode, loads the MF4 file.
        In write mode, creates an empty MDF instance plus adds signals if any are given.

        Args:
            file_path (str | None): Path to the MF4 file to load or write.
            **kwargs (Any): Additional arguments passed to asammdf's MDF constructor.
        """

        AresDataInterface.__init__(self, file_path=file_path, **kwargs)

        signals = kwargs.pop("signals", [])
        if file_path is None or file_path == "":
            super().__init__(**kwargs)
            self._available_signals: list[str] = []

            if signals is None:
                return
            else:
                self.add(signals=signals, **kwargs)
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
        default_return=[],
        message="Error during writing mf4-file. Validate output_path also consider write rights.",
        log=logger,
    )
    def _save(self, output_path: str, **kwargs) -> None:
        """Save MF4 file with timestamp in header comment.

        Wrapper for asammdf's MDF.save() that adds a timestamp to the file header.

        Args:
            output_path (str): Absolute path where the MF4 file should be written.
            **kwargs (Any): Additional arguments passed to MDF.save().
        """

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.header.comment = f"File last saved on: {timestamp}"
        result_path = self.save(output_path, **kwargs)
        logger.debug(f"Data was successfully written to: {result_path}")

    @override
    def get(self, label_filter: list[str] | None = None, **kwargs) -> list[AresSignal]:
        """Get signals from MF4 file with optional resampling.

        Args:
            label_filter (list[str] | None): List of signal names to read from MF4 file.
                If None, all available signals are read. Defaults to None.
            **kwargs (Any): Additional arguments. 'stepsize' (int) triggers resampling.

        Returns:
            list[AresSignal]: List of AresSignal objects, optionally resampled to common time vector.
        """
        stepsize = kwargs.pop("stepsize", None)
        tmp_data = (
            self._get_signals(self._available_signals)
            if label_filter is None
            else self._get_signals(label_filter, **kwargs)
        )

        if stepsize is None:
            return tmp_data
        else:
            return self._resample(tmp_data, stepsize=stepsize)

    @typechecked
    def _get_signals(self, label_filter: list[str], **kwargs) -> list[AresSignal]:
        """Helper function for get() that handles multiple occurrences of signals in MF4 files.

        Uses asammdf's whereis() function to locate signals and selects the signal
        with the most samples when multiple occurrences exist. Missing signals are
        skipped with a warning instead of causing errors.

        Args:
            label_filter (list[str]): List of signal names to retrieve from the MF4 file.
            **kwargs (Any): Additional arguments passed to asammdf's select() method.

        Returns:
            list[AresSignal]: List of AresSignal objects extracted from the MF4 file.
                Only contains signals that were actually found.
        """

        occurences = [self.whereis(c) for c in label_filter]
        not_found = [i for i, x in enumerate(occurences) if len(x) == 0]
        if len(not_found) > 0:
            missing_channels = ", ".join([label_filter[i] for i in not_found])
            logger.warning(
                f"Selection of the following channels not possible. Existence is not given: {missing_channels}"
            )

        single_occ = [i for i, x in enumerate(occurences) if len(x) == 1]
        multi_occ = [i for i, x in enumerate(occurences) if len(x) > 1]

        # Collect only found signals (no static list with None values)
        found_signals: list[Signal] = []

        if len(single_occ) > 0:
            selected_signals = super().select(
                [label_filter[idx] for idx in single_occ], **kwargs
            )
            found_signals.extend(selected_signals)

        for i in multi_occ:
            sel_signal = [(None, gp_idx, cn_idx) for gp_idx, cn_idx in occurences[i]]
            all_signals = super().select(sel_signal, **kwargs)
            len_samples = [len(s.samples) for s in all_signals]
            idx = len_samples.index(max(len_samples))
            found_signals.append(all_signals[idx])

        return [
            AresSignal(
                label=signal.name, timestamps=signal.timestamps, value=signal.samples
            )
            for signal in found_signals
        ]

    @override
    def add(self, signals: list[AresSignal], **kwargs) -> None:
        """Add AresSignal objects to MF4 file.

        Converts AresSignal objects to asammdf Signal format and appends them to the MF4 file.
        Optionally adds source information to signals for traceability.

        Args:
            signals (list[AresSignal]): List of AresSignal objects to append to MF4 file.
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

        signals_to_write = [
            Signal(
                samples=sig.value,
                timestamps=sig.timestamps,
                name=sig.label,
                source=source,
            )
            for sig in signals
        ]
        self.append(signals_to_write)
        [self._available_signals.append(sig.label) for sig in signals]
