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

from abc import ABC, abstractmethod
from typing import Any, Literal

import numpy as np

from ares.utils.signal import signal


class AresDataInterface(ABC):
    def __init__(
        self, name: str, file_path: str, mode: Literal["write", "read"], **kwargs: Any
    ):
        """AresDataInterface abstract class to provide template for all filetypes (mf4, mat, parquet).
            The idea is that all ares interfaces inherit this class so that easy data-handling inside ARES is possible.
            MUST have functions for data interfaces are:
                - get
                - write
                - save_file

        Args:
            fpath (str): The path to the data source file (.mf4, .parquet, or .mat).
        """
        super().__init__(**kwargs)

    @property
    def name(self) -> str | None:
        """name of data element"""
        return self._name

    @property
    def file_path(self) -> str | None:
        """File path to element to read/write. File can NOT exist."""
        return self._file_path

    @property
    def available_channels(self) -> list[str] | None:
        """All channels available in this data-element."""
        return self._available_channels

    @property
    def mode(self) -> Literal["write", "read"]:
        """Mode of the data-element. Possible ['write', 'read']"""
        return self._mode

    @abstractmethod
    def save_file(self, *args: Any, **kwargs: Any) -> str | None:
        """AresDataInterface abstract function for saving the current data to disk."""
        pass

    @abstractmethod
    def get(
        self, channels: list[str] | None = None, **kwargs: Any
    ) -> list[signal] | None:
        """AresDataInterface abstract function for getting signals from mf4. Returns list with asammdf signals"""
        pass

    @abstractmethod
    def write(self, data: list[signal]) -> None:
        pass

    # TODO: rename function after final implementation -> resample is currently also in asammdf package parent implemented so careful name chosing is necessary
    def _resample(self, data: list[signal], stepsize_ms: int) -> list[signal]:
        """AresDataInterface, standard resample function
        - linear interpolation
        """
        latest_start_time = float(0.0)
        earliest_end_time = np.inf

        # get timevector
        for sig in data:
            if len(sig.timestamps) > 0:
                latest_start_time = max(latest_start_time, sig.timestamps[0])
                earliest_end_time = min(earliest_end_time, sig.timestamps[-1])

        timestamps_resample = np.arange(
            0,
            (earliest_end_time - latest_start_time) + (stepsize_ms / 1000.0),
            stepsize_ms / 1000.0,
        )

        # resampling of each element
        [sig.resample(timestamps_resample) for sig in data]
        return data

    # TODO: destructor won't work in python -> garbage collector is challenge!
    # alternative would "context manager" using the with ... statement + __enter__, __exit__
    def __del__(self):
        """AresDataInterface, destructor for handling saving of data fils"""
        if self._mode == "write":
            _ = self.save_file()
