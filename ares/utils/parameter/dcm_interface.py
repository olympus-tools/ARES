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

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import ValidationError
from typeguard import typechecked

from ares.core.logfile import Logfile
from ares.models.parameter_model import ParameterElement, ParameterModel


# TODO: dcm keywor should not be implemented in parameter pydantic model
# => there should be a evaluation in the dcm write_out method
# => otherwise its not possible to import a .json and export a .dcm
# => check placeholder method "_eval_dcm_keyword"
class ParamDCMinterface:
    DCMValueLength = 6

    @staticmethod
    @typechecked
    def load(file_path: str, logfile: Logfile) -> Optional[ParameterModel]:
        """Parses a DCM file and converts it to a validated ParameterModel object.

        DAMOS DCM format is defined on:
        https://www.etas.com/ww/en/downloads/?path=%252F&page=1&order=asc&layout=table&search=TechNote_DCM_File_Formats.pdf

        Args:
            file_path (str): The path to the DCM file to be parsed.
            logfile (Logfile): The logfile object for writing messages.

        Returns:
            ParameterModel or None: Validated parameter object, or None if parsing fails.
        """
        try:
            keywords = [
                "FESTWERT",
                "TEXTSTRING",
                "KENNLINIE",
                "KENNFELD",
                "FESTWERTEBLOCK",
                "FESTKENNLINIE",
                "FESTKENNFELD",
                "GRUPPENKENNFELD",
                "GRUPPENKENNLINIE",
                "STUETZSTELLENVERTEILUNG",
            ]
            parameter_pattern = (
                r"(?:" + "|".join(map(re.escape, keywords)) + r")[\s\S]*?^END\b"
            )

            parameter: Dict[str, Any] = {}

            with open(file_path, "r", encoding="utf-8") as dcm_file:
                dcm_content = dcm_file.read()
                dcm_content = dcm_content.replace("\t", " ")
                dcm_parameters = re.findall(parameter_pattern, dcm_content, flags=re.M)

                for dcm_parameter in dcm_parameters:
                    lines = dcm_parameter.splitlines()

                    for line in lines:
                        line = re.sub(r"^\*", "", line)
                        line = line.strip()

                        if line.startswith(tuple(keywords)):
                            parameter_keyword = line.split()[0]
                            parameter_name = line.split()[1]
                            dim_str = line.split()[2:]
                            parameter[parameter_name] = {}
                            value = []
                            breakpoints_1 = []
                            breakpoints_2 = []
                            description = None
                            unit_value = None
                            unit_breakpoints_1 = None
                            unit_breakpoints_2 = None
                            name_breakpoints_1 = None
                            name_breakpoints_2 = None
                        elif line.startswith("LANGNAME"):
                            description = (
                                description_tmp.group(1)
                                if (description_tmp := re.search(r'"(.*?)"', line))
                                else None
                            )
                        elif line.startswith("EINHEIT_W"):
                            unit_value = (
                                unit_value_tmp.group(1)
                                if (unit_value_tmp := re.search(r'"(.*?)"', line))
                                else None
                            )
                        elif line.startswith("EINHEIT_X"):
                            unit_breakpoints_1 = (
                                unit_breakpoints_1_tmp.group(1)
                                if (
                                    unit_breakpoints_1_tmp := re.search(
                                        r'"(.*?)"', line
                                    )
                                )
                                else None
                            )
                        elif line.startswith("EINHEIT_Y"):
                            unit_breakpoints_2 = (
                                unit_breakpoints_2_tmp.group(1)
                                if (
                                    unit_breakpoints_2_tmp := re.search(
                                        r'"(.*?)"', line
                                    )
                                )
                                else None
                            )
                        elif line.startswith("SSTX"):
                            name_breakpoints_1 = (
                                line.split()[1] if len(line.split()) > 1 else None
                            )
                        elif line.startswith("SSTY"):
                            name_breakpoints_2 = (
                                line.split()[1] if len(line.split()) > 1 else None
                            )
                        elif line.startswith("ST_TX/X") or line.startswith("ST/X"):
                            value_tmp = line.split()[1:]
                            value_tmp = [float(x) for x in value_tmp]
                            breakpoints_1.extend(value_tmp)
                        elif line.startswith("ST_TX/Y") or line.startswith("ST/Y"):
                            value_tmp = line.split()[1:]
                            value_tmp = [float(x) for x in value_tmp]
                            breakpoints_2.extend(value_tmp)
                        elif line.startswith("WERT"):
                            value_tmp = line.split()[1:]
                            value_tmp = [float(x) for x in value_tmp]
                            value.extend(value_tmp)
                        elif line.startswith("TEXT"):
                            value_tmp = line.split()[1:]
                            value_tmp = [x.replace('"', "") for x in value_tmp]
                            value.extend(value_tmp)

                    parameter[parameter_name]["description"] = description
                    parameter[parameter_name]["dcm_keyword"] = parameter_keyword
                    if parameter_keyword in ["FESTWERT"]:
                        parameter[parameter_name]["unit"] = unit_value
                        parameter[parameter_name]["value"] = value[0]
                        parameter[parameter_name]["type"] = "scalar"
                    elif parameter_keyword in ["TEXTSTRING"]:
                        parameter[parameter_name]["value"] = value[0]
                        parameter[parameter_name]["type"] = "scalar"
                    elif parameter_keyword in ["FESTWERTEBLOCK"]:
                        parameter[parameter_name]["unit"] = unit_value
                        dim_str = [x for x in dim_str if "@" not in x]
                        dim = [int(x) for x in dim_str]
                        if len(dim) <= 1:
                            parameter[parameter_name]["value"] = value
                            parameter[parameter_name]["type"] = "array1d"
                        else:
                            parameter[parameter_name]["value"] = [
                                value[i : i + dim[0]]
                                for i in range(0, len(value), dim[0])
                            ]
                            parameter[parameter_name]["type"] = "array2d"
                    elif parameter_keyword in ["FESTKENNLINIE", "KENNLINIE"]:
                        parameter[parameter_name]["unit"] = unit_value
                        name_breakpoints_1 = f"{parameter_name}_static_breakpoints_1"
                        parameter[parameter_name]["name_breakpoints_1"] = (
                            name_breakpoints_1
                        )
                        parameter[parameter_name]["value"] = value
                        parameter[name_breakpoints_1] = {}
                        parameter[name_breakpoints_1]["value"] = breakpoints_1
                        parameter[name_breakpoints_1]["unit"] = unit_breakpoints_1
                        parameter[name_breakpoints_1]["description"] = (
                            f"breakpoints 1 to static axis {parameter_name}"
                        )
                        parameter[name_breakpoints_1]["type"] = "array1d"
                        parameter[name_breakpoints_1]["dcm_keyword"] = (
                            "STUETZSTELLENVERTEILUNG"
                        )
                        parameter[parameter_name]["type"] = "array1d"
                    elif parameter_keyword in ["FESTKENNFELD", "KENNFELD"]:
                        parameter[parameter_name]["unit"] = unit_value
                        name_breakpoints_1 = f"{parameter_name}_static_breakpoints_1"
                        name_breakpoints_2 = f"{parameter_name}_static_breakpoints_2"
                        parameter[parameter_name]["name_breakpoints_1"] = (
                            name_breakpoints_1
                        )
                        parameter[parameter_name]["name_breakpoints_2"] = (
                            name_breakpoints_2
                        )
                        parameter[parameter_name]["value"] = [
                            value[i : i + len(breakpoints_1)]
                            for i in range(0, len(value), len(breakpoints_1))
                        ]
                        parameter[name_breakpoints_1] = {}
                        parameter[name_breakpoints_1]["value"] = breakpoints_1
                        parameter[name_breakpoints_1]["unit"] = unit_breakpoints_1
                        parameter[name_breakpoints_1]["description"] = (
                            f"breakpoints 1 to static axis {parameter_name}"
                        )
                        parameter[name_breakpoints_1]["type"] = "array1d"
                        parameter[name_breakpoints_1]["dcm_keyword"] = (
                            "STUETZSTELLENVERTEILUNG"
                        )
                        parameter[name_breakpoints_2] = {}
                        parameter[name_breakpoints_2]["value"] = breakpoints_2
                        parameter[name_breakpoints_2]["unit"] = unit_breakpoints_2
                        parameter[name_breakpoints_2]["description"] = (
                            f"breakpoints 2 to static axis {parameter_name}"
                        )
                        parameter[name_breakpoints_2]["type"] = "array1d"
                        parameter[name_breakpoints_2]["dcm_keyword"] = (
                            "STUETZSTELLENVERTEILUNG"
                        )
                        parameter[parameter_name]["type"] = "array2d"
                    elif parameter_keyword in ["GRUPPENKENNLINIE"]:
                        parameter[parameter_name]["unit"] = unit_value
                        parameter[parameter_name]["name_breakpoints_1"] = (
                            name_breakpoints_1
                        )
                        parameter[parameter_name]["value"] = value
                        parameter[parameter_name]["type"] = "array1d"
                    elif parameter_keyword in ["GRUPPENKENNFELD"]:
                        parameter[parameter_name]["unit"] = unit_value
                        parameter[parameter_name]["name_breakpoints_1"] = (
                            name_breakpoints_1
                        )
                        parameter[parameter_name]["name_breakpoints_2"] = (
                            name_breakpoints_2
                        )
                        parameter[parameter_name]["value"] = [
                            value[i : i + len(breakpoints_1)]
                            for i in range(0, len(value), len(breakpoints_1))
                        ]
                        parameter[parameter_name]["type"] = "array2d"
                    elif parameter_keyword in ["STUETZSTELLENVERTEILUNG"]:
                        parameter[parameter_name]["unit"] = unit_breakpoints_1
                        parameter[parameter_name]["value"] = breakpoints_1
                        parameter[parameter_name]["type"] = "array1d"

            return ParameterModel.model_validate(parameter)

        except FileNotFoundError:
            error_msg = f"DCM file not found: '{file_path}'"
            logfile.write(error_msg, level="ERROR")
            return None
        except OSError as e:
            error_msg = f"Error reading DCM file '{file_path}': {e}"
            logfile.write(error_msg, level="ERROR")
            return None
        except ValidationError as e:
            error_msg = (
                f"Validation Error in DCM file '{file_path}': The file format does "
                f"not match the expected parameter model.\nDetails: {e}"
            )
            logfile.write(error_msg, level="ERROR")
            return None
        except Exception as e:
            # For all other unexpected errors
            error_msg = f"An unexpected error occurred while parsing the DCM file '{file_path}': {e}"
            logfile.write(error_msg, level="ERROR")
            return None

    @staticmethod
    @typechecked
    def write_out(
        parameter: ParameterModel,
        output_path: str,
        meta_data: Dict[str, str],
        logfile: Logfile,
    ):
        """Writes a ParameterModel object to a DCM file.

        The method formats the validated Pydantic object into a DCM-compliant
        string and saves it to the specified file path. It handles various
        DCM parameter types (e.g., FESTWERT, KENNFELD).

        DAMOS DCM format is defined on:
        https://www.etas.com/ww/en/downloads/?path=%252F&page=1&order=asc&layout=table&search=TechNote_DCM_File_Formats.pdf

        Args:
            parameter (ParameterModel): The validated Pydantic object containing
                the simulation parameters.
            output_path (str): The full path to the output DCM file.
            meta_data (dict): A dictionary containing metadata such as the ARES
                version and the current username.
            logfile (Logfile): The logfile object for writing messages.
        """
        try:
            encoding_type = "utf-8"
            time_stamp = datetime.now()
            metadata_str = [
                f'* encoding="{encoding_type}"',
                "* DAMOS-Austauschdatei",
                f"* Erstellt mit ARES {meta_data['version']}",
                f"* Erstellt von: {meta_data['username']}",
                f"* Erstellt am: {time_stamp.strftime('%d.%m.%Y %H:%M:%S')}",
                "\n",
            ]
            metadata_str = "\n".join(metadata_str)

            with open(output_path, "w", encoding=encoding_type) as file:
                file.write(metadata_str)

                for parameter_name, parameter_value in parameter.items():
                    parameter_keyword = ParamDCMinterface._eval_dcm_keyword(
                        parameter_name=parameter_name,
                        parameter_value=parameter_value,
                        logfile=logfile,
                    )

                    param_str = []
                    dim_str = None
                    unit_str: List[str] = []
                    axisname_str: List[str] = []
                    value_str: List[str] = []

                    match parameter_keyword:
                        case "FESTWERT":
                            unit_str.append(f'\tEINHEIT_W "{parameter_value.unit}"')
                            value_str.append(f"\tWERT\t{str(parameter_value.value)}")
                        case "TEXTSTRING":
                            value_str.append(f'\tTEXT\t"{parameter_value.value}"')
                        case "FESTWERTEBLOCK":
                            if len(parameter_value.value) > 0 and not isinstance(
                                parameter_value.value[0], list
                            ):
                                dim_str = f"{len(parameter_value.value)}"
                                unit_str.append(f'\tEINHEIT_W "{parameter_value.unit}"')
                                value_str.extend(
                                    ParamDCMinterface._dcm_array1d_str(
                                        "WERT", parameter_value.value
                                    )
                                )
                            else:
                                dim_str = f"{len(parameter_value.value[0])} @ {len(parameter_value.value)}"
                                unit_str.append(f'\tEINHEIT_W "{parameter_value.unit}"')
                                value_block = ParamDCMinterface._dcm_array2d_str(
                                    "WERT", parameter_value.value
                                )
                                for block in value_block:
                                    value_str.extend(block)
                        case "FESTKENNLINIE" | "KENNLINIE":
                            dim_str = f"{len(parameter_value.value)}"
                            breakpoints_1 = parameter[
                                parameter_value.name_breakpoints_1
                            ]
                            unit_str.append(f'\tEINHEIT_X "{breakpoints_1.unit}"')
                            unit_str.append(f'\tEINHEIT_W "{parameter_value.unit}"')
                            value_str.extend(
                                ParamDCMinterface._dcm_array1d_str(
                                    "ST/X", breakpoints_1.value
                                )
                            )
                            value_str.extend(
                                ParamDCMinterface._dcm_array1d_str(
                                    "WERT", parameter_value.value
                                )
                            )
                        case "FESTKENNFELD" | "KENNFELD":
                            dim_str = f"{len(parameter_value.value[0])} {len(parameter_value.value)}"
                            breakpoints_1 = parameter[
                                parameter_value.name_breakpoints_1
                            ]
                            unit_str.append(f'\tEINHEIT_X "{breakpoints_1.unit}"')
                            breakpoints_2 = parameter[
                                parameter_value.name_breakpoints_2
                            ]
                            unit_str.append(f'\tEINHEIT_Y "{breakpoints_2.unit}"')
                            unit_str.append(f'\tEINHEIT_W "{parameter_value.unit}"')
                            value_str.extend(
                                ParamDCMinterface._dcm_array1d_str(
                                    "ST/X", breakpoints_1.value
                                )
                            )
                            temp_values = ParamDCMinterface._dcm_array2d_str(
                                "WERT", parameter_value.value
                            )
                            for temp_value in temp_values:
                                value_str.extend(temp_value)
                        case "GRUPPENKENNLINIE":
                            dim_str = f"{len(parameter_value.value)}"
                            breakpoints_1 = parameter[
                                parameter_value.name_breakpoints_1
                            ]
                            unit_str.append(f'\tEINHEIT_X "{breakpoints_1.unit}"')
                            unit_str.append(f'\tEINHEIT_W "{parameter_value.unit}"')
                            axisname_str.append(
                                f"* SSTX {parameter_value.name_breakpoints_1}"
                            )
                            value_str.extend(
                                ParamDCMinterface._dcm_array1d_str(
                                    "ST/X", breakpoints_1.value
                                )
                            )
                            value_str.extend(
                                ParamDCMinterface._dcm_array1d_str(
                                    "WERT", parameter_value.value
                                )
                            )
                        case "GRUPPENKENNFELD":
                            dim_str = f"{len(parameter_value.value[0])} {len(parameter_value.value)}"
                            breakpoints_1 = parameter[
                                parameter_value.name_breakpoints_1
                            ]
                            unit_str.append(f'\tEINHEIT_X "{breakpoints_1.unit}"')
                            breakpoints_2 = parameter[
                                parameter_value.name_breakpoints_2
                            ]
                            unit_str.append(f'\tEINHEIT_Y "{breakpoints_2.unit}"')
                            unit_str.append(f'\tEINHEIT_W "{parameter_value.unit}"')
                            axisname_str.append(
                                f"* SSTX {parameter_value.name_breakpoints_1}"
                            )
                            axisname_str.append(
                                f"* SSTY {parameter_value.name_breakpoints_2}"
                            )
                            value_str.extend(
                                ParamDCMinterface._dcm_array1d_str(
                                    "ST/X", breakpoints_1.value
                                )
                            )
                            tmp_values = ParamDCMinterface._dcm_array2d_str(
                                "WERT", parameter_value.value
                            )
                            for tmp_brkpt, tmp_value in zip(
                                breakpoints_2.value, tmp_values
                            ):
                                value_str.append(f"\tST/Y\t{str(tmp_brkpt)}")
                                value_str.extend(tmp_value)
                        case "STUETZSTELLENVERTEILUNG":
                            if parameter_name.endswith(
                                ("_static_breakpoints_1", "_static_breakpoints_2")
                            ):
                                # this parameters are static and not only defined via dcm inport
                                # see definition of "FESTKENNLINIE", "KENNLINIE", "FESTKENNFELD", "KENNFELD"
                                continue
                            dim_str = f"{len(parameter_value.value)}"
                            unit_str.append(f'\tEINHEIT_X "{parameter_value.unit}"')
                            value_str.extend(
                                ParamDCMinterface._dcm_array1d_str(
                                    "ST/X", parameter_value.value
                                )
                            )
                        case _:
                            pass

                    param_str.extend(
                        [
                            f"{parameter_keyword} {parameter_name} {dim_str}",
                            f'\tLANGNAME "{parameter_value.description}"',
                        ]
                    )
                    param_str.extend(unit_str)
                    param_str.extend(axisname_str)
                    param_str.extend(value_str)
                    param_str.append("")
                    param_str = "\n".join(param_str)

                    file.write(param_str)
                    file.write("END\n\n")

        except OSError as e:
            error_msg = (
                f"Error writing DCM file '{output_path}': Missing write permissions or "
                f"an invalid path.\nDetails: {e}"
            )
            logfile.write(error_msg, level="ERROR")
        except KeyError as e:
            error_msg = (
                f"Metadata error: The expected key {e} is missing. Please ensure "
                f"'version' and 'username' are included in `meta_data`."
            )
            logfile.write(error_msg, level="ERROR")
        except Exception as e:
            error_msg = f"An unexpected error occurred while writing the DCM file '{output_path}': {e}"
            logfile.write(error_msg, level="ERROR")

    @staticmethod
    @typechecked
    def _dcm_array1d_str(title: str, input_array: List[Union[int, float]]) -> List[str]:
        """Formats a one-dimensional array into DCM string lines.

        Args:
            title (str): The DCM keyword or title for the data lines (e.g., 'WERT', 'ST/X').
            input_array (List[Union[int, float]]): A one-dimensional list of numerical values.

        Returns:
            List[str]: A list of formatted string lines for the DCM file.
        """
        output_array = [
            [str(n) for n in input_array[i : i + ParamDCMinterface.DCMValueLength]]
            for i in range(0, len(input_array), ParamDCMinterface.DCMValueLength)
        ]
        output_array = [[f"\t{title}"] + sublist for sublist in output_array]
        output_array = ["\t" + " ".join(sublist) for sublist in output_array]

        return output_array

    @staticmethod
    @typechecked
    def _dcm_array2d_str(
        title: str, input_array: List[List[Union[int, float]]]
    ) -> List[List[str]]:
        """Formats a two-dimensional array into a list of formatted string blocks.

        This method iterates over each inner list of a 2D array and uses the
        `_dcm_array1d_str` helper to format it into DCM-compliant string lines.

        Args:
            title (str): The DCM keyword or title for the data lines (e.g., 'WERT').
            input_array (List[List[Union[int, float]]]): A two-dimensional list of
                numerical values to be formatted.

        Returns:
            List[List[str]]: A list of lists, where each inner list contains the
                formatted string lines for one row of the input array.
        """
        output_array = []
        for sublist in input_array:
            formatted_lines = ParamDCMinterface._dcm_array1d_str(title, sublist)
            output_array.append(formatted_lines)

        return output_array

    @staticmethod
    @typechecked
    def _eval_dcm_keyword(
        parameter_name: str, parameter_value: ParameterElement, logfile: Logfile
    ) -> Optional[str]:
        """Evaluates the DCM keyword from a ParameterElement object.

        Args:
            parameter_name (str): The name of the parameter.
            parameter_value (ParameterElement): The Pydantic object containing parameter
                metadata.
            logfile (Logfile): The logfile object for writing messages.

        Returns:
            str or None: The DCM keyword if found, otherwise None.
        """
        try:
            keyword = parameter_value.dcm_keyword
            return keyword

        except Exception as e:
            logfile.write(
                f"Failed to evaluate DCM keyword of parameter {parameter_name}: {e}",
                level="ERROR",
            )
            return None
