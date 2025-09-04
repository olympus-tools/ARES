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
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np
from typeguard import typechecked

from ares.core.logfile import Logfile
from ares.utils.data.mf4_interface import DataMF4interface


class Data:
    @typechecked
    def __init__(
        self,
        file_path: str,
        source: Iterable[str],
        step_size_init_ms: int,
        logfile: Logfile,
    ):
        """Initializes the Data class by reading a data source file.

        The constructor automatically loads and preprocesses the data based on the file
        extension. The processed data is stored in the `self.data` attribute.

        Args:
            file_path (str): The path to the data source file (.mf4, .parquet, or .mat).
            source (Iterable[str]): Specifies which source(s) from the data file to include.
                Use ['all'] to load all sources, or a list of specific source names (e.g.,
                ['source1', 'source2']).
            step_size_init_ms (int): The target resampling step size in milliseconds for
                the initial loading.
            logfile (Logfile): The logfile object of the current ARES pipeline.
        """
        self._file_path = file_path
        self._logfile = logfile
        data: Dict[str, Dict[str, Any]] = {"base": {}}

        # get fileformat to trigger the correct loading pipeline
        input_format = os.path.splitext(self._file_path)[1].lower()
        if input_format == ".mf4":
            self.data = DataMF4interface.load_mf4(
                file_path=self._file_path,
                data=data,
                source=list(source),
                step_size_init_ms=step_size_init_ms,
                logfile=self._logfile,
            )
        elif input_format == ".parquet":
            self.data = None
            self._logfile.write(
                "Evaluation of .parquet input/output is not implemented yet",
                level="ERROR",
            )  # TODO
        elif input_format == ".mat":
            self.data = None
            self._logfile.write(
                "Evaluation of .mat input/output is not implemented yet", level="ERROR"
            )  # TODO
        else:
            self.data = None
            self._logfile.write(
                f"Unknown file format for {self._file_path}.", level="ERROR"
            )

    @typechecked
    def write_out(
        self,
        dir_path: str,
        output_format: str,
        element_workflow: list[str],
        source: list[str],
    ) -> Optional[str]:
        """Writes data from a specified source within `self.data` to an output file.

        The final file path is constructed by combining `dir_path` with a new filename,
        which includes a timestamp and the specified `output_format`.
        Currently, only .mf4 output is supported.

        Args:
            dir_path (str): The path to the output directory.
            output_format (str): The desired file extension (e.g., 'mf4').
            element_workflow (list[str]): The workflow elements associated with the data.
            source (list[str]): A list of keys from `self.data` to be written. Use ['all']
                to write all available sources.

        Returns:
            str or None: The full path of the output file, or None if an error occurs.
        """
        file_path = self._eval_output_path(
            dir_path=dir_path, output_format=output_format
        )

        output_data, log_sources = self._define_write_out_dict(
            source=source, element_workflow=element_workflow
        )

        if output_format == "mf4":
            DataMF4interface.write_out_mf4(
                file_path=file_path,
                data=output_data,
                log_sources=log_sources,
                logfile=self._logfile,
            )
        elif output_format == "parquet":
            self._logfile.write(
                "Evaluation of .parquet input/output is not implemented yet",
                level="ERROR",
            )  # TODO
        elif output_format == "mat":
            self._logfile.write(
                "Evaluation of .mat input/output is not implemented yet", level="ERROR"
            )  # TODO
        else:
            self._logfile.write(
                f"Unsupported data output file format: {output_format}.",
                level="WARNING",
            )
            file_path = None

        return file_path

    @typechecked
    def _define_write_out_dict(
        self, source: List[str], element_workflow: List[str]
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Defines the subset of data that should be written to an output file.

        Args:
            source (list[str]): The data sources to write, or ['all'] to include all
                sources present in element_workflow.
            element_workflow (list[str]): The workflow elements available for writing.

        Returns:
            tuple[dict or None, str or None]: A tuple containing:
                - The data dictionary prepared for output. Returns `None` if an error occurs.
                - A description of which sources were selected for writing. Returns `None`
                  if an error occurs.
        """
        try:
            output_data: Dict[str, Any] = {}

            if "all" in source:
                all_data_keys = set(self.data.keys())
                all_element_keys = set(element_workflow)
                source_list = list(all_data_keys.intersection(all_element_keys))
                log_sources = "all available sources present in element_workflow"
            else:
                source_list = [
                    wf_element_name
                    for wf_element_name in source
                    if wf_element_name in element_workflow
                ]
                log_sources = str(source_list)

            for wf_element_name in source_list:
                if wf_element_name in self.data:
                    output_data[wf_element_name] = self.data[wf_element_name]

            return output_data, log_sources

        except Exception as e:
            self._logfile.write(
                f"Error occurred while defining write-out dictionary: {e}",
                level="ERROR",
            )
            return None, None

    @typechecked
    def _eval_output_path(self, dir_path: str, output_format: str) -> Optional[str]:
        """Adds a timestamp to the filename and returns a complete, absolute file path.

        The format is `*_YYYYMMDD_HHMMSS*` before the file extension.

        Args:
            dir_path (str): The absolute path to the output directory.
            output_format (str): The desired file extension (e.g., 'mf4'). The leading dot
                is added automatically.

        Returns:
            str or None: The new, complete file path with a timestamp, or None if an
                error occurs.
        """
        try:
            os.makedirs(dir_path, exist_ok=True)
            file_name = os.path.splitext(os.path.basename(self._file_path))[0]
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            new_file_name = f"{file_name}_{timestamp}.{output_format}"
            full_path = os.path.join(dir_path, new_file_name)
            return full_path

        except Exception as e:
            self._logfile.write(
                f"Evaluation of data output name failed: {e}", level="ERROR"
            )
            return None

    @typechecked
    def get(self, step_size_ms: float) -> Optional[Dict[str, np.ndarray]]:
        """Retrieves and resamples the processed data from all sources within `self.data`.

        It resamples each source to the specified `step_size_ms` and merges them into a
        single dictionary. This combined dictionary is intended for use by a subsequent
        workflow element.

        Args:
            step_size_ms (float): The target resampling step size in milliseconds.

        Returns:
            dict or None: A merged dictionary containing all resampled signals and their
                timestamps, or None if an error occurs during resampling or merging.
        """
        try:
            out_data: Dict[str, np.ndarray] = {}
            source_list: List[str] = []

            for data_source_name, data_source_value in self.data.items():
                resampled_data = self._resample(
                    data_raw=data_source_value, step_size_ms=step_size_ms
                )

                out_data.update(resampled_data)
                source_list.append(data_source_name)

            source_string = " <- ".join(source_list)
            self._logfile.write(
                f"Simulation input data got merged from sources: {source_string}",
                level="INFO",
            )
            return out_data

        except Exception as e:
            self._logfile.write(
                f"Error occurred while merging simulation input data: {e}",
                level="ERROR",
            )
            return None

    @typechecked
    def _resample(
        self, data_raw: Dict[str, np.ndarray], step_size_ms: float
    ) -> Optional[Dict[str, np.ndarray]]:
        """Resamples all numeric signals in a data dictionary to a uniform time basis.

        It assumes that all signals in `data_raw` share the same time vector, which is
        stored under the key 'timestamp'.

        Args:
            data_raw (dict[str, np.ndarray]): A dictionary containing the 'timestamp'
                array and other signal arrays.
            step_size_ms (float): The target resampling step size in milliseconds.

        Returns:
            dict or None: A new dictionary with the new 'timestamp' and
                the corresponding resampled signals, or None if an error occurs.
        """
        try:
            timestamp = data_raw["timestamp"]
            step_size_s = step_size_ms / 1000.0
            timestamp_resampled = np.arange(
                timestamp[0], timestamp[-1] + step_size_s, step_size_s
            )
            data_resampled: Dict[str, np.ndarray] = {"timestamp": timestamp_resampled}

            for signal_name, signal_value in data_raw.items():
                if (
                    isinstance(signal_value, np.ndarray)
                    and np.issubdtype(signal_value.dtype, np.number)
                    and signal_name != "timestamp"
                ):
                    resampled = np.interp(timestamp_resampled, timestamp, signal_value)
                    data_resampled[signal_name] = resampled
                # Non-numeric or non-timestamp signals are ignored during resampling

            self._logfile.write("Resampling successfully finished.", level="INFO")
            return data_resampled

        except Exception as e:
            self._logfile.write(f"Error during resampling: {e}", level="ERROR")
            return None
