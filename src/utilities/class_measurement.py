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
# Licensed under the GNU LGPLv3 License. You may obtain a copy of the 
# License at
#
#     https://github.com/AndraeCarotta/ARES/blob/master/LICENSE
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""

import os
from asammdf import MDF, Signal, Source
import ares_globals
import numpy as np

class Measurement:
    def __init__(self, file_path: str, sources_import: list = None, step_size_ms = 10):
        """
        Initializes the Measurement class with the file path.

        :param file_path: The path to the measurement file (.mf4 or .parquet).
        :param sources: Specifies which sources in the measurement file should be considered for 'base'.
                        Pass None (default) for 'all' sources, or a list of source names (list of str).
        :param step_size_ms: The target resampling step size in milliseconds.
        """
        self.file_path = file_path
        self.step_size_ms = step_size_ms

        if sources_import is None:
            self.sources_import = 'all'
        elif isinstance(sources_import, list):
            self.sources_import = set(sources_import)
        else:
            raise TypeError("The 'sources' parameter must be a list of strings or None (for 'all' sources).")

        self.data = {}
        self.data['base'] = {}

        file_format = os.path.splitext(self.file_path)[1].lower()

        if file_format == '.mf4':
            self._load_mf4()
        elif file_format == '.parquet':
            self._load_parquet(),
        elif file_format == '.mat':
            self._load_mat()
        else:
            ares_globals.logfile.write(f"Unknown file format for {self.file_path}.", level="WARNING")

    def _load_mf4(self):
        """
        Loads an MF4 file, extracts filtered signals, and performs custom resampling.
        """
        try:
            with MDF(self.file_path) as measurement:
                signals_raw = {}
                for signal in measurement.iter_channels():
                    source_name = signal.source.path if hasattr(signal.source, 'path') else None
                    if not source_name and hasattr(signal.source, 'path'):
                         source_name = signal.source.path

                    # Filter signals based on specified sources
                    if self.sources_import == 'all' or (source_name and source_name in self.sources_import):
                        signals_raw[signal.name] = (signal.timestamps, signal.samples)

                if not signals_raw:
                    ares_globals.logfile.write(f"No signals found matching the specified sources in {self.file_path}.", level="INFO")

                time_vector, resampled_signals = self._resample(signals_raw, self.step_size_ms)
                self.data['base']['timestamps'] = time_vector
                self.data['base'].update(resampled_signals)

                ares_globals.logfile.write(f"Sources '{self.sources_import}' from MF4 file {self.file_path} loaded and resampled successfully (nested data under 'base').")

        except Exception as e:
            ares_globals.logfile.write(f"Error loading MF4 file {self.file_path}: {e}", level="ERROR")

    def _load_parquet(self):
        """
        Loads a Parquet file and stores the data.
        """
        ares_globals.logfile.write("Parquet loading is not yet implemented.", level="ERROR")

    def _load_mat(self):
        """
        Loads a .mat file and stores the data.
        """
        ares_globals.logfile.write("Mat loading is not yet implemented.", level="ERROR")

    def write_out(self, file_path: str, sources: list = None):
        """
        Writes the data to a specified file format from a given source within self.data.

        :param file_path: The path to the output file.
        :param sources: The key in self.data from which to retrieve the data for writing.
                       Defaults to 'base'.
        """
        try:
            file_format = os.path.splitext(file_path)[1].lower()
            
            if file_format == ".mf4":
                self._write_out_mf4(file_path, sources)
            elif file_format == ".parquet":
                self._write_out_parquet(file_path, sources)
            elif file_format == ".mat":
                self._write_out_mat(file_path, sources)
            else:
                ares_globals.logfile.write(f"Unsupported output file format: {file_format}.", level="WARNING")

            ares_globals.logfile.write(f"Data written successfully to {file_path} from source '{sources}'")

        except Exception as e:
            ares_globals.logfile.write(f"Error writing data to {file_path} from source '{sources}': {e}", level="ERROR")

    def _write_out_mf4(self, file_path: str, sources_export: list = None):
        """
        Writes data from specified keys in self.data to an MF4 file.

        :param file_path: The path to the output MF4 file.
        :param sources_export: A list of keys from self.data to export.
                                  If None, all keys in self.data (except 'base' if not specified) will be attempted.
        """
        if sources_export is None:
            keys_to_process = list(self.data.keys())
            log_sources = "all available sources"
        elif isinstance(sources_export, list):
            keys_to_process = sources_export
            log_sources = str(sources_export)
        else:
            ares_globals.logfile.write(f"Invalid type for 'sources_export'. Must be a list or None.", level="ERROR")

        all_signals_to_write = []
        
        with MDF() as new_file:
            for source_key in keys_to_process:
                if source_key in self.data and isinstance(self.data[source_key], dict) and 'timestamps' in self.data[source_key]:
                    data_to_write = self.data[source_key]
                    timestamps = data_to_write['timestamps']

                    src = Source(name=source_key, path=source_key, comment=f"Data from {source_key}", source_type=1, bus_type=1)

                    for signal_name, samples in data_to_write.items():

                        if isinstance(samples, np.ndarray) and len(samples) == len(timestamps):
                            # Ensure numeric type, convert if necessary
                            if samples.dtype == np.object_:
                                try:
                                    samples = samples.astype(np.float64)
                                except ValueError:
                                    ares_globals.logfile.write(f"Error: Signal '{signal_name}' in source '{source_key}' could not be converted to float64. Skipping.", level="WARNING")
                                    continue
                            elif not np.issubdtype(samples.dtype, np.number):
                                ares_globals.logfile.write(f"Warning: Signal '{signal_name}' in source '{source_key}' has non-numeric dtype '{samples.dtype}'. Skipping.", level="WARNING")
                                continue

                            signal = Signal(
                                samples=samples,
                                timestamps=timestamps,
                                name=signal_name,
                                source=src,
                                comment=""
                            )
                            all_signals_to_write.append(signal)
                        else:
                            ares_globals.logfile.write(f"Skipping signal '{signal_name}' from source '{source_key}'. Sample length does not match timestamp length or is not a NumPy array.", level="WARNING")
                else:
                    ares_globals.logfile.write(f"Skipping key '{source_key}' for MF4 export: Not a valid data structure or missing 'timestamps'.", level="WARNING")
            
            if not all_signals_to_write:
                ares_globals.logfile.write(f"No valid signals found to write for sources {log_sources} to {file_path}.", level="WARNING")

            try:
                new_file.append(all_signals_to_write, comment=f'ARES simulation result')
                new_file.save(file_path, overwrite=True)
                ares_globals.logfile.write(f"MF4 file written successfully to {file_path} with sources {log_sources}.")
            except Exception as e:
                ares_globals.logfile.write(f"Error saving MF4 file to {file_path} with sources {log_sources}: {e}", level="ERROR")

    def _write_out_parquet(self, file_path: str, source: list = None):
        """
        Writes the data to a Parquet file (not implemented).

        :param file_path: The path to the output Parquet file.
        :param source: The key in the self.data from which to retrieve the data.
        """
        ares_globals.logfile.write("Writing to Parquet file is not yet implemented.", level="ERROR")

    def _write_out_mat(self, file_path: str, source: list = None):
        """
        Writes the data to a .mat file (not implemented).

        :param file_path: The path to the output .mat file.
        :param source: The key in the self.data from which to retrieve the data.
        """
        ares_globals.logfile.write("Writing to .mat file is not yet implemented.", level="ERROR")

    def _resample(self, signals_raw: dict, step_size_ms: float) -> tuple[np.ndarray | None, dict]:
        """
        Resamples the loaded signals to a uniform time basis (custom) with a global time vector and handles non-numeric data.

        :param signals_raw: A dictionary where keys are signal names and values are tuples
                              containing (timestamps: np.ndarray, samples: np.ndarray).
        :param step_size_ms: The target resampling step size in milliseconds.
        :return: A tuple containing the global time vector (np.ndarray | None if no valid range)
                 and a dictionary where keys are signal names and values are the resampled sample arrays (np.ndarray).
        """
        try:
            latest_start_time = 0
            earliest_end_time = np.inf

            # Find the latest start time and the earliest end time across all numeric signals
            for timestamps, _ in signals_raw.values():
                if isinstance(timestamps, np.ndarray) and np.issubdtype(timestamps.dtype, np.number) and len(timestamps) > 0:
                    latest_start_time = max(latest_start_time, timestamps[0])
                    earliest_end_time = min(earliest_end_time, timestamps[-1])

            if latest_start_time >= earliest_end_time:
                ares_globals.logfile.write("No valid numeric time range found for resampling (nested data under 'base').", level="WARNING")
                return None, {}

            target_rate_hz = 1000.0 / step_size_ms
            global_time_vector = np.arange(0, (earliest_end_time - latest_start_time) + (1 / target_rate_hz), 1 / target_rate_hz)

            resampled_signals = {}
            for signal_name, (timestamps, samples) in signals_raw.items():
                if isinstance(timestamps, np.ndarray) and np.issubdtype(timestamps.dtype, np.number) and isinstance(samples, np.ndarray) and np.issubdtype(samples.dtype, np.number) and len(timestamps) > 0:
                    # Make timestamps relative to the latest start time
                    relative_timestamps = timestamps - latest_start_time

                    # Resample the data using linear interpolation
                    resampled_samples = np.interp(global_time_vector, relative_timestamps, samples)
                    resampled_signals[signal_name] = resampled_samples
                else:
                    num_samples = len(global_time_vector) if global_time_vector is not None else 0
                    none_array = np.array([None] * num_samples)
                    resampled_signals[signal_name] = none_array
                    #ares_globals.logfile.write(f"Signal '{signal_name}' contains non-numeric data. Filled with None values (nested data under 'base').", level="WARNING")

            ares_globals.logfile.write(f"File successfully custom resampled (nested data under 'base').")
            return global_time_vector, resampled_signals

        except Exception as e:
            ares_globals.logfile.write(f"Error during custom resampling (nested data under 'base'): {e}", level="ERROR")
            return None, {}