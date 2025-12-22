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

# Copyright (c) 2025 Andrä Carotta
#
# Licensed under the MIT License. See the LICENSE file for details.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# You may obtain a copy of the License at
# https://github.com/AndraeCarotta/ares/blob/master/LICENSE

"""

import datetime
import os
from typing import Literal, override

import numpy as np
from asammdf import MDF, Signal

from ares.interface.data.ares_data_interface import AresDataInterface
from ares.interface.data.ares_signal import AresSignal
from ares.utils.logger import create_logger

logger = create_logger(__name__)

# define obsolete channels that are ALWAYS skipped
OBSOLETE_CHANNEL = ["time"]


class MF4Handler(MDF, AresDataInterface):
    """A extension of the asammdf.MDF class to allow ARES to interact with mf4's.
    see: https://asammdf.readthedocs.io/en/latest/api.html#asammdf.mdf.MDF
    """

    def __init__(
        self,
        file_path: str,
        mode: Literal["write", "read"] = "read",
        **kwargs,
    ):
        """Initialize MDF and get all available channels. Check if asammdf was already initialized.

        Args:
            file_path ( str ): Path to the signals file to load
            mode ( ["write", "read"]): mode to access file, defaults to: "read"

            **kwargs: Additional arguments passed to subclass
        """
        if len(self.__dict__) == 0 or (
            len(self.__dict__) > 0 and not hasattr(self, "_initialized")
        ):
            if mode == "read":
                if not os.path.isfile(file_path):
                    raise FileNotFoundError(
                        "The signal file requested to read doesn't exist. File requested: {file_path}"
                    )
                super().__init__(file_path, **kwargs)
            elif mode == "write":
                super().__init__("", **kwargs)

            self._mode = mode
            self._file_path: str = "" if file_path is None else file_path

            self._available_channels: list[str] = list(self.channels_db.keys())
            for obs_channel in OBSOLETE_CHANNEL:
                if obs_channel in self._available_channels:
                    self._available_channels.remove(obs_channel)

            self._initialized = True
        else:
            logger.info(
                "Clone detected! Using already existent mf4-handler! We are smart, doing things twice is not!"
            )

    @override
    # TODO: safely_run function candidate?
    def write(self, output_path: str, **kwargs) -> None:
        """Wrapper for MDF save() to print message and adding timestamp.

        Args:
            **kwargs: Additional format-specific arguments
        """

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.header.comment = f"File last saved on: {timestamp}"
        result_path = self.save(self._file_path, **kwargs)
        logger.debug(f"Data was successfully written to: {result_path}")

    @override
    def get(self, signal: list[str] | None = None, **kwargs) -> list[AresSignal]:
        """Ares get signal function

        Args:
            signals (list[str] | None): List of channels/signals to read from mf4-file. In case of None all signals are read. default = None.
            **kwargs: Additional arguments. Currently not in use.

        Returns:
            list[AresSignal]: List of resampled AresSignal objects with common time vector.
        """
        stepsize_ms = kwargs.pop("stepsize_ms", None)
        tmp_data = (
            self.get_signals(self._available_channels)
            if channels is None
            else self.get_signals(channels, **kwargs)
        )

        if stepsize_ms is None:
            return tmp_data
        else:
            return self._resample(tmp_data, stepsize_ms=stepsize_ms)

    def get_signals(self, channels: list[str], **kwargs) -> list[AresSignal]:
        """Helper function for 'get'. Function handles multiple occurences of signals in mf4's via 'whereis' function provided in asammdf."""

        # check signals for multiple occurences using "whereis"
        occurences = [self.whereis(c) for c in channels]
        not_found = np.array([i for i, x in enumerate(occurences) if len(x) == 0])
        if len(not_found) > 0:
            raise ValueError(
                f"Selection of the following channels not possible. Existence is not given: {','.join(channels[not_found])}"
            )
        single_occ = np.array([i for i, x in enumerate(occurences) if len(x) == 1])
        multi_occ = np.array([i for i, x in enumerate(occurences) if len(x) > 1])

        data: list[Signal | None] = [None] * len(channels)
        if len(single_occ) > 0:
            selected_signals = super().select(
                [channels[idx] for idx in single_occ], **kwargs
            )
            for i, idx in enumerate(single_occ):
                data[idx] = selected_signals[i]
        for i in multi_occ:
            sel_signal = [(None, gp_idx, cn_idx) for gp_idx, cn_idx in occurences[i]]
            all_signals = super().select(sel_signal, **kwargs)
            len_samples = [len(s.samples) for s in all_signals]
            idx = len_samples.index(max(len_samples))
            data[i] = all_signals[idx]

        return [
            AresSignal(label=d.name, timestamps=d.timestamps, value=d.samples)
            for d in data
        ]

    @override
    def add(self, signals: list[AresSignal], **kwargs) -> None:
        """Basic function to write ares signals to mf4 using 'append()'
        Args:
            signals (list[AresSignal]): List of AresSignal objects to to append to mf4-file.
            **kwargs: Additional arguments. Currently not in use.
        """
        signals_to_write = [
            Signal(samples=sig.value, timestamps=sig.timestamps, name=sig.label)
            for sig in signals
        ]
        self.append(signals_to_write)
