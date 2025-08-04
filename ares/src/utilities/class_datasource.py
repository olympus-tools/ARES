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

import os
from datetime import datetime
from asammdf import MDF, Signal, Source
from .class_logfile import Logfile
import numpy as np


class DataSource:
    def __init__(
        self,
        file_path: str,
        source: list,
        step_size_init_ms: int,
        logfile: Logfile,
    ):
        """
        Initializes the DataSource class by reading a data source file.
        The constructor automatically loads and preprocesses the data based on the file extension.
        The processed data is stored in the `self.data` attribute.

        :param file_path: The path to the data source file (.mf4, .parquet, or .mat).
        :param source: Specifies which source(s) from the data file to include.
                    Use `['all']` to load all sources, or a list of specific source names (e.g., `['source1', 'source2']`).
        :param step_size_init_ms: The target resampling step size in milliseconds for the initial loading.
        :param logfile: The logfile object of the current ARES pipeline.
        :return: None. The constructor initializes the object's state and loads the data.
        """
        self.file_path = file_path
        self.logfile = logfile
        self.source = set(source)
        self.data = {}
        self.data["base"] = {}

        # get fileformat to trigger the correct loading pipeline
        file_format = os.path.splitext(self.file_path)[1].lower()
        if file_format == ".mf4":
            self._load_mf4(step_size_init_ms=step_size_init_ms)
        elif file_format == ".parquet":
            self.logfile.write(
                f"Evaluation of .parquet input/output is not implemented yet",
                level="ERROR",
            )  # TODO
        elif file_format == ".mat":
            self.logfile.write(
                f"Evaluation of .mat input/output is not implemented yet", level="ERROR"
            )  # TODO
        else:
            self.logfile.write(
                f"Unknown file format for {self.file_path}.", level="WARNING"
            )

    def _load_mf4(self, step_size_init_ms: float = None):
        """
        Loads an .mf4 file, extracts signals from specified sources, and preprocesses them.
        Preprocessing includes finding a common time basis, resampling, and storing the
        results in `self.data` under the key 'base'.

        :param step_size_init_ms: The target resampling step size in milliseconds.
        :return: None. The method populates the `self.data` attribute and logs the process.
                Errors are logged, but no value is returned.
        """
        try:
            with MDF(self.file_path) as datasource:
                data_raw = {}
                for signal in datasource.iter_channels():
                    signal_source_name = (
                        signal.source.path if hasattr(signal.source, "path") else None
                    )
                    if not signal_source_name and hasattr(signal.source, "path"):
                        signal_source_name = signal.source.path

                    # Filter signals based on specified source
                    if "all" in self.source or (
                        signal_source_name and signal_source_name in self.source
                    ):
                        data_raw[signal.name] = (signal.timestamps, signal.samples)

                if not data_raw:
                    self.logfile.write(
                        f"No signals found matching the specified source {self.source} in {self.file_path}.",
                        level="WARNING",
                    )

                time_vector, data_resampled = self._preprocessing_mf4(
                    data_raw=data_raw, step_size_init_ms=step_size_init_ms
                )
                self.data["base"]["timestamp"] = time_vector
                self.data["base"].update(data_resampled)

                self.logfile.write(
                    f"Source '{self.source}' from .mf4 file {self.file_path} loaded successfully (nested data under source 'base')."
                )

        except Exception as e:
            self.logfile.write(
                f"Error loading .mf4 file {self.file_path}: {e}", level="ERROR"
            )

    def write_out(self, file_path: str, source: list):
        """
        Writes data from a specified source within `self.data` to an output file.
        The output format is determined by the file extension provided in `file_path`.
        Currently, only .mf4 output is supported.

        :param file_path: The path to the output file (e.g., 'results.mf4').
        :param source: A list of keys from `self.data` to be written.
                    Use `['all']` to write all available sources.
        :return: None. The method performs a file-writing operation and logs the outcome.
        """
        try:
            file_format = os.path.splitext(file_path)[1].lower()

            if file_format == ".mf4":
                self._write_out_mf4(file_path, source)
            elif file_format == ".parquet":
                self.logfile.write(
                    f"Evaluation of .parquet input/output is not implemented yet",
                    level="ERROR",
                )  # TODO
            elif file_format == ".mat":
                self.logfile.write(
                    f"Evaluation of .mat input/output is not implemented yet",
                    level="ERROR",
                )  # TODO
            else:
                self.logfile.write(
                    f"Unsupported output file format: {file_format}.", level="WARNING"
                )

        except Exception as e:
            self.logfile.write(
                f"Error writing data to {file_path} from source '{source}': {e}",
                level="ERROR",
            )

    def _write_out_mf4(self, file_path: str, source: list = None):
        """
        Writes data from the specified sources in `self.data` to an .mf4 file.
        It iterates through the provided `source` keys, creates `asammdf.Signal` objects,
        and appends them to a new `asammdf.MDF` file.

        :param file_path: The path to the output .mf4 file.
        :param source: A list of keys from `self.data` to export. If `['all']`,
                    all available keys are used.
        :return: None. The method handles file creation and writing, and logs errors.
        """
        #TODO: only the values that have really been in the element workflow should be written out
        try:
            if "all" in source:
                source = list(self.data.keys())
                log_sources = "all available source"
            elif isinstance(source, list):
                source = source
                log_sources = str(source)

            file_path = self._eval_output_path(file_path)
            all_signals_to_write = []

            with MDF() as output_file_mf4:
                for source_key in source:
                    if source_key in self.data:
                        data_to_write = self.data[source_key]
                        timestamp = data_to_write["timestamp"]

                        src = Source(
                            name=source_key,
                            path=source_key,
                            comment=f"Data from {source_key}",
                            source_type=1,
                            bus_type=1,
                        )

                        for signal_name, samples in data_to_write.items():

                            try:
                                samples = samples.astype(np.float64)
                            except ValueError:
                                self.logfile.write(
                                    f"Error: Signal '{signal_name}' in source '{source_key}' could not be converted to float64. Skipping.",
                                    level="WARNING",
                                )
                                continue

                            signal = Signal(
                                samples=samples,
                                timestamps=timestamp,
                                name=signal_name,
                                source=src,
                                comment="",
                            )
                            all_signals_to_write.append(signal)

                    else:
                        self.logfile.write(
                            f"Skipping key '{source_key}' not found in simulation 'data_source' element.",
                            level="WARNING",
                        )

                if not all_signals_to_write:
                    self.logfile.write(
                        f"No valid signals found to write for source {log_sources} to {file_path}.",
                        level="WARNING",
                    )

                output_file_mf4.append(
                    all_signals_to_write, comment=f"ares simulation result"
                )
                output_file_mf4.save(file_path, overwrite=False)
                self.logfile.write(
                    f"Output .mf4 file written successfully to {file_path} with source {log_sources}."
                )

        except Exception as e:
            self.logfile.write(
                f"Error saving .mf4 file to {file_path} with source {log_sources}: {e}",
                level="ERROR",
            )

    def _preprocessing_mf4(
        self, data_raw: dict, step_size_init_ms: float
    ) -> tuple[np.ndarray | None, dict]:
        """
        Resamples loaded signals from an MF4 file to a uniform time basis.
        This function finds the latest start time and earliest end time to create a global
        time vector. It then resamples all numeric signals to this time basis using linear
        interpolation. Non-numeric or invalid signals are handled by creating an array of `None` values.

        :param data_raw: A dictionary where keys are signal names and values are tuples
                            containing (timestamps: np.ndarray, samples: np.ndarray).
        :param step_size_init_ms: The target resampling step size in milliseconds.
        :return: A tuple containing:
                1. The global time vector (np.ndarray) for the resampled data, or `None` if no valid data range is found.
                2. A dictionary where keys are signal names and values are the resampled sample arrays (np.ndarray).
        """
        try:
            latest_start_time = 0
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

            data_resampled = {}
            for signal_name, (timestamps, samples) in data_raw.items():
                if (
                    isinstance(
                        timestamps, np.ndarray
                    )  # check if 'timestamps' is a NumPy array
                    and np.issubdtype(
                        timestamps.dtype, np.number
                    )  # and if its elements are numbers.
                    and isinstance(
                        samples, np.ndarray
                    )  # check if 'samples' is a NumPy array
                    and np.issubdtype(
                        samples.dtype, np.number
                    )  # and if its elements are numbers.
                    and len(timestamps)
                    > 0  # check that the 'timestamps' array is not empty.
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
                    none_array = np.array([None] * num_samples)
                    data_resampled[signal_name] = none_array
                    self.logfile.write(
                        f"Signal '{signal_name}' could not be read from measurement file.",
                        level="INFO",
                    )

            self.logfile.write(
                f"Data source file successfully resampled.", level="INFO"
            )
            return global_time_vector, data_resampled

        except Exception as e:
            self.logfile.write(
                f"Error during preprocessing mf4 data source file: {e}", level="ERROR"
            )
            return None, {}

    def _eval_output_path(self, file_path: str) -> str | None:
        """
        Adds a timestamp to the filename in the given file path to prevent overwriting.
        The format is `*_YYYYMMDD_HHMMSS*` before the file extension.

        :param file_path: The original path to the output file.
        :return: The new file path with a timestamp, or `None` if an error occurs.
        """
        try:
            base, ext = os.path.splitext(file_path)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            new_file_path = f"{base}_{timestamp}{ext}"
            return new_file_path

        except Exception as e:
            self.logfile.write(
                f"Evaluation of data output name failed: {e}", level="ERROR"
            )
            return None

    def get(self, step_size_ms: float) -> dict | None:
        """
        Retrieves and resamples the processed data from all sources within `self.data`.
        It resamples each source to the specified `step_size_ms` and merges them into a single dictionary.
        This combined dictionary is intended for use by a subsequent workflow element.

        :param step_size_ms: The target resampling step size in milliseconds.
        :return: A merged dictionary containing all resampled signals and their timestamps,
                or `None` if an error occurs during resampling or merging.
        """
        try:
            out_data = {}
            source = []
            source_string = ""

            for data_source_name, data_source_value in self.data.items():

                data_source_value = self._resample(
                    data_raw=data_source_value, step_size_ms=step_size_ms
                )

                out_data.update(data_source_value)
                source.append(data_source_name)

            source_string = " <- ".join(source)
            self.logfile.write(
                f"Simulation input data got merged from sources: {source_string}",
                level="INFO",
            )
            return out_data

        except Exception as e:
            self.logfile.write(
                f"Error occurred while merging simulation input data from sources {source_string}: {e}",
                level="ERROR",
            )
            return None

    def _resample(self, data_raw: dict, step_size_ms: float) -> dict | None:
        """
        Resamples all numeric signals in a given data dictionary to a new, uniform time basis.
        It assumes that all signals in `data_raw` share the same time vector, which is stored
        under the key `'timestamp'`.

        :param data_raw: A dictionary containing the `'timestamp'` array and other signal arrays.
        :param step_size_ms: The target resampling step size in milliseconds.
        :return: A new dictionary with the new `'timestamp'` and the corresponding resampled signals,
                or `None` if an error occurs.
        """
        try:
            timestamp = data_raw["timestamp"]
            step_size_s = step_size_ms / 1000.0
            timestamp_resampled = np.arange(
                timestamp[0], timestamp[-1] + step_size_s, step_size_s
            )
            data_resampled = {"timestamp": timestamp_resampled}

            for signal_name, signal_value in data_raw.items():
                if (
                    np.issubdtype(signal_value.dtype, np.number)
                    and signal_name != "timestamp"
                ):
                    resampled = np.interp(timestamp_resampled, timestamp, signal_value)
                    data_resampled[signal_name] = resampled

            self.logfile.write(f"Resampling successfully finished.", level="INFO")
            return data_resampled

        except Exception as e:
            self.logfile.write(f"Error during resampling: {e}", level="ERROR")
            return None
