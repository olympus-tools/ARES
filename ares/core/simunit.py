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

import ctypes
import json
from typing import Any, ClassVar, Dict, List, Optional

import numpy as np
from pydantic import ValidationError
from typeguard import typechecked

from ares.models.datadictionary_model import DataDictionaryModel
from ares.utils.logger import create_logger

# initialize logger
logger = create_logger("simunit")


class SimUnit:
    DATATYPES: ClassVar[Dict[str, List[Any]]] = {
        "int": [ctypes.c_int, np.int8],
        "float": [ctypes.c_float, np.float32],
        "double": [ctypes.c_double, np.float64],
        "bool": [ctypes.c_bool, np.bool_],
        "short": [ctypes.c_short, np.int16],
        "long": [ctypes.c_long, np.int32],
        "longlong": [ctypes.c_longlong, np.int64],
        "uint": [ctypes.c_uint, np.uint8],
        "ulong": [ctypes.c_ulong, np.uint32],
        "ulonglong": [ctypes.c_ulonglong, np.uint64],
    }

    @typechecked
    def __init__(
        self,
        file_path: Optional[str] = None,
        dd_path: Optional[str] = None,
    ):
        """Initializes the simulation unit by loading a shared library and a Data Dictionary.

        This constructor performs all necessary setup steps: loading the DD, validating it,
        loading the C shared library, mapping the C global variables to ctypes,
        and setting up the main simulation function.

        Args:
            file_path (str, optional): The path to the shared library file (e.g., .so, .dll, .dylib).
            dd_path (str, optional): The path to the Data Dictionary JSON file.
        """
        self._dd: Optional[DataDictionaryModel] = self._load_and_validate_dd(
            dd_path=dd_path
        )
        self._library: Optional[ctypes.CDLL] = self._load_library(file_path=file_path)
        self._dll_interface: Optional[Dict[str, Any]] = self._setup_c_interface()
        self._sim_function: Optional[ctypes.CFUNCTYPE] = self._setup_sim_function()

    @typechecked
    def _load_and_validate_dd(
        self, dd_path: Optional[str]
    ) -> Optional[DataDictionaryModel]:
        """Loads the Data Dictionary from a JSON file and validates its structure using Pydantic.

        If the file cannot be found or parsed, or if validation fails, an error is
        logged and `None` is returned.

        Args:
            dd_path (str, optional): The path to the Data Dictionary JSON file.

        Returns:
            Optional[DataDictionaryModel]: The loaded and validated Data Dictionary as a Pydantic
                object, or `None` if an error occurs.
        """
        try:
            with open(dd_path, "r", encoding="utf-8") as file:
                dd_data = json.load(file)

            dd = DataDictionaryModel.model_validate(dd_data)
            logger.info(
                f"Data dictionary '{dd_path}' successfully loaded and validated with Pydantic.",
            )
            return dd
        except FileNotFoundError:
            logger.error(
                f"Data dictionary file not found at '{dd_path}'.",
            )
            return None
        except json.JSONDecodeError as e:
            logger.error(
                f"Error parsing data dictionary JSON file '{dd_path}': {e}",
            )
            return None
        except ValidationError as e:
            logger.error(
                f"Validation error for data dictionary '{dd_path}': {e}",
            )
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error loading data dictionary file '{dd_path}': {e}",
            )
            return None

    @typechecked
    def _load_library(self, file_path: Optional[str]) -> Optional[ctypes.CDLL]:
        """Loads a shared library file using `ctypes`.

        This makes the symbols (variables and functions) from the C library accessible in Python.

        Args:
            file_path (str, optional): The path to the shared library file.

        Returns:
            Optional[ctypes.CDLL]: The loaded `ctypes.CDLL` object, or `None` if the library cannot be loaded.
        """
        try:
            library = ctypes.CDLL(file_path)
            logger.info(
                f"Library '{file_path}' successfully loaded.",
            )
            return library
        except OSError as e:
            logger.error(
                f"Error loading shared library '{file_path}': {e}",
            )
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error loading library '{file_path}': {e}",
            )
            return None

    @typechecked
    def _setup_c_interface(self) -> Optional[Dict[str, Any]]:
        """Maps global variables defined in the Data Dictionary to their corresponding ctypes objects.

        This process involves translating the datatype and size information from the DD into
        `ctypes` types and mapping them to the DLL's global variables.

        Returns:
            Optional[Dict[str, Any]]: A dictionary where keys are the variable names from the DD and values
                are the `ctypes` objects mapped to the DLL's global variables. Returns `None`
                if an error occurs during mapping (e.g., symbol not found).
        """
        dll_interface: Dict[str, Any] = {}
        for dd_element_name, dd_element_value in self._dd.items():
            try:
                datatype = dd_element_value.datatype
                size = dd_element_value.size
                base_ctypes_type = SimUnit.DATATYPES[datatype][0]

                if base_ctypes_type is None:
                    logger.error(
                        f"Invalid datatype '{datatype}' in variable '{dd_element_name}'.",
                    )
                    continue

                if len(size) == 1:
                    if size[0] == 1:
                        ctypes_type = base_ctypes_type
                    elif size[0] > 1:
                        ctypes_type = base_ctypes_type * size[0]
                    else:
                        logger.error(
                            f"Invalid size '{size[0]}' for '{dd_element_name}'. Expected > 0.",
                        )
                        continue
                elif len(size) == 2:
                    ctypes_type = (base_ctypes_type * size[1]) * size[0]
                else:
                    logger.error(
                        f"Invalid size '{size}' for '{dd_element_name}'. Expected 1 or 2 dimensions.",
                    )
                    continue

                dll_interface[dd_element_name] = ctypes_type.in_dll(
                    self._library, dd_element_name
                )
                logger.info(
                    f"Global simulation variable '{dd_element_name}' defined with datatype '{datatype}' and size '{size}'.",
                )
            except AttributeError as e:
                logger.error(
                    f"Failed to map global simulation variable '{dd_element_name}': Symbol not found or type mismatch. {e}",
                )
                continue
            except Exception as e:
                logger.error(
                    f"An unexpected error occurred while mapping global simulation variable '{dd_element_name}': {e}",
                )
                continue

        if not dll_interface:
            logger.error(
                "No variables could be mapped successfully.",
            )
            return None
        return dll_interface

    @typechecked
    def _setup_sim_function(self) -> Optional[ctypes.CFUNCTYPE]:
        """Configures the main simulation function (`ares_simunit`) from the shared library.

        It sets the argument types (`argtypes`) and return type (`restype`) to ensure
        correct function calls via `ctypes`.

        Returns:
            Optional[ctypes.CFUNCTYPE]: The `ctypes` function object for `ares_simunit`, or `None` if the
                function cannot be found in the library.
        """
        try:
            sim_function = self._library.ares_simunit
            sim_function.argtypes = []
            sim_function.restype = None
            logger.info(
                "Ares simulation function 'ares_simunit' successfully set up.",
            )
            return sim_function
        except AttributeError as e:
            logger.error(
                f"Ares simulation function 'ares_simunit' not found in library: {e}",
            )
            return None
        except Exception as e:
            logger.error(
                f"An unexpected error occurred while setting up ares simulation function: {e}",
            )
            return None

    @typechecked
    def run_simulation(
        self, data: Dict[str, Any], parameter: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Executes the main simulation function over multiple time steps.

        It processes input data, writes it to the C interface, calls the simulation
        function for each time step, and reads the output back into a dictionary.

        Args:
            data (dict): A dictionary containing all input signals, including a 'timestamp' array.
                Example: `{"timestamp": [t0, t1], "signal_A": [v0, v1]}`.
            parameter (dict): A dictionary containing simulation parameters.

        Returns:
            Optional[Dict[str, Any]]: A dictionary of NumPy arrays containing the output signals for all
                time steps, or `None` if an error occurs during the simulation.
        """

        try:
            logger.info("Starting ares simulation...")

            sim_result: Dict[str, np.ndarray] = {}
            time_steps = len(data["timestamp"])
            logger.info(
                f"The simulation starts at timestamp {data['timestamp'][0]} seconds "
                f"and ends at timestamp {data['timestamp'][-1]} seconds - duration: "
                f"{data['timestamp'][-1] - data['timestamp'][0]} seconds",
            )

            mapped_input = self._map_sim_input(input_data=data, time_steps=time_steps)

            for time_step_idx in range(time_steps):
                self._write_dll_interface(
                    input=mapped_input, time_step_idx=time_step_idx
                )
                self._sim_function()
                step_result = self._read_dll_interface()
                if step_result is None:
                    logger.error(
                        "Aborting simulation due to a critical error while reading output data.",
                    )
                    return None

                step_result["timestamp"] = data["timestamp"][time_step_idx].item()

                for output_signal in step_result.keys():
                    if output_signal not in sim_result:
                        if output_signal != "timestamp":
                            dd_element_value = self._dd[output_signal]
                            np_dtype = SimUnit.DATATYPES[dd_element_value.datatype][1]
                            sim_result[output_signal] = np.empty(0, dtype=np_dtype)
                        else:
                            np_dtype = SimUnit.DATATYPES["float"][1]
                        sim_result[output_signal] = np.empty(0, dtype=np_dtype)

                    sim_result[output_signal] = np.append(
                        sim_result[output_signal], step_result[output_signal]
                    )

            logger.info("ares simulation successfully finished.")
            return sim_result
        except Exception as e:
            logger.error(f"Error while running ares simulation: {e}")
            return None

    @typechecked
    def _map_sim_input(
        self, input_data: Dict[str, Any], time_steps: int
    ) -> Optional[Dict[str, Any]]:
        """Maps the provided input data to the expected simulation variables from the DD.

        This method handles missing signals by checking for alternative names or assigning
        a default static value of 0.

        Args:
            input_data (dict): The input data dictionary (e.g., from a data source).
            time_steps (int): The total number of simulation steps.

        Returns:
            Optional[Dict[str, Any]]: A dictionary of mapped input values, or `None` if a mapping error occurs.
        """
        if self._dd is None:
            return None
        try:
            mapped_input: Dict[str, Any] = {}
            for dd_element_name, dd_element_value in self._dd.items():
                if dd_element_value.type not in ["in", "inout"]:
                    continue

                if dd_element_name in input_data:
                    mapped_input[dd_element_name] = input_data[dd_element_name]
                    logger.info(
                        f"Simulation signal '{dd_element_name}' could be mapped to the original signal.",
                    )
                    continue

                mapped = False
                if (
                    hasattr(dd_element_value, "input_alternatives")
                    and dd_element_value.input_alternatives
                ):
                    for alternative_value in dd_element_value.input_alternatives:
                        if isinstance(alternative_value, str):
                            if alternative_value in input_data:
                                mapped_input[dd_element_name] = input_data[
                                    alternative_value
                                ]
                                logger.info(
                                    f"Simulation signal '{dd_element_name}' has been mapped to alternative '{alternative_value}'.",
                                )
                                mapped = True
                                break
                        else:
                            mapped_input[dd_element_name] = self._map_sim_input_static(
                                time_steps=time_steps,
                                datatype=dd_element_value.datatype,
                                size=dd_element_value.size,
                                value=alternative_value,
                            )
                            logger.info(
                                f"Simulation signal '{dd_element_name}' has been mapped to constant value {alternative_value}.",
                            )
                            mapped = True
                            break

                if not mapped:
                    # Fallback to default value 0
                    value = 0
                    mapped_input[dd_element_name] = self._map_sim_input_static(
                        time_steps=time_steps,
                        datatype=dd_element_value.datatype,
                        size=dd_element_value.size,
                        value=value,
                    )
                    logger.info(
                        f"Simulation signal '{dd_element_name}' has been mapped to default constant value {value}.",
                    )

            logger.info("Mapping is successfully finished.")
            return mapped_input
        except Exception as e:
            logger.error(
                f"Error during mapping of simulation input signals: {e}",
            )
            return None

    @typechecked
    def _map_sim_input_static(
        self, time_steps: int, datatype: str, size: List[int], value: Any
    ) -> Optional[np.ndarray]:
        """Creates a NumPy array of a specified size and datatype, filled with a constant value.

        This is used to handle simulation variables that have a static value instead of a signal.
        The function supports scalar, 1D, and 2D arrays as static values.

        Args:
            time_steps (int): The total number of simulation steps.
            datatype (str): The target datatype for the NumPy array (e.g., 'float', 'int').
            size (list[int]): The size of the simulation variable (e.g., `[1]` for a scalar, `[10]` for an array).
            value (any): The constant value to assign to the variable.

        Returns:
            Optional[np.ndarray]: A NumPy array containing the constant value for all time steps, or `None`
                if an error occurs.
        """
        try:
            np_dtype = self.DATATYPES[datatype][1]
            if len(size) == 1:
                if size[0] == 1:
                    return np.full((time_steps, 1), value, dtype=np_dtype)
                else:
                    out = np.empty((time_steps, size[0]), dtype=np_dtype)
                    if isinstance(value, list) or isinstance(value, np.ndarray):
                        if np.array(value).shape != (size[0],):
                            raise ValueError(
                                f"Shape of static 1D array value {np.array(value).shape} does not match DD size {size}."
                            )
                        for time_step_idx in range(time_steps):
                            out[time_step_idx] = value
                    else:
                        out[:] = value
                    return out
            elif len(size) == 2:
                out = np.empty((time_steps, size[0], size[1]), dtype=np_dtype)
                if isinstance(value, list) or isinstance(value, np.ndarray):
                    if np.array(value).shape != (size[0], size[1]):
                        raise ValueError(
                            f"Shape of static 2D array value {np.array(value).shape} does not match DD size {size}."
                        )
                    for time_step_idx in range(time_steps):
                        out[time_step_idx] = value
                else:
                    out[:] = value
                return out
            else:
                logger.error(
                    f"Unsupported size '{size}'. Expected 1 or 2 dimensions.",
                )
                return None
        except Exception as e:
            logger.error(
                f"Error during mapping static value {value}: {e}",
            )
            return None

    @typechecked
    def _write_dll_interface(self, input: Dict[str, Any], time_step_idx: int):
        """Writes the input data for a single time step from a Python dictionary to the
        global C variables in the shared library.

        It only writes to variables marked as `'in'` or `'inout'` in the Data Dictionary.

        Args:
            input (dict): A dictionary with variable names and their values for the current time step.
            time_step_idx (int): The index of the current time step.
        """
        for dd_element_name, dd_element_value in self._dd.items():
            try:
                if dd_element_value.type not in ["in", "inout"]:
                    continue

                sim_var = self._dll_interface[dd_element_name]
                size = dd_element_value.size

                if len(size) == 1:
                    if size[0] == 1:
                        sim_var.value = input[dd_element_name][time_step_idx]
                    else:
                        for i in range(size[0]):
                            sim_var[i] = input[dd_element_name][time_step_idx][i]
                elif len(size) == 2:
                    for i in range(size[0]):
                        for j in range(size[1]):
                            sim_var[i][j] = input[dd_element_name][time_step_idx][i][j]
                else:
                    logger.error(
                        f"Unsupported size '{size}' for '{dd_element_name}'. Cannot write values.",
                    )
            except Exception as e:
                logger.error(
                    f"Error writing input value '{dd_element_name}' to 'ares_simunit' function: {e}",
                )

    @typechecked
    def _read_dll_interface(self) -> Optional[Dict[str, Any]]:
        """Reads the current values of the global C variables from the shared library.

        It only reads from variables marked as `'out'` or `'inout'` in the Data Dictionary.

        Returns:
            Optional[Dict[str, Any]]: A dictionary where keys are the variable names and values are their current
                values read from the C library for the current time step. Returns `None` if an error occurs.
        """
        current_values: Dict[str, Any] = {}
        for dd_element_name, dd_element_value in self._dd.items():
            try:
                if dd_element_value.type not in ["out", "inout"]:
                    continue

                sim_var = self._dll_interface[dd_element_name]
                size = dd_element_value.size

                if len(size) == 1:
                    if size[0] == 1:
                        current_values[dd_element_name] = sim_var.value
                    else:
                        current_values[dd_element_name] = [
                            sim_var[i] for i in range(size[0])
                        ]
                elif len(size) == 2:
                    current_values[dd_element_name] = [
                        [sim_var[i][j] for j in range(size[1])] for i in range(size[0])
                    ]
                else:
                    logger.error(
                        f"Unsupported size '{size}' for '{dd_element_name}'. Cannot read values.",
                    )
            except Exception as e:
                logger.error(
                    f"Error reading output value '{dd_element_name}' from 'ares_simunit' function: {e}",
                )

        if not current_values:
            logger.error(
                "No variables could be read successfully.",
            )
            return None
        return current_values
