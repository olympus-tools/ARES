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

from dataclasses import dataclass, field

import numpy as np


@dataclass()
class signal:
    """A python dataclass to store signals in ARES."""

    label: str
    timestamps: np.ndarray = field(default_factory=lambda: np.array([], dtype=float))
    data: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.object_))

    def __post_init__(self):
        """
        Validate the data types after initialization.
        """
        if not np.issubdtype(self.timestamps.dtype, np.floating):
            raise TypeError("The 'timestamps' array must have a float datatype.")
        if self.timestamps.ndim != 1 or (
            self.data.ndim >= 1 and self.timestamps.shape[0] != self.data.shape[0]
        ):
            raise ValueError(
                "Both 'timestamps' and 'data' arrays must be at least 1-dimensional."
            )

    def resample(self, timestamps_resampled: np.ndarray):
        """Resample function for ares signals
        Algortihms available:
            - linear interpolation (default)
        """
        self.data = np.interp(timestamps_resampled, self.timestamps, self.data).astype(
            self.data.dtype
        )
        self.timestamps = timestamps_resampled
