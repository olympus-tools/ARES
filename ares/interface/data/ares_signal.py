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

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from ares.utils.decorators import safely_run
from ares.utils.decorators import typechecked_dev as typechecked
from ares.utils.logger import create_logger

logger = create_logger(__name__)


@dataclass
@typechecked
class AresSignal:
    """A class to handle time-series signals in ARES.

    This class provides a unified interface for handling time-series signals
    with timestamps and corresponding data values. It automatically validates
    data types and dimensions after initialization.

    Attributes:
        label (str): Name or identifier of the signal (required).
        timestamps (npt.NDArray[np.float32]): Time values as numpy array with floating point dtype (required).
        value (npt.NDArray): Signal data values as numpy array - can be any dtype (required).
        description (str | None): Optional textual description of the signal.
        unit (str | None): Optional physical unit of the signal (e.g., 'km/h', '°C', 'm/s').
    """

    label: str
    value: npt.NDArray
    timestamps: npt.NDArray[np.float32]
    description: str | None = None
    unit: str | None = None

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
            np.dtype: The data type of the underlying numpy array (e.g., float32, int32).
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

    @safely_run(
        default_return=None,
        exception_msg="The signal could not be resampled.",
        log=logger,
        instance_el=["label"],
    )
    @typechecked
    def resample(self, timestamps_resampled: npt.NDArray[np.float32]) -> None:
        """Resample the signal to new timestamps using linear interpolation.

        Handles scalar signals (1D), 1D array signals (2D), and 2D array signals (3D).
        Interpolation is performed independently for each array element.

        Args:
            timestamps_resampled (npt.NDArray[np.float32]): New timestamp values
                for resampling. Must be a 1D numpy array with floating point dtype.

        Returns:
            None: Modifies the signal in-place, updating timestamps and value.
        """
        if self.ndim == 1:
            self.value = np.interp(
                timestamps_resampled, self.timestamps, self.value.astype(np.float32)
            ).astype(self.dtype)

        elif self.ndim == 2:
            array_size = self.shape[1]
            resampled = np.zeros(
                (len(timestamps_resampled), array_size), dtype=np.float32
            )
            for i in range(array_size):
                resampled[:, i] = np.interp(
                    timestamps_resampled, self.timestamps, self.value[:, i]
                )
            self.value = resampled.astype(self.dtype)

        elif self.ndim == 3:
            rows, cols = self.shape[1], self.shape[2]
            resampled = np.zeros(
                (len(timestamps_resampled), rows, cols), dtype=np.float32
            )
            for i in range(rows):
                for j in range(cols):
                    resampled[:, i, j] = np.interp(
                        timestamps_resampled, self.timestamps, self.value[:, i, j]
                    )
            self.value = resampled.astype(self.dtype)

        else:
            logger.warning(
                f"Unsupported signal dimension: {self.ndim}. Supported: 1 (scalar), 2 (1D array/timestep), 3 (2D array/timestep)"
            )

        self.timestamps = timestamps_resampled

    @safely_run(
        default_return=None,
        exception_msg="Typecast for this signal could not be executed.",
        log=logger,
        instance_el=["label"],
    )
    @typechecked
    def dtype_cast(self, dtype: np.dtype | type[np.generic]) -> None:
        """Cast the signal value to a specified numpy dtype.

        Converts the value array to the target dtype only if the current dtype
        differs from the target dtype. Does nothing if dtypes already match.

        Args:
            dtype (np.dtype | type[np.generic]): Target numpy data type
                (e.g., np.float32, np.int64, np.dtype('float64')).

        Returns:
            None: Modifies the signal value in-place.
        """
        target_dtype = np.dtype(dtype)

        if self.dtype != target_dtype:
            curr_datatype = self.dtype
            self.value = self.value.astype(target_dtype)
            logger.debug(
                f"Signal '{self.label}' cast from {curr_datatype} to {target_dtype}"
            )
