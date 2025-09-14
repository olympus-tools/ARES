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

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from asammdf import MDF, Signal, Source
from typeguard import typechecked

from ares.utils.logger import create_logger

# initialize logger
logger = create_logger("mf4_interface")


# TODO: make DataMF4Interface an asammdf object? -> asammdf.MDF OR create other class: mf4_loader or so that takes over the job
# TODO: another idea: create a "data-class" (general API data in ARES) -> this data class can inherit from mf4,mat, etc. classes that provide api for read,writing
#       this would make if,elif, etc. in data.py unnecessary
class DataMF4interface:
    @staticmethod
    @typechecked
    def load_mf4(
        file_path: str,
        source: List[str],
        step_size_init_ms: Optional[float] = None,
    ) -> Optional[Dict[str, Any]]:
        """Loads an .mf4 file, extracts signals, and preprocesses them.

        Preprocessing includes finding a common time basis, resampling, and storing the
        results in `data`.

        Args:
            file_path (str): The path to the .mf4 file.
            source (list[str]): The list of sources to load from the file. Use ['all']
                to load all available sources.
            step_size_init_ms (float, optional): The target resampling step size in
                milliseconds.

        Returns:
            dict or None: The updated data dictionary, or None if an error occurs.
        """
        try:
            data: Dict[str, Any] = {}

            with MDF(file_path) as datasource:
                data_raw: Dict[str, Tuple[np.ndarray, np.ndarray]] = {}
                for signal in datasource.iter_channels():
                    signal_source_name = (
                        signal.source.path if hasattr(signal.source, "path") else None
                    )
                    if not signal_source_name and hasattr(signal.source, "path"):
                        signal_source_name = signal.source.path

                    # Filter signals based on specified source
                    if "all" in source or (
                        signal_source_name and signal_source_name in source
                    ):
                        data_raw[signal.name] = (signal.timestamps, signal.samples)

                if not data_raw:
                    logger.warning(
                        f"No signals found matching the specified source {source} in {file_path}.",
                    )

                time_vector, data_resampled = DataMF4interface._preprocessing_mf4(
                    data_raw=data_raw,
                    step_size_init_ms=step_size_init_ms,
                )

                data["timestamp"] = time_vector
                data.update(data_resampled)

                logger.debug(
                    f"Source '{source}' from .mf4 file {file_path} loaded successfully."
                )
                return data

        except Exception as e:
            logger.error(f"Error loading .mf4 file {file_path}: {e}")
            return None

    @staticmethod
    @typechecked
    def _preprocessing_mf4(
        data_raw: Dict[str, Tuple[np.ndarray, np.ndarray]],
        step_size_init_ms: float,
    ) -> Tuple[Optional[np.ndarray], Dict[str, np.ndarray]]:
        """Resamples loaded signals from an MF4 file to a uniform time basis.

        This function finds the latest start time and earliest end time to create a global
        time vector. It then resamples all numeric signals to this time basis using linear
        interpolation. Non-numeric or invalid signals are handled by creating an array of `None`
        values.

        Args:
            data_raw (dict[str, tuple[np.ndarray, np.ndarray]]): A dictionary where keys
                are signal names and values are tuples containing `(timestamps, samples)`.
            step_size_init_ms (float): The target resampling step size in milliseconds.

        Returns:
            tuple[np.ndarray or None, dict[str, np.ndarray]]: A tuple containing:
                1. The global time vector (`np.ndarray`) for the resampled data, or `None`
                   if no valid data range is found.
                2. A dictionary where keys are signal names and values are the resampled
                   sample arrays (`np.ndarray`).
        """
        try:
            latest_start_time = 0.0
            earliest_end_time = np.inf

            # Find the latest start time and the earliest end time across all numeric signals
            for timestamps, _ in data_raw.values():
                if (
                    isinstance(timestamps, np.ndarray)
                    and np.issubdtype(timestamps.dtype, np.number)
                    and len(timestamps) > 0
                ):
                    latest_start_time = max(latest_start_time, timestamps[0])
                    earliest_end_time = min(earliest_end_time, timestamps[-1])

            target_rate_hz = 1000.0 / step_size_init_ms
            global_time_vector = np.arange(
                0,
                (earliest_end_time - latest_start_time) + (1 / target_rate_hz),
                1 / target_rate_hz,
            )

            data_resampled: Dict[str, np.ndarray] = {}
            for signal_name, (timestamps, samples) in data_raw.items():
                if (
                    isinstance(timestamps, np.ndarray)
                    and np.issubdtype(timestamps.dtype, np.number)
                    and isinstance(samples, np.ndarray)
                    and np.issubdtype(samples.dtype, np.number)
                    and len(timestamps) > 0
                ):
                    # Make timestamps relative to the latest start time
                    relative_timestamps = timestamps - latest_start_time
                    resampled_samples = np.interp(
                        global_time_vector, relative_timestamps, samples
                    )
                    data_resampled[signal_name] = resampled_samples
                else:
                    num_samples = (
                        len(global_time_vector) if global_time_vector is not None else 0
                    )
                    none_array = np.array([None] * num_samples, dtype=object)
                    data_resampled[signal_name] = none_array
                    logger.info(
                        f"Signal '{signal_name}' could not be read from measurement file.",
                    )

            logger.info("Data source file successfully resampled.")
            return global_time_vector, data_resampled

        except Exception as e:
            logger.error(f"Error during preprocessing mf4 data source file: {e}")
            return None, {}

    @staticmethod
    @typechecked
    def write_out_mf4(
        file_path: str,
        data: dict,
        meta_data: Dict[str, str],
    ):
        """Writes data from the specified sources in `data` to an .mf4 file.

        It iterates through the provided `data` keys, creates `asammdf.Signal` objects,
        and appends them to a new `asammdf.MDF` file.

        Args:
            file_path (str): The path to the output file.
            data (dict[str, Any]): The data dictionary containing sources to export.
            meta_data (dict): A dictionary containing metadata such as the ARES
                version and the current username.
        """
        try:
            all_signals_to_write = []

            with MDF() as output_file_mf4:
                for source_key, data_value in data.items():
                    timestamp: np.ndarray = data_value["timestamp"]

                    src = Source(
                        name=source_key,
                        path=source_key,
                        comment=f"Data from {source_key}",
                        source_type=1,
                        bus_type=1,
                    )

                    for signal_name, samples in data_value.items():
                        if signal_name == "timestamp":
                            continue

                        try:
                            # Convert to float64 for compatibility with asammdf
                            samples_float = samples.astype(np.float64)
                        except (ValueError, TypeError):
                            logger.warning(
                                f"Error: Signal '{signal_name}' in source '{source_key}' could not be converted to float64. Skipping.",
                            )
                            continue

                        signal = Signal(
                            samples=samples_float,
                            timestamps=timestamp,
                            name=signal_name,
                            source=src,
                            comment="",
                        )
                        all_signals_to_write.append(signal)

                if not all_signals_to_write:
                    logger.warning(
                        f"No valid signals found to write for source(s) to {file_path}.",
                    )
                else:
                    output_file_mf4.append(
                        all_signals_to_write, comment="ares simulation result"
                    )
                    output_file_mf4.save(file_path, overwrite=False)
                    logger.info(
                        f"Output .mf4 file written successfully to {file_path}.",
                    )

        except Exception as e:
            logger.error(
                f"Error saving .mf4 file to {file_path} with source(s): {e}",
            )
