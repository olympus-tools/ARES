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
from typing import Any, Dict, Iterable, List, Optional

import numpy as np
from typeguard import typechecked

from ares.utils.data.mf4_interface import DataMF4interface
from ares.utils.logger import create_logger

logger = create_logger("data")


class Data:
    @typechecked
    def __init__(
        self,
        file_path: str,
        base_wf_element_name: str,
        source: Iterable[str],
        step_size_init_ms: int,
    ):
        """Initializes the Data class by reading a data source file.

        The constructor automatically loads and preprocesses the data based on the file
        extension. The processed data is stored in the `self.data` attribute.

        Args:
            file_path (str): The path to the data source file (.mf4, .parquet, or .mat).
            base_wf_element_name (str): The base name of the workflow element associated
                with this data source.
            source (Iterable[str]): Specifies which source(s) from the data file to include.
                Use ['all'] to load all sources, or a list of specific source names (e.g.,
                ['source1', 'source2']).
            step_size_init_ms (int): The target resampling step size in milliseconds for
                the initial loading.
        """
        self._file_path = file_path
        self.data: Dict[Dict[str, np.ndarray]] = {base_wf_element_name: {}}

        # get fileformat to trigger the correct loading pipeline
        input_format = os.path.splitext(self._file_path)[1].lower()
        if input_format == ".mf4":
            self.data[base_wf_element_name] = DataMF4interface.load_mf4(
                file_path=self._file_path,
                source=list(source),
                step_size_init_ms=step_size_init_ms,
            )
        elif input_format == ".parquet":
            self.data[base_wf_element_name] = None
            logger.error(
                "Evaluation of .parquet input/output is not implemented yet",
            )  # TODO:
        elif input_format == ".mat":
            self.data[base_wf_element_name] = None
            logger.error(
                "Evaluation of .mat input/output is not implemented yet"
            )  # TODO:
        else:
            self.data[base_wf_element_name] = None
            logger.error(f"Unknown file format for {self._file_path}.")

    @typechecked
    def write_out(
        self,
        dir_path: str,
        output_format: str,
        meta_data: Dict[str, Any],
        element_input_workflow: list[str],
        source: list[str],
    ) -> Optional[str]:
        """Writes data from a specified source within `self.data` to an output file.

        The final file path is constructed by combining `dir_path` with a new filename,
        which includes a timestamps and the specified `output_format`.
        Currently, only .mf4 output is supported.

        Args:
            dir_path (str): The path to the output directory.
            output_format (str): The desired file extension (e.g., 'mf4').
            meta_data (dict[str, any]): Current ARES and workstation meta data.
            element_input_workflow (list[str]): The workflow elements associated with the data.
            source (list[str]): A list of keys from `self.data` to be written. Use ['all']
                to write all available sources.

        Returns:
            str or None: The full path of the output file, or None if an error occurs.
        """
        file_path = self._eval_output_path(
            dir_path=dir_path, output_format=output_format
        )

        output_data = self._define_write_out_data(
            source=source, element_input_workflow=element_input_workflow
        )

        if output_format == "mf4":
            DataMF4interface.write_out_mf4(
                file_path=file_path,
                data=output_data,
                meta_data=meta_data,
            )
        elif output_format == "parquet":
            logger.error(
                "Evaluation of .parquet input/output is not implemented yet",
            )  # TODO:
        elif output_format == "mat":
            logger.error(
                "Evaluation of .mat input/output is not implemented yet",
            )  # TODO:
        else:
            logger.warning(
                f"Unsupported data output file format: {output_format}.",
            )
            file_path = None

        return file_path

    @typechecked
    def _define_write_out_data(
        self, source: List[str], element_input_workflow: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Defines the subset of data that should be written to an output file.

        Args:
            source (list[str]): The data sources to write, or ['all'] to include all
                sources present in element_input_workflow.
            element_input_workflow (list[str]): The workflow elements available for writing.

        Returns:
            dict or None: The data dictionary prepared for output. Returns `None` if an error occurs.
        """
        try:
            output_data: Dict[str, Any] = {}

            if "all" in source:
                all_data_keys = set(self.data.keys())
                all_element_keys = set(element_input_workflow)
                source_list = list(all_data_keys.intersection(all_element_keys))
            else:
                source_list = [
                    wf_element_name
                    for wf_element_name in source
                    if wf_element_name in element_input_workflow
                ]

            for wf_element_name in source_list:
                if wf_element_name in self.data:
                    output_data[wf_element_name] = self.data[wf_element_name]

            return output_data

        except Exception as e:
            logger.error(
                f"Error occurred while defining write-out dictionary: {e}",
            )
            return None

    @typechecked
    def _eval_output_path(self, dir_path: str, output_format: str) -> Optional[str]:
        """Adds a timestamps to the filename and returns a complete, absolute file path.

        The format is `*_YYYYMMDD_HHMMSS*` before the file extension.

        Args:
            dir_path (str): The absolute path to the output directory.
            output_format (str): The desired file extension (e.g., 'mf4'). The leading dot
                is added automatically.

        Returns:
            str or None: The new, complete file path with a timestamps, or None if an
                error occurs.
        """
        try:
            os.makedirs(dir_path, exist_ok=True)
            file_name = os.path.splitext(os.path.basename(self._file_path))[0]
            timestamps = datetime.now().strftime("%Y%m%d%H%M%S")
            new_file_name = f"{file_name}_{timestamps}.{output_format}"
            full_path = os.path.join(dir_path, new_file_name)
            return full_path

        except Exception as e:
            logger.error(f"Evaluation of data output name failed: {e}")
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
            logger.info(
                f"Simulation input data got merged from sources: {source_string}",
            )
            return out_data

        except Exception as e:
            logger.error(
                f"Error occurred while merging simulation input data: {e}",
            )
            return None

    @typechecked
    def _resample(
        self, data_raw: Dict[str, np.ndarray], step_size_ms: float
    ) -> Optional[Dict[str, np.ndarray]]:
        """Resamples all numeric signals in a data dictionary to a uniform time basis.

        It assumes that all signals in `data_raw` share the same time vector, which is
        stored under the key 'timestamps'.

        Args:
            data_raw (dict[str, np.ndarray]): A dictionary containing the 'timestamps'
                array and other signal arrays.
            step_size_ms (float): The target resampling step size in milliseconds.

        Returns:
            dict or None: A new dictionary with the new 'timestamps' and
                the corresponding resampled signals, or None if an error occurs.
        """
        try:
            timestamps = data_raw["timestamps"]
            step_size_s = step_size_ms / 1000.0
            timestamp_resampled = np.arange(
                timestamps[0], timestamps[-1] + step_size_s, step_size_s
            )
            data_resampled: Dict[str, np.ndarray] = {"timestamps": timestamp_resampled}

            for signal_name, signal_value in data_raw.items():
                if (
                    isinstance(signal_value, np.ndarray)
                    and np.issubdtype(signal_value.dtype, np.number)
                    and signal_name != "timestamps"
                ):
                    # TODO: resampling should also be possible for 1D arrays and 2D arrays, not only scalars
                    if signal_value.ndim == 1:
                        resampled = np.interp(
                            timestamp_resampled, timestamps, signal_value
                        )
                        data_resampled[signal_name] = resampled
                    else:
                        logger.debug(
                            f"Signal '{signal_name}' is not able to be resampled."
                        )
                # Non-numeric or non-timestamps signals are ignored during resampling

            logger.debug("Resampling successfully finished.")
            return data_resampled

        except Exception as e:
            logger.error(f"Error during resampling: {e}")
            return None
