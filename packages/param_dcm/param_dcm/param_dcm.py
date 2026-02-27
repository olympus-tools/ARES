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

Copyright 2025 olympus-tools contributors. Dependencies and licenses
are listed in the NOTICE file:

    https://github.com/olympus-tools/ARES/blob/master/NOTICE

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License:

    https://github.com/olympus-tools/ARES/blob/master/LICENSE
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Any

from ares.utils.decorators import typechecked_dev as typechecked


class ParamDCM:
    """DCM Parameter file handler.

    This class loads and manages DCM parameter files, providing access to
    the parsed parameters through a dictionary.

    Usage:
        # Load from file
        param = ParamDCM(file_path="path/to/file.dcm")
        if param.parameter:
            # Access parameter
            value = param.parameter["parameter_name"]

        # Create empty
        param = ParamDCM()
        param.parameter["new_param"] = {...}
    """

    DCMValueLength = 6

    @typechecked
    def __init__(self, file_path: Path):
        """Initialize ParamDCM and optionally load a DCM file.

        DAMOS DCM format is defined on:
        https://www.etas.com/ww/en/downloads/?path=%252F&page=1&order=asc&layout=table&search=TechNote_DCM_File_Formats.pdf

        Args:
            file_path (Path): Path to the DCM file to load.
        """
        self.file_path: Path = file_path
        self.parameter: dict[str, Any] = self._load()

    @typechecked
    def _load(self) -> dict[str, Any]:
        """Parses a DCM file and converts it to a validated ParameterModel object.

        Returns:
            dict[str, Any]: Validated parameter dictionary. Returns empty dict on error.
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

            parameter: dict[str, Any] = {}

            with open(self.file_path, "r", encoding="utf-8") as dcm_file:
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
                    elif parameter_keyword in ["TEXTSTRING"]:
                        parameter[parameter_name]["value"] = value[0]
                    elif parameter_keyword in ["FESTWERTEBLOCK"]:
                        parameter[parameter_name]["unit"] = unit_value
                        dim_str = [x for x in dim_str if "@" not in x]
                        dim = [int(x) for x in dim_str]
                        if len(dim) <= 1:
                            parameter[parameter_name]["value"] = value
                        else:
                            parameter[parameter_name]["value"] = [
                                [value[i + j * dim[0]] for j in range(dim[1])]
                                for i in range(dim[0])
                            ]
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
                        parameter[name_breakpoints_1]["dcm_keyword"] = (
                            "STUETZSTELLENVERTEILUNG"
                        )
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
                            [
                                value[i + j * len(breakpoints_1)]
                                for j in range(len(breakpoints_2))
                            ]
                            for i in range(len(breakpoints_1))
                        ]
                        parameter[name_breakpoints_1] = {}
                        parameter[name_breakpoints_1]["value"] = breakpoints_1
                        parameter[name_breakpoints_1]["unit"] = unit_breakpoints_1
                        parameter[name_breakpoints_1]["description"] = (
                            f"breakpoints 1 to static axis {parameter_name}"
                        )
                        parameter[name_breakpoints_1]["dcm_keyword"] = (
                            "STUETZSTELLENVERTEILUNG"
                        )
                        parameter[name_breakpoints_2] = {}
                        parameter[name_breakpoints_2]["value"] = breakpoints_2
                        parameter[name_breakpoints_2]["unit"] = unit_breakpoints_2
                        parameter[name_breakpoints_2]["description"] = (
                            f"breakpoints 2 to static axis {parameter_name}"
                        )
                        parameter[name_breakpoints_2]["dcm_keyword"] = (
                            "STUETZSTELLENVERTEILUNG"
                        )
                    elif parameter_keyword in ["GRUPPENKENNLINIE"]:
                        parameter[parameter_name]["unit"] = unit_value
                        parameter[parameter_name]["name_breakpoints_1"] = (
                            name_breakpoints_1
                        )
                        parameter[parameter_name]["value"] = value
                    elif parameter_keyword in ["GRUPPENKENNFELD"]:
                        parameter[parameter_name]["unit"] = unit_value
                        parameter[parameter_name]["name_breakpoints_1"] = (
                            name_breakpoints_1
                        )
                        parameter[parameter_name]["name_breakpoints_2"] = (
                            name_breakpoints_2
                        )
                        parameter[parameter_name]["value"] = [
                            [
                                value[i + j * len(breakpoints_1)]
                                for j in range(len(breakpoints_2))
                            ]
                            for i in range(len(breakpoints_1))
                        ]
                    elif parameter_keyword in ["STUETZSTELLENVERTEILUNG"]:
                        parameter[parameter_name]["unit"] = unit_breakpoints_1
                        parameter[parameter_name]["value"] = breakpoints_1

            return parameter

        except FileNotFoundError:
            error_msg = f"DCM file not found: '{self.file_path}'"
            print(error_msg)
            return {}
        except OSError as e:
            error_msg = f"Error reading DCM file '{self.file_path}': {e}"
            print(error_msg)
            return {}
        except Exception as e:
            # For all other unexpected errors
            error_msg = f"An unexpected error occurred while parsing the DCM file '{self.file_path}': {e}"
            print(error_msg)
            return {}

    @typechecked
    def write(
        self,
        output_path: Path,
        meta_data: dict[str, str],
    ):
        """Writes the loaded parameter model to a DCM file.

        The method formats the validated Pydantic object into a DCM-compliant
        string and saves it to the specified file path. It handles various
        DCM parameter types (e.g., FESTWERT, KENNFELD).

        DAMOS DCM format is defined on:
        https://www.etas.com/ww/en/downloads/?path=%252F&page=1&order=asc&layout=table&search=TechNote_DCM_File_Formats.pdf

        Args:
            output_path (Path): The full path to the output DCM file.
            meta_data (dict[str, str]): A dictionary containing metadata such as the ARES
                version and the current username.
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

                for parameter_name, parameter_value in self.parameter.items():
                    parameter_keyword = ParamDCM._eval_dcm_keyword(
                        parameter_name=parameter_name,
                        parameter_value=parameter_value,
                    )

                    param_str = []
                    dim_str = None
                    unit_str: list[str] = []
                    axisname_str: list[str] = []
                    value_str: list[str] = []

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
                                    ParamDCM._dcm_array1d_str(
                                        "WERT", parameter_value.value
                                    )
                                )
                            else:
                                dim_str = f"{len(parameter_value.value[0])} @ {len(parameter_value.value)}"
                                unit_str.append(f'\tEINHEIT_W "{parameter_value.unit}"')
                                value_block = ParamDCM._dcm_array2d_str(
                                    "WERT", parameter_value.value
                                )
                                for block in value_block:
                                    value_str.extend(block)
                        case "FESTKENNLINIE" | "KENNLINIE":
                            dim_str = f"{len(parameter_value.value)}"
                            breakpoints_1 = self.parameter[
                                parameter_value.name_breakpoints_1
                            ]
                            unit_str.append(f'\tEINHEIT_X "{breakpoints_1.unit}"')
                            unit_str.append(f'\tEINHEIT_W "{parameter_value.unit}"')
                            value_str.extend(
                                ParamDCM._dcm_array1d_str("ST/X", breakpoints_1.value)
                            )
                            value_str.extend(
                                ParamDCM._dcm_array1d_str("WERT", parameter_value.value)
                            )
                        case "FESTKENNFELD" | "KENNFELD":
                            dim_str = f"{len(parameter_value.value[0])} {len(parameter_value.value)}"
                            breakpoints_1 = self.parameter[
                                parameter_value.name_breakpoints_1
                            ]
                            unit_str.append(f'\tEINHEIT_X "{breakpoints_1.unit}"')
                            breakpoints_2 = self.parameter[
                                parameter_value.name_breakpoints_2
                            ]
                            unit_str.append(f'\tEINHEIT_Y "{breakpoints_2.unit}"')
                            unit_str.append(f'\tEINHEIT_W "{parameter_value.unit}"')
                            value_str.extend(
                                ParamDCM._dcm_array1d_str("ST/X", breakpoints_1.value)
                            )
                            temp_values = ParamDCM._dcm_array2d_str(
                                "WERT", parameter_value.value
                            )
                            for temp_value in temp_values:
                                value_str.extend(temp_value)
                        case "GRUPPENKENNLINIE":
                            dim_str = f"{len(parameter_value.value)}"
                            breakpoints_1 = self.parameter[
                                parameter_value.name_breakpoints_1
                            ]
                            unit_str.append(f'\tEINHEIT_X "{breakpoints_1.unit}"')
                            unit_str.append(f'\tEINHEIT_W "{parameter_value.unit}"')
                            axisname_str.append(
                                f"* SSTX {parameter_value.name_breakpoints_1}"
                            )
                            value_str.extend(
                                ParamDCM._dcm_array1d_str("ST/X", breakpoints_1.value)
                            )
                            value_str.extend(
                                ParamDCM._dcm_array1d_str("WERT", parameter_value.value)
                            )
                        case "GRUPPENKENNFELD":
                            dim_str = f"{len(parameter_value.value[0])} {len(parameter_value.value)}"
                            breakpoints_1 = self.parameter[
                                parameter_value.name_breakpoints_1
                            ]
                            unit_str.append(f'\tEINHEIT_X "{breakpoints_1.unit}"')
                            breakpoints_2 = self.parameter[
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
                                ParamDCM._dcm_array1d_str("ST/X", breakpoints_1.value)
                            )
                            tmp_values = ParamDCM._dcm_array2d_str(
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
                                ParamDCM._dcm_array1d_str("ST/X", parameter_value.value)
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
            print(error_msg)
        except KeyError as e:
            error_msg = (
                f"Metadata error: The expected key {e} is missing. Please ensure "
                f"'version' and 'username' are included in `meta_data`."
            )
            print(error_msg)
        except Exception as e:
            error_msg = f"An unexpected error occurred while writing the DCM file '{output_path}': {e}"
            print(error_msg)

    @staticmethod
    @typechecked
    def _dcm_array1d_str(title: str, input_array: list[int | float]) -> list[str]:
        """Formats a one-dimensional array into DCM string lines.

        Args:
            title (str): The DCM keyword or title for the data lines (e.g., 'WERT', 'ST/X').
            input_array (list[int | float]): A one-dimensional list of numerical values.

        Returns:
            list[str]: A list of formatted string lines for the DCM file.
        """
        output_array = [
            [str(n) for n in input_array[i : i + ParamDCM.DCMValueLength]]
            for i in range(0, len(input_array), ParamDCM.DCMValueLength)
        ]
        output_array = [[f"\t{title}"] + sublist for sublist in output_array]
        output_array = ["\t" + " ".join(sublist) for sublist in output_array]

        return output_array

    @staticmethod
    @typechecked
    def _dcm_array2d_str(
        title: str, input_array: list[list[int | float]]
    ) -> list[list[str]]:
        """Formats a two-dimensional array into a list of formatted string blocks.

        This method iterates over each inner list of a 2D array and uses the
        `_dcm_array1d_str` helper to format it into DCM-compliant string lines.

        Args:
            title (str): The DCM keyword or title for the data lines (e.g., 'WERT').
            input_array (list[list[int | float]]): A two-dimensional list of
                numerical values to be formatted.

        Returns:
            list[list[str]]: A list of lists, where each inner list contains the
                formatted string lines for one row of the input array.
        """
        output_array = []
        for sublist in input_array:
            formatted_lines = ParamDCM._dcm_array1d_str(title, sublist)
            output_array.append(formatted_lines)

        return output_array

    @staticmethod
    @typechecked
    def _eval_dcm_keyword(
        parameter_name: str,
        parameter_value: Any,
    ) -> str | None:
        """Evaluates the DCM keyword from a ParameterElement object.

        Args:
            parameter_name (str): The name of the parameter.
            parameter_value (Any): The Pydantic object containing parameter
                metadata.

        Returns:
            str | None: The DCM keyword if found, otherwise None.
        """
        try:
            keyword = None

            if hasattr(parameter_value, "dcm_keyword"):
                keyword = parameter_value.dcm_keyword

            return keyword

        except Exception as e:
            print(
                f"Failed to evaluate DCM keyword of parameter {parameter_name}: {e}",
            )
            return None
