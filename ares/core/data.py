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

from ares.core.logfile import Logfile
import os
from datetime import datetime
from asammdf import MDF, Signal, Source
import numpy as np
from typeguard import typechecked

class Data:
    @typechecked
    def __init__(self, file_path: str, source: list, step_size_init_ms: int, logfile: Logfile):
        """
        Initializes the Data class by reading a data source file.

        The constructor automatically loads and preprocesses the data based on the file extension.
        The processed data is stored in the `self.data` attribute.

        Args:
            file_path (str): The path to the data source file (.mf4, .parquet, or .mat).
            source (list): Specifies which source(s) from the data file to include.
                Use `['all']` to load all sources, or a list of specific source names (e.g., `['source1', 'source2']`).
            step_size_init_ms (int): The target resampling step size in milliseconds for the initial loading.
            logfile (Logfile): The logfile object of the current ARES pipeline.
        """
        self._file_path = file_path
        self._logfile_path = logfile
        self.source = set(source)
        self.data = {}
        self.data["base"] = {}

        # get fileformat to trigger the correct loading pipeline
        input_format = os.path.splitext(self._file_path)[1].lower()
        if input_format == ".mf4":
            self._load_mf4(step_size_init_ms=step_size_init_ms)
        elif input_format == ".parquet":
            self._logfile_path.write(
                f"Evaluation of .parquet input/output is not implemented yet",
                level="ERROR",
            )  # TODO
        elif input_format == ".mat":
            self._logfile_path.write(
                f"Evaluation of .mat input/output is not implemented yet", level="ERROR"
            )  # TODO
        else:
            self._logfile_path.write(
                f"Unknown file format for {self._file_path}.", level="ERROR"
            )

    @typechecked
    def _load_mf4(self, step_size_init_ms: float = None):
        """
        Loads an .mf4 file, extracts signals from specified sources, and preprocesses them.

        Preprocessing includes finding a common time basis, resampling, and storing the
        results in `self.data` under the key 'base'.

        Args:
            step_size_init_ms (float): The target resampling step size in milliseconds.
        """
        try:
            with MDF(self._file_path) as datasource:
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
                    self._logfile_path.write(
                        f"No signals found matching the specified source {self.source} in {self._file_path}.",
                        level="WARNING",
                    )

                time_vector, data_resampled = self._preprocessing_mf4(
                    data_raw=data_raw, step_size_init_ms=step_size_init_ms
                )
                self.data["base"]["timestamp"] = time_vector
                self.data["base"].update(data_resampled)

                self._logfile_path.write(
                    f"Source '{self.source}' from .mf4 file {self._file_path} loaded successfully (nested data under source 'base')."
                )

        except Exception as e:
            self._logfile_path.write(
                f"Error loading .mf4 file {self._file_path}: {e}", level="ERROR"
            )

    @typechecked
    def write_out(self, dir_path: str, output_format: str, element_workflow: list, source: list) -> str | None:
        """
        Writes data from a specified source within `self.data` to an output file.

        The final file path is constructed by combining `dir_path` with a new filename,
        which includes a timestamp and the specified `output_format`.
        Currently, only .mf4 output is supported.

        Args:
            dir_path (str): The path to the output directory.
            output_format (str): The desired file extension (e.g., 'mf4').
            element_workflow (list): The workflow elements associated with the data.
            source (list): A list of keys from `self.data` to be written. Use `['all']` to write all available sources.

        Returns:
            str | None: The full path of the output file, or `None` if an error occurs.
        """
        try:

            file_path = self._eval_output_path(dir_path=dir_path, output_format=output_format)

            if output_format == "mf4":
                self._write_out_mf4(
                    file_path=file_path,
                    element_workflow=element_workflow,
                    source=source,
                )
            elif output_format == "parquet":
                self._logfile_path.write(
                    f"Evaluation of .parquet input/output is not implemented yet",
                    level="ERROR",
                )  # TODO
            elif output_format == "mat":
                self._logfile_path.write(
                    f"Evaluation of .mat input/output is not implemented yet",
                    level="ERROR",
                )  # TODO
            else:
                self._logfile_path.write(
                    f"Unsupported output file format: {output_format}.", level="WARNING"
                )

            return file_path

        except Exception as e:
            self._logfile_path.write(
                f"Error writing data to {dir_path} from source '{source}': {e}",
                level="ERROR",
            )
            return None

    @typechecked
    def _write_out_mf4(self, file_path: str, element_workflow: list, source: list = None):
        """
        Writes data from the specified sources in `self.data` to an .mf4 file.

        It iterates through the provided `source` keys, creates `asammdf.Signal` objects,
        and appends them to a new `asammdf.MDF` file.

        Args:
            file_path (str): The path to the output file.
            element_workflow (list): The workflow elements associated with the data.
            source (list): A list of keys from `self.data` to export. If `['all']`,
                all available keys are used.
        """
        try:
            if "all" in source:
                all_data_keys = set(self.data.keys())
                all_element_keys = set(element_workflow)
                source = list(all_data_keys.intersection(all_element_keys))
                log_sources = "all available sources present in element_workflow"
            elif isinstance(source, list):
                source = [
                    wf_element_name
                    for wf_element_name in source
                    if wf_element_name in element_workflow
                ]
                log_sources = str(source)

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
                                self._logfile_path.write(
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
                        self._logfile_path.write(
                            f"Skipping key '{source_key}' not found in simulation 'data' element.",
                            level="WARNING",
                        )

                if not all_signals_to_write:
                    self._logfile_path.write(
                        f"No valid signals found to write for source {log_sources} to {file_path}.",
                        level="WARNING",
                    )

                output_file_mf4.append(all_signals_to_write, comment=f"ares simulation result")
                output_file_mf4.save(file_path, overwrite=False)
                self._logfile_path.write(f"Output .mf4 file written successfully to {file_path} with source(s) {log_sources}.")

        except Exception as e:
            self._logfile_path.write(
                f"Error saving .mf4 file to {file_path} with source(s) {log_sources}: {e}",
                level="ERROR",
            )

    @typechecked
    def _preprocessing_mf4(
        self, data_raw: dict, step_size_init_ms: float
    ) -> tuple[np.ndarray | None, dict]:
        """
        Resamples loaded signals from an MF4 file to a uniform time basis.

        This function finds the latest start time and earliest end time to create a global
        time vector. It then resamples all numeric signals to this time basis using linear
        interpolation. Non-numeric or invalid signals are handled by creating an array of `None` values.

        Args:
            data_raw (dict): A dictionary where keys are signal names and values are tuples
                containing `(timestamps: np.ndarray, samples: np.ndarray)`.
            step_size_init_ms (float): The target resampling step size in milliseconds.

        Returns:
            tuple[np.ndarray | None, dict]: A tuple containing:
                1. The global time vector (`np.ndarray`) for the resampled data, or `None` if no valid data range is found.
                2. A dictionary where keys are signal names and values are the resampled sample arrays (`np.ndarray`).
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
                    self._logfile_path.write(
                        f"Signal '{signal_name}' could not be read from measurement file.",
                        level="INFO",
                    )

            self._logfile_path.write(
                f"Data source file successfully resampled.", level="INFO"
            )
            return global_time_vector, data_resampled

        except Exception as e:
            self._logfile_path.write(
                f"Error during preprocessing mf4 data source file: {e}", level="ERROR"
            )
            return None, {}

    @typechecked
    def _eval_output_path(self, dir_path: str, output_format: str) -> str | None:
        """
        Adds a timestamp to the filename and returns a complete, absolute file path to prevent overwriting.

        The format is `*_YYYYMMDD_HHMMSS*` before the file extension.

        Args:
            dir_path (str): The absolute path to the output directory.
            output_format (str): The desired file extension (e.g., 'mf4'). The leading dot is added automatically.

        Returns:
            str | None: The new, complete file path with a timestamp, or `None` if an error occurs.
        """
        try:
            file_name = os.path.splitext(os.path.basename(self._file_path))[0]
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            new_file_name = f"{file_name}_{timestamp}.{output_format}"
            full_path = os.path.join(dir_path, new_file_name)
            return full_path

        except Exception as e:
            self._logfile_path.write(
                f"Evaluation of data output name failed: {e}", level="ERROR"
            )
            return None

    @typechecked
    def get(self, step_size_ms: float) -> dict | None:
        """
        Retrieves and resamples the processed data from all sources within `self.data`.

        It resamples each source to the specified `step_size_ms` and merges them into a
        single dictionary. This combined dictionary is intended for use by a subsequent
        workflow element.

        Args:
            step_size_ms (float): The target resampling step size in milliseconds.

        Returns:
            dict | None: A merged dictionary containing all resampled signals and their timestamps,
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
            self._logfile_path.write(
                f"Simulation input data got merged from sources: {source_string}",
                level="INFO",
            )
            return out_data

        except Exception as e:
            self._logfile_path.write(
                f"Error occurred while merging simulation input data from sources {source_string}: {e}",
                level="ERROR",
            )
            return None

    @typechecked
    def _resample(self, data_raw: dict, step_size_ms: float) -> dict | None:
        """
        Resamples all numeric signals in a given data dictionary to a new, uniform time basis.

        It assumes that all signals in `data_raw` share the same time vector, which is stored
        under the key `'timestamp'`.

        Args:
            data_raw (dict): A dictionary containing the `'timestamp'` array and other signal arrays.
            step_size_ms (float): The target resampling step size in milliseconds.

        Returns:
            dict | None: A new dictionary with the new `'timestamp'` and the corresponding resampled signals,
                or `None` if an an error occurs.
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

            self._logfile_path.write(f"Resampling successfully finished.", level="INFO")
            return data_resampled

        except Exception as e:
            self._logfile_path.write(f"Error during resampling: {e}", level="ERROR")
            return None
