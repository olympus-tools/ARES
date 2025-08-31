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

import json

from pydantic import ValidationError
from typeguard import typechecked

from ares.core.logfile import Logfile
from ares.models.parameter_model import ParameterModel


class ParamJSONinterface:
    @staticmethod
    @typechecked
    def load(file_path, logfile: Logfile) -> ParameterModel | None:
        """
        Reads and validates the parameters JSON file using Pydantic.

        Returns:
            ParameterModel | None: A Pydantic object representing the parameters,
                                      or None in case of an error.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                parameter_raw = json.load(file)

            for parameter_value in parameter_raw.values():
                value = parameter_value["value"]

                if isinstance(value, (int, float, str, bool)):
                    parameter_value["type"] = "scalar"
                elif isinstance(value, list):
                    if not value:
                        parameter_value["type"] = "array1d"
                    elif isinstance(value[0], list):
                        parameter_value["type"] = "array2d"
                    else:
                        parameter_value["type"] = "array1d"

            parameter = ParameterModel.model_validate(parameter_raw)

            logfile.write(
                f"Parameter file {file_path} successfully loaded and validated with Pydantic.",
                level="INFO",
            )
            return parameter

        except FileNotFoundError:
            logfile.write(
                f"Parameter file not found at '{file_path}'.",
                level="ERROR",
            )
            return None
        except json.JSONDecodeError as e:
            logfile.write(
                f"Error parsing parameter file '{file_path}': {e}",
                level="ERROR",
            )
            return None
        except ValidationError as e:
            logfile.write(
                f"Validation error in parameter file '{file_path}': {e}",
                level="ERROR",
            )
            return None
        except Exception as e:
            logfile.write(
                f"Unexpected error loading parameter file '{file_path}': {e}",
                level="ERROR",
            )
            return None

    @staticmethod
    @typechecked
    def write_out(parameter: ParameterModel, output_path: str, logfile: Logfile):
        """
        Writes the current, processed parameter object to a JSON file.

        Args:
            output_path (str): The path where the parameter should be saved.
        """
        try:
            with open(output_path, "w", encoding="utf-8") as file:
                file.write(parameter.model_dump_json(indent=4, exclude_none=True))

            logfile.write(
                f"File successfully written to {output_path}.",
                level="INFO",
            )
        except OSError as e:
            logfile.write(
                f"Failed to write parameter file to '{output_path}'. Check permissions or path: {e}",
                level="ERROR",
            )
        except Exception as e:
            logfile.write(
                f"An unexpected error occurred while writing to '{output_path}': {e}",
                level="ERROR",
            )
