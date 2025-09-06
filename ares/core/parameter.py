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
from typing import Any, Dict, List, Optional

from typeguard import typechecked

from ares.models.parameter_model import ParameterModel
from ares.utils.logger import create_logger
from ares.utils.parameter.dcm_interface import ParamDCMinterface
from ares.utils.parameter.json_interface import ParamJSONinterface

# initialize logger
logger = create_logger("parameter")


class Parameter:
    @typechecked
    def __init__(self, file_path: str, base_wf_element_name: str):
        """Initializes the Parameter class by loading and validating a parameter file.

        The constructor automatically loads the parameter data based on the file
        extension and validates it using a Pydantic model. The processed data is
        stored in the `self.parameter` attribute.

        Args:
            file_path (str): The path to the parameter file (.json or .dcm).
            base_wf_element_name (str): The base name of the workflow element associated
                with this data source.
        """
        self._file_path = file_path
        self.parameter: Dict[str, ParameterModel] = {
            base_wf_element_name: ParameterModel(root={})
        }

        input_format = os.path.splitext(self._file_path)[1].lower()
        if input_format == ".json":
            self.parameter[base_wf_element_name] = ParamJSONinterface.load(
                file_path=self._file_path
            )
        elif input_format == ".dcm":
            self.parameter[base_wf_element_name] = ParamDCMinterface.load(
                file_path=self._file_path
            )
        else:
            logger.error(f"Unknown file format for {self._file_path}.")

    @typechecked
    def write_out(
        self,
        dir_path: str,
        output_format: str,
        meta_data: Dict[str, Any],
        element_parameter_workflow: list[str],
        source: list[str],
    ) -> Optional[str]:
        """Writes the parameter object to the specified directory in the given format.

        Args:
            dir_path (str): Directory where the output file will be written.
            output_format (str): Desired file format ('json' or 'dcm').
            meta_data (dict[str, any]): Current ARES and workstation meta data.
            element_parameter_workflow (list[str]): The workflow elements associated with the parameter.
            source (list[str]): A list of keys from `self.parameter` to be written. Use ['all']
                to write all available sources.
        Returns:
            str or None: Full path to the written file, or None if writing fails.
        """

        output_path = self._eval_output_path(
            dir_path=dir_path, output_format=output_format
        )

        output_data = self._define_write_out_data(
            source=source, element_parameter_workflow=element_parameter_workflow
        )
        merged_parameter = ParameterModel(root=output_data)

        if output_format == "json":
            ParamJSONinterface.write_out(
                parameter=merged_parameter,
                output_path=output_path,
            )
            pass
        elif output_format == "dcm":
            ParamDCMinterface.write_out(
                parameter=merged_parameter,
                output_path=output_path,
                meta_data=meta_data,
            )
            pass
        else:
            logger.warning(
                f"Unsupported parameter output file format: {output_format}.",
            )
            return None

        return output_path

    @typechecked
    def _define_write_out_data(
        self, source: List[str], element_parameter_workflow: Optional[List[str]]
    ) -> Optional[Dict[str, Any]]:
        """Defines the subset of data that should be written to an output file.

        Args:
            source (list[str]): The data sources to write, or ['all'] to include all
                sources present in element_parameter_workflow.
            element_parameter_workflow (list[str]): The workflow elements available for writing.

        Returns:
            dict or None: The merged parameters. Returns `None` if an error occurs.
        """
        try:
            merged_parameter: Dict[str, Any] = {}

            if "all" in source:
                if element_parameter_workflow is not None:
                    all_data_keys = set(self.parameter.keys())
                    all_element_keys = set(element_parameter_workflow)
                    source_list = list(all_data_keys.intersection(all_element_keys))
                else:
                    source_list = list(self.parameter.keys())
            else:
                source_list = [
                    wf_element_name
                    for wf_element_name in source
                    if wf_element_name in element_parameter_workflow
                ]

            # merging datasets of all wf elements to one. if a parameter ist mentioned
            # in more than one wf element, the last one in the list overwrites the previous ones
            for wf_element_name in source_list:
                if wf_element_name in self.parameter:
                    param_model = self.parameter[wf_element_name]
                    for param_key, param_val in param_model.items():
                        merged_parameter[param_key] = param_val

            return merged_parameter

        except Exception as e:
            self._logfile.write(
                f"Error occurred while defining write-out dictionary: {e}",
                level="ERROR",
            )
            return None

    @typechecked
    def _eval_output_path(self, dir_path: str, output_format: str) -> Optional[str]:
        """Adds a timestamp to the filename and returns a complete, absolute file path.

        The timestamp prevents overwriting. The format is `*_YYYYMMDDHHMMSS*` before
        the file extension.

        Args:
            dir_path (str): The absolute path to the output directory.
            output_format (str): The desired file extension without a leading dot (e.g., 'json').

        Returns:
            str or None: The new, complete file path with a timestamp, or `None` if an
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
            logger.error(f"Evaluation of data output name failed: {e}")
            return None

    @typechecked
    def get(self) -> Dict[str, Any]:
        """Returns the parameter data as a dictionary.

        Returns:
            dict: The parameter data.
        """
        merged_parameter = self._define_write_out_data(
            source=["all"], element_parameter_workflow=None
        )
        return merged_parameter
