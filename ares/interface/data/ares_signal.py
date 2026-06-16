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

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt
from scipy.interpolate import CubicSpline

from ares.utils.decorators import safely_run
from ares.utils.decorators import typechecked_dev as typechecked
from ares.utils.logger import create_logger

logger = create_logger(name=__name__)


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
        source (str | None): Optional source or origin of the signal data.
        unit (str | None): Optional physical unit of the signal (e.g., 'km/h', '°C', 'm/s').
    """

    label: str
    value: npt.NDArray
    timestamps: npt.NDArray[np.float32]
    description: str | None = None
    source: str | None = None
    unit: str | None = None

    def __post_init__(self):
        """Validate, cast, and regularize timestamps after initialization.

        Casts ``timestamps`` to ``np.float32`` if needed, then makes the
        timestamps equidistant using ``np.linspace()`` while preserving length,
        minimum, and maximum values. Finally validates that ``timestamps`` has
        a floating-point dtype, is one-dimensional, and that its length matches
        the first dimension of ``value``.
        """

        if self.timestamps.shape[0] > 1:
            self.timestamps = np.linspace(
                self.timestamps[0],
                self.timestamps[-1],
                len(self.timestamps),
                dtype=np.float32,
            )
        else:
            self.timestamps = self._cast(
                self.timestamps, np.float32, input_type="timestamps"
            )

        if not np.issubdtype(self.timestamps.dtype, np.floating):
            raise TypeError("The 'timestamps' array must have a float datatype.")
        if self.timestamps.ndim != 1 or (
            self.value.ndim >= 0 and self.timestamps.shape[0] != self.value.shape[0]
        ):
            raise ValueError(
                "Both 'timestamps' and 'data' arrays must be at least 1-dimensional."
            )

    @typechecked
    def _cast(
        self,
        input: npt.NDArray | np.generic | int | float | bool,
        target_dtype: np.dtype | type[np.generic],
        input_type: str = "array",
    ) -> npt.NDArray:
        """Cast a numpy array or scalar to a target dtype if needed.

        Accepts both numpy arrays and scalars (Python or numpy). Scalars are
        wrapped into a 0-dim numpy array via ``np.asarray()`` before casting.

        Args:
            input (npt.NDArray | np.generic | int | float | bool): Source array or scalar to cast.
            target_dtype (np.dtype | type[np.generic]): Target numpy data type.
            input_type (str): Name of the input for logging purposes (default: 'array').

        Returns:
            npt.NDArray: The array with the target dtype. If already matching, returns unchanged.
        """
        target_dtype_obj = np.dtype(target_dtype)
        output = np.asarray(input)
        if output.dtype != target_dtype_obj:
            curr_dtype = output.dtype
            output = output.astype(target_dtype_obj)
            logger.debug(
                f"Signal '{self.label}': {input_type} cast from {curr_dtype} to {target_dtype_obj}."
            )
        return output

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

    @typechecked
    def _resample_linear(
        self,
        values_1d: npt.NDArray,
        timestamps_resampled: npt.NDArray[np.float32],
    ) -> npt.NDArray:
        """Resample a one-dimensional signal vector using linear interpolation.

        Args:
            values_1d (npt.NDArray): One-dimensional source values.
            timestamps_resampled (npt.NDArray[np.float32]): Target timestamps.

        Returns:
            npt.NDArray: Resampled values with the original signal dtype.
        """
        values_float = values_1d.astype(np.float32)
        resampled = np.interp(timestamps_resampled, self.timestamps, values_float)
        if np.issubdtype(self.dtype, np.bool_):
            return (resampled >= 0.5).astype(self.dtype)
        return resampled.astype(self.dtype)

    @typechecked
    def _resample_cubic(
        self,
        values_1d: npt.NDArray,
        timestamps_resampled: npt.NDArray[np.float32],
    ) -> npt.NDArray:
        """Resample a one-dimensional signal vector using cubic spline interpolation.

        Args:
            values_1d (npt.NDArray): One-dimensional source values.
            timestamps_resampled (npt.NDArray[np.float32]): Target timestamps.

        Returns:
            npt.NDArray: Resampled values with the original signal dtype.
        """
        values_float = values_1d.astype(np.float32)
        if np.issubdtype(self.dtype, np.bool_):
            return self._resample_linear(values_1d, timestamps_resampled)

        cs = CubicSpline(self.timestamps, values_float)
        return cs(timestamps_resampled).astype(self.dtype)

    @safely_run(
        default_return=None,
        exception_msg="The signal could not be resampled.",
        log=logger,
        instance_el=["label"],
    )
    @typechecked
    def resample(
        self,
        timestamps_resampled: npt.NDArray[np.float32],
        method: str = "linear",
    ) -> "AresSignal | None":
        """Create a resampled copy of the signal with selectable interpolation method.

        Supports linear interpolation and cubic spline interpolation.
        Interpolation is performed independently for each array element.
        The original signal instance is not modified.

        ``timestamps_resampled`` is expected to be an absolute time vector fully contained
        within ``[self.timestamps[0], self.timestamps[-1]]``. No normalization is applied,
        so both the signal timestamps and the resample vector must share the same absolute
        time reference.

        Args:
            timestamps_resampled (npt.NDArray[np.float32]): New absolute timestamp values
                within the signal's time range, with floating point dtype.
            method (str): Resampling method. Supported values are
                ``"linear"`` (default) and ``"cubic"``.

        Returns:
            AresSignal: A new signal instance with resampled timestamps and values.

        """
        is_numeric_dtype = np.issubdtype(self.dtype, np.number)
        is_boolean_dtype = np.issubdtype(self.dtype, np.bool_)

        if method == "linear":
            resample_1d = self._resample_linear
        elif method == "cubic":
            resample_1d = self._resample_cubic
        else:
            logger.warning(
                f"Unsupported resample method: '{method}'. Supported: linear, cubic"
            )
            return None

        if not (is_numeric_dtype or is_boolean_dtype):
            logger.warning(
                f"Signal '{self.label}' cannot be resampled because dtype '{self.dtype}' is neither numeric nor boolean."
            )
            return None

        if self.ndim == 1:
            resampled_value = resample_1d(self.value, timestamps_resampled)

        elif self.ndim == 2:
            array_size = self.shape[1]
            resampled_value = np.zeros(
                (len(timestamps_resampled), array_size), dtype=self.dtype
            )
            for i in range(array_size):
                resampled_value[:, i] = resample_1d(
                    self.value[:, i], timestamps_resampled
                )

        elif self.ndim == 3:
            rows, cols = self.shape[1], self.shape[2]
            resampled_value = np.zeros(
                (len(timestamps_resampled), rows, cols), dtype=self.dtype
            )
            for i in range(rows):
                for j in range(cols):
                    resampled_value[:, i, j] = resample_1d(
                        self.value[:, i, j], timestamps_resampled
                    )

        else:
            logger.warning(
                f"Unsupported signal dimension: {self.ndim}. Supported: 1 (scalar), 2 (1D array/timestep), 3 (2D array/timestep)"
            )
            return None

        return AresSignal(
            label=self.label,
            timestamps=timestamps_resampled,
            value=resampled_value,
            description=self.description,
            source=self.source,
            unit=self.unit,
        )

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
        """
        self.value = self._cast(self.value, dtype, input_type="value")
