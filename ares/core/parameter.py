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
from typing import Any, Dict, Optional

from typeguard import typechecked

from ares.core.logfile import Logfile
from ares.models.parameter_model import ParameterModel
from ares.utils.parameter.dcm_interface import ParamDCMinterface
from ares.utils.parameter.json_interface import ParamJSONinterface


class Parameter:
    @typechecked
    def __init__(self, file_path: str, logfile: Logfile):
        """Initializes the Parameter class by loading and validating a parameter file.

        The constructor automatically loads the parameter data based on the file
        extension and validates it using a Pydantic model. The processed data is
        stored in the `self.parameter` attribute.

        Args:
            file_path (str): The path to the parameter file (.json or .dcm).
            logfile (Logfile): The logfile object of the current ARES pipeline.
        """
        self._file_path = file_path
        self._logfile = logfile
        self.parameter: Optional[ParameterModel] = None

        input_format = os.path.splitext(self._file_path)[1].lower()
        if input_format == ".json":
            self.parameter = ParamJSONinterface.load(
                file_path=self._file_path, logfile=self._logfile
            )
        elif input_format == ".dcm":
            self.parameter = ParamDCMinterface.load(
                file_path=self._file_path, logfile=self._logfile
            )
        else:
            self._logfile.write(
                f"Unknown file format for {self._file_path}.", level="ERROR"
            )

    @typechecked
    def write_out(
        self, dir_path: str, output_format: str, meta_data: Dict[str, Any]
    ) -> Optional[str]:
        """Writes the parameter object to the specified directory in the given format.

        Args:
            dir_path (str): Directory where the output file will be written.
            output_format (str): Desired file format ('json' or 'dcm').
            meta_data (dict[str, any]): Current ARES and workstation meta data.

        Returns:
            str or None: Full path to the written file, or None if writing fails.
        """

        output_path = self._eval_output_path(
            dir_path=dir_path, output_format=output_format
        )

        if output_format == "json":
            ParamJSONinterface.write_out(
                parameter=self.parameter,
                output_path=output_path,
                logfile=self._logfile,
            )
        elif output_format == "dcm":
            ParamDCMinterface.write_out(
                parameter=self.parameter,
                output_path=output_path,
                meta_data=meta_data,
                logfile=self._logfile,
            )
        else:
            self._logfile.write(
                f"Unsupported parameter output file format: {output_format}.",
                level="WARNING",
            )
            return None

        return output_path

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
            self._logfile.write(
                f"Evaluation of data output name failed: {e}", level="ERROR"
            )
            return None
