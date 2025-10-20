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

import numpy as np
from asammdf import MDF, Signal

from ares.utils.data.ares_interface import AresDataInterface
from ares.utils.logger import create_logger
from ares.utils.signal import signal

# initialize logger
logger = create_logger("mf4_interface")


class mf4_handler(MDF, AresDataInterface):
    """A extension of the asammdf.MDF class to allow ARES to interact with mf4's.
    see: https://asammdf.readthedocs.io/en/latest/api.html#asammdf.mdf.MDF
    """

    def __init__(self, name: str = "", **kwargs):
        """Initialize MDF and get all available channels.
        With 'name=None' an empty mf4-file is created that can be written with self.save()"""
        super().__init__(name, **kwargs)
        self._available_channels = list(self.channels_db.keys())

        # TODO: remove magic default values, make this more general, config file?
        if "time" in self._available_channels:
            self._available_channels.remove("time")

    def save_file(self, file_path, **kwargs):
        """Wrapper for MDF save() to print message and adding timestamp."""

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.header.comment = f"File last saved on: {timestamp}"
        result_path = self.save(file_path, **kwargs)
        logger.debug(f"Data was written to: {result_path}")

    def get(self, channels=None, **kwargs) -> list[signal]:
        """ares get signal function"""
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

    def get_signals(self, channels, **kwargs) -> list[signal]:
        # check signals for multiple occurences using "whereis"
        occurences = [self.whereis(c) for c in channels]
        not_found = np.array([i for i, x in enumerate(occurences) if len(x) == 0])
        if len(not_found) > 0:
            raise ValueError(
                f"Selection of the following channels not possible. Existence is not given: {','.join(channels[not_found])}"
            )

        single_occ = np.array([i for i, x in enumerate(occurences) if len(x) == 1])
        multi_occ = np.array([i for i, x in enumerate(occurences) if len(x) > 1])

        data = np.full(len(channels), None)
        if len(single_occ) > 0:
            data[single_occ] = super().select(
                [channels[idx] for idx in single_occ], **kwargs
            )
            for i in multi_occ:
                sel_signal = [
                    (None, gp_idx, cn_idx) for gp_idx, cn_idx in occurences[i]
                ]
                all_signals = super().select(sel_signal, **kwargs)
                len_samples = [len(s.samples) for s in all_signals]
                idx = len_samples.index(max(len_samples))
                data[i] = all_signals[idx]

            data = data.tolist()
        else:
            data = super().select(channels, **kwargs)

        return [
            signal(label=d.name, timestamps=d.timestamps, data=d.samples) for d in data
        ]

    def write(self, data: list[signal]) -> None:
        """Basic function to write ares signals to mf4."""
        self.append(
            signals=[
                Signal(samples=sig.data, timestamps=sig.timestamps, name=sig.label)
                for sig in data
            ],
        )
