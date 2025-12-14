"""
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

from dataclasses import dataclass
from typing import Optional

import numpy as np
import numpy.typing as npt


@dataclass
class AresSignal:
    """A class to handle time-series signals in ARES.

    This class provides a unified interface for handling time-series signals
    with timestamps and corresponding data values. It automatically validates
    data types and dimensions after initialization.

    Attributes:
        label: Name or identifier of the signal (required).
        timestamps: Time values as numpy array with floating point dtype (required).
        value: Signal data values as numpy array - can be any dtype (required).
        description: Optional textual description of the signal.
        unit: Optional physical unit of the signal (e.g., 'km/h', '°C', 'm/s').
    """

    label: str
    value: npt.NDArray
    timestamps: npt.NDArray[np.floating]
    description: Optional[str] = None
    unit: Optional[str] = None

    def __post_init__(self):
        """
        Validate the data types after initialization.
        """

        if not np.issubdtype(self.timestamps.dtype, np.floating):
            raise TypeError("The 'timestamps' array must have a float datatype.")
        if self.timestamps.ndim != 1 or (
            self.value.ndim >= 0 and self.timestamps.shape[0] != self.value.shape[0]
        ):
            raise ValueError(
                "Both 'timestamps' and 'data' arrays must be at least 1-dimensional."
            )

    @property
    def dtype(self) -> np.dtype:
        """Returns the numpy dtype of the signal value.

        Returns:
            np.dtype: The data type of the underlying numpy array (e.g., float64, int32).
        """
        return self.value.dtype

    @property
    def shape(self) -> tuple:
        """Returns the shape of the signal value.

        Returns:
            tuple: The shape of the underlying numpy array.
                   () for scalar, (n,) for 1D array, (m, n) for 2D array.
        """
        return self.value.shape

    @property
    def ndim(self) -> int:
        """Returns the number of dimensions of the signal value.

        Returns:
            int: The number of dimensions of the underlying numpy array.
                 0 for scalar, 1 for 1D array, 2 for 2D array.
        """
        return self.value.ndim

    def resample(self, timestamps_resampled: npt.NDArray[np.floating]) -> None:
        """Resample the signal to new timestamps using linear interpolation.

        Args:
            timestamps_resampled (npt.NDArray[np.floating]): New timestamp values
                for resampling. Must be a 1D numpy array with floating point dtype.

        Returns:
            None: Modifies the signal in-place, updating timestamps and value.
        """
        self.value = np.interp(
            timestamps_resampled, self.timestamps, self.value.astype(np.floating)
        ).astype(self.dtype)
        self.timestamps = timestamps_resampled
