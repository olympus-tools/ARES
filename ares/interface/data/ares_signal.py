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
from numba import njit
from scipy.interpolate import CubicSpline

from ares.utils.decorators import error_msg, safely_run
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

    @property
    def fs(self) -> np.float32:
        """Returns the average sampling rate over the full timestamp range.

        Returns:
            np.float32: The average sampling rate of the signal over the full timestamp range.
        """

        return np.float32(
            (self.shape[0] - 1) / (self.timestamps[-1] - self.timestamps[0])
        )

    @staticmethod
    @njit
    def _resample_nearest(
        values_1d: npt.NDArray[np.integer | np.bool],
        timestamps_source: npt.NDArray[np.float32],
        timestamps_resampled: npt.NDArray[np.float32],
    ) -> npt.NDArray[np.integer | np.bool]:
        """Resample a one-dimensional signal vector using the neirest neighbour method.

        Args:
            values_1d (npt.NDArray[npt.integer or np.bool]): One-dimensional source values.
            timestamps_source (npt.NDArray[np.float32]): Source timestamps.
            timestamps_resampled (npt.NDArray[np.float32]): Target timestamps.

        Returns:
            npt.NDArray: Resampled values with the original signal dtype.
        """
        time_idx = np.searchsorted(timestamps_source, timestamps_resampled)
        time_idx = np.clip(time_idx, 1, len(timestamps_source) - 1)

        left_distance = timestamps_resampled - timestamps_source[time_idx - 1]
        right_distance = timestamps_source[time_idx] - timestamps_resampled

        nearest_idx = np.where(left_distance < right_distance, time_idx - 1, time_idx)
        nearest_idx[timestamps_resampled < timestamps_source[0]] = 0

        return values_1d[nearest_idx]

    @typechecked
    @staticmethod
    def _resample_linear(
        values_1d: npt.NDArray[np.float32],
        timestamps_source: npt.NDArray[np.float32],
        timestamps_resampled: npt.NDArray[np.float32],
    ) -> npt.NDArray[np.float32]:
        """Resample a one-dimensional signal vector using linear interpolation.

        Args:
            values_1d (npt.NDArray[np.float32]): One-dimensional source values.
            timestamps_source (npt.NDArray[np.float32]): Source timestamps.
            timestamps_resampled (npt.NDArray[np.float32]): Target timestamps.

        Returns:
            npt.NDArray[np.float32]: Resampled values with the original signal dtype.
        """
        signal_resampled = np.interp(
            timestamps_resampled, timestamps_source, values_1d.astype(np.float32)
        )

        return signal_resampled.astype(values_1d.dtype)

    @typechecked
    @staticmethod
    def _resample_cubic(
        values_1d: npt.NDArray,
        timestamps_source: npt.NDArray[np.float32],
        timestamps_resampled: npt.NDArray[np.float32],
    ) -> npt.NDArray[np.float32]:
        """Resample a one-dimensional signal vector using cubic spline interpolation.

        Args:
            values_1d (npt.NDArray[np.float32]): One-dimensional source values.
            timestamps_source (npt.NDArray[np.float32]): Source timestamps.
            timestamps_resampled (npt.NDArray[np.float32]): Target timestamps.

        Returns:
            npt.NDArray[np.float32]: Resampled values with the original signal dtype.
        """
        cs = CubicSpline(timestamps_source, values_1d.astype(np.float32))
        return cs(timestamps_resampled).astype(values_1d.dtype)

    @staticmethod
    @njit
    def _resample_windowedsinc(
        values_1d: npt.NDArray[np.float32],
        timestamps_source: npt.NDArray[np.float32],
        timestamps_resampled: npt.NDArray[np.float32],
        fs: np.float32,
        radius: int = 10,
    ) -> npt.NDArray[np.float32]:
        """Resample using windowed-sinc interpolation (sinc * Blackman-Nuttall).

        Uses bandlimited interpolation with a truncated sinc kernel windowed by
        a Blackman window.

        Reference: https://ccrma.stanford.edu/~jos/resample/What_Bandlimited_Interpolation.html
                   https://www.analog.com/media/en/technical-documentation/dsp-book/dsp_book_Ch16.pdf

        Args:
            values_1d (npt.NDArray[np.float32]): One-dimensional source values.
            timestamps_source (npt.NDArray[np.float32]): Source timestamps.
            fs ( np.float32 ): Sample rate of the source signal.
            timestamps_resampled (npt.NDArray[np.float32]): Target timestamps.
            radius ( int ): Radius of window used in sinc-resampling. Default: 4.

        Returns:
            npt.NDArray[np.float32]: Resampled values with the original signal dtype.
        """
        signal_resampled = np.empty(len(timestamps_resampled), dtype=np.float32)

        for j in range(len(timestamps_resampled)):
            t_current = timestamps_resampled[j]

            original_time_samples = t_current * fs
            original_time_idx = np.int32(np.floor(original_time_samples))
            alpha = np.float32(original_time_samples - original_time_idx)

            signal_resampled_val = np.float32(0.0)
            total_weight = np.float32(0.0)

            for k in range(-radius + 1, radius + 1):
                window_idx = original_time_idx + k

                if 0 <= window_idx < len(values_1d):
                    sample_distance = np.float32(k) - alpha

                    sinc_val = np.sinc(sample_distance)

                    # Hamming Window
                    window_val = np.float32(0.54) + np.float32(0.46) * np.cos(
                        np.pi * (sample_distance / radius)
                    )

                    weight = sinc_val * window_val

                    signal_resampled_val += values_1d[window_idx] * weight
                    total_weight += weight

                if total_weight > 0.0:
                    signal_resampled[j] = signal_resampled_val / total_weight
                else:
                    signal_resampled[j] = np.float32(0.0)

        return signal_resampled

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
        method: str | None = "linear",
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
                ``"linear"`` (default), ``"windowedsinc"`` and ``"cubic"``.

        Returns:
            AresSignal: A new signal instance with resampled timestamps and values.

        """
        is_numeric_dtype = np.issubdtype(self.dtype, np.number) and not np.issubdtype(
            self.dtype, np.complexfloating
        )
        is_integer_dtype = np.issubdtype(self.dtype, np.integer)
        is_boolean_dtype = np.issubdtype(self.dtype, np.bool_)

        method = "linear" if method is None else method

        if not (is_numeric_dtype or is_boolean_dtype):
            logger.warning(
                f"Signal '{self.label}' cannot be resampled because dtype '{self.dtype}' is neither numeric nor boolean."
            )
            return None

        if self.value.ndim == 1:
            signal_dim_flat = self.value
            n_channels = 1
        else:
            signal_dim_flat = self.value.reshape(self.shape[0], -1)
            n_channels = signal_dim_flat.shape[1]

        resampled_channels = []
        for ch in range(n_channels):
            values_ch = signal_dim_flat if n_channels == 1 else signal_dim_flat[:, ch]

            if is_boolean_dtype or is_integer_dtype:
                resampled_ch = AresSignal._resample_nearest(
                    values_ch, self.timestamps, timestamps_resampled
                )
                method = "nearest"
            elif method == "linear":
                resampled_ch = AresSignal._resample_linear(
                    values_ch, self.timestamps, timestamps_resampled
                )
            elif method == "cubic":
                resampled_ch = AresSignal._resample_cubic(
                    values_ch, self.timestamps, timestamps_resampled
                )
            elif method == "windowedsinc":
                resampled_ch = AresSignal._resample_windowedsinc(
                    values_ch,
                    self.timestamps,
                    timestamps_resampled,
                    self.fs,
                )
            else:
                logger.warning(
                    f'Unsupported resample method: \'{method}\'. Supported: "linear", "cubic", "windowedsinc"'
                )
                return None
            resampled_channels.append(resampled_ch)

        if n_channels == 1:
            resampled_value = resampled_channels[0]
        else:
            resampled_value = np.column_stack(resampled_channels)

        if self.value.ndim > 1:
            resampled_value = resampled_value.reshape(
                (len(timestamps_resampled),) + self.shape[1:]
            )

        logger.debug(
            f"Signal '{self.label}' resampled from {self.timestamps[0]} to {self.timestamps[-1]} seconds with {len(timestamps_resampled)} samples using method '{method}'."
        )

        return AresSignal(
            label=self.label,
            timestamps=timestamps_resampled,
            value=resampled_value,
            description=self.description,
            source=self.source,
            unit=self.unit,
        )

    @error_msg(
        exception_msg="Error in ares-data-interface cut function.",
        log=logger,
        include_args=["start", "end", "mode"],
    )
    @typechecked
    def cut(
        self,
        start: np.float32 | int,
        end: np.float32 | int,
        mode: str = "time",
    ) -> "AresSignal":
        """Cut signal by time or index range.

        Enables flexible signal trimming: either by absolute time values
        (seconds) or by sample indices. The original signal instance is not
        modified — a new ``AresSignal`` is returned.

        Args:
            start (np.float32 | int): Start time in seconds (if mode='time')
                or start sample index (if mode='index').
            end (np.float32 | int): End time in seconds (if mode='time')
                or end sample index (if mode='index').
            mode (str): Cutting mode - either 'time' (default) for time-based
                or 'index' for index-based cutting.

        Returns:
            AresSignal: A new signal with the trimmed timestamps and values.
        """
        if mode == "time":
            i = np.searchsorted(self.timestamps, start, side="left")
            j = np.searchsorted(self.timestamps, end, side="right") - 1
        elif mode == "index":
            i, j = int(start), int(end)
        else:
            logger.error(f"Invalid cut mode: '{mode}'. Supported: 'time', 'index'.")
            raise

        if i > 0 or j < self.shape[0] - 1:
            logger.debug(
                f"Cutting signal '{self.label}' ({mode}-based): "
                f"indices [{i}:{j + 1}], "
                f"time range [{self.timestamps[i]:.3f}, {self.timestamps[j]:.3f}] seconds, "
                f"samples: {j - i + 1}."
            )

        return AresSignal(
            label=self.label,
            value=self.value[i : j + 1],
            timestamps=self.timestamps[i : j + 1],
            description=self.description,
            source=self.source,
            unit=self.unit,
        )

    @error_msg(
        exception_msg="Error in ares-data-interface padding function.",
        log=logger,
        include_args=["samples_to_add", "pad_value"],
    )
    @typechecked
    def padding(
        self,
        samples_to_add: int,
        pad_value: npt.NDArray | np.generic | int | float | bool = 0,
    ) -> "AresSignal":
        """Pad signal values by a given number of samples.

        The timestamp vector is extended using the signal sample rate
        (``self.fs``). If ``samples_to_add`` is not positive, the signal is
        returned unchanged.

        Args:
            samples_to_add (int): Number of samples to append.
            pad_value (npt.NDArray | np.generic | int | float | bool): Padding
                sample value used for appended samples.

        Returns:
            AresSignal: A new signal with padded values and extended timestamps.
        """

        if samples_to_add <= 0:
            return self
        else:
            logger.info(
                f"Padding applied to signal '{self.label}' with {samples_to_add} "
                f"sample(s) to match target length {len(self.timestamps) + samples_to_add}."
            )

        pad_sample = np.broadcast_to(pad_value, self.shape[1:])
        pad_block = np.repeat(pad_sample[np.newaxis, ...], samples_to_add, axis=0)
        value_aligned = np.concatenate([self.value, pad_block], axis=0)

        sample_period = np.float32(1.0 / self.fs)

        timestamps_padding = self.timestamps[-1] + sample_period * np.arange(
            1, samples_to_add + 1, dtype=np.float32
        )
        timestamps_aligned = np.concatenate(
            [self.timestamps, timestamps_padding]
        ).astype(np.float32)

        return AresSignal(
            label=self.label,
            value=value_aligned,
            timestamps=timestamps_aligned,
            description=self.description,
            source=self.source,
            unit=self.unit,
        )

    @staticmethod
    @typechecked
    def _validate_resample_accuracy(
        signal_original: "AresSignal",
        signal_resampled: "AresSignal",
        method: str | None = "linear",
    ) -> None:
        """Validate resampling accuracy via round-trip resampling.

        Resamples the already-resampled signal back onto the original timestamps
        and logs the mean percentage deviation and maximum absolute deviation
        between the original values and the round-trip result.

        This method is intended to be called only when DEBUG logging is active,
        as it performs an additional resampling step solely for validation.

        Args:
            signal_original (AresSignal): The original signal before resampling.
            signal_resampled (AresSignal): The signal after one resampling step.
            method (str): Resampling method used for the round-trip. Defaults to "linear".
        """

        signal_roundtrip = signal_resampled.resample(
            timestamps_resampled=signal_original.timestamps,
            method=method,
        )
        if signal_roundtrip is None:
            logger.debug(
                f"Resample accuracy validation for '{signal_original.label}': "
                f"round-trip resampling failed."
            )
            return

        orig = signal_original.value.astype(np.float32).ravel()
        rt = signal_roundtrip.value.astype(np.float32).ravel()

        abs_diff = np.abs(orig - rt)

        # avoid division by zero: fall back to absolute deviation where original is 0
        with np.errstate(divide="ignore", invalid="ignore"):
            pct_diff = np.where(
                orig != 0.0,
                (abs_diff / np.abs(orig)) * 100.0,
                abs_diff,
            )

        mean_pct_deviation = float(np.nanmean(pct_diff))
        max_abs_deviation = float(np.max(abs_diff))
        max_abs_flat_index = int(np.argmax(abs_diff))

        if len(signal_original.timestamps) > 0:
            elements_per_sample = max(
                1, int(orig.size / len(signal_original.timestamps))
            )
            max_abs_time_index = min(
                max_abs_flat_index // elements_per_sample,
                len(signal_original.timestamps) - 1,
            )
            max_abs_deviation_timestamp = float(
                signal_original.timestamps[max_abs_time_index]
            )
        else:
            max_abs_deviation_timestamp = float("nan")

        logger.debug(
            "Resample accuracy validation | "
            f"label = {signal_original.label:<50} | "
            f"dtype = {str(signal_original.dtype):<10} | "
            f"mean_pct_deviation = {mean_pct_deviation:>10.4f} % | "
            f"max_abs_deviation = {max_abs_deviation:>12.6f} | "
            f"max_abs_timestamp = {max_abs_deviation_timestamp:>12.6f} s"
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
