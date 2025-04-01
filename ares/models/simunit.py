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

from .logfile import Logfile
import os
import json
from jsonschema import validate, ValidationError
import ctypes
import numpy as np
from typing import Union
from typeguard import typechecked

class SimUnit:
    @typechecked
    def __init__(
        self, file_path: str = None, dd_path: str = None, logfile: Logfile = None
    ):
        """
        Initializes the simulation unit by loading a shared library and a Data Dictionary.

        This constructor performs all necessary setup steps: loading the DD, validating it,
        loading the C shared library, mapping the C global variables to ctypes,
        and setting up the main simulation function.

        Args:
            file_path (str): The path to the shared library file (e.g., .so, .dll, .dylib).
            dd_path (str): The path to the Data Dictionary JSON file.
            logfile (Logfile): The logfile object for logging.
        """
        self.logfile = logfile

        self.dd = self._load_dd(dd_path=dd_path)
        self.library = self._load_library(file_path=file_path)
        self.dll_interface = self._setup_c_interface()
        self.sim_function = self._setup_sim_function()

    @typechecked
    def _load_dd(self, dd_path: str) -> dict | None:
        """
        Loads the Data Dictionary from a JSON file and validates its structure.

        If the file cannot be found or parsed, or if validation fails, an error is
        logged and `None` is returned.

        Args:
            dd_path (str): The path to the Data Dictionary JSON file.

        Returns:
            dict | None: The loaded Data Dictionary as a dictionary, or `None` if an error occurs.
        """
        try:
            with open(dd_path, "r", encoding="utf-8") as file:
                dd = json.load(file)
            self._dd_validation(dd=dd, dd_path=dd_path)
            self.logfile.write(
                f"Data dictionary '{dd_path}' successfully loaded.", level="INFO"
            )
            return dd
        except FileNotFoundError:
            self.logfile.write(
                f"Data dictionary file not found at '{dd_path}'.", level="ERROR"
            )
            return None
        except json.JSONDecodeError as e:
            self.logfile.write(
                f"Error parsing data dictionary JSON file '{dd_path}': {e}",
                level="ERROR",
            )
            return None
        except Exception as e:
            self.logfile.write(
                f"Unexpected error loading data dictionary file '{dd_path}': {e}",
                level="ERROR",
            )
            return None

    @typechecked
    def _dd_validation(self, dd: dict, dd_path: str):
        """
        Validates the structure and content of the Data Dictionary JSON file against a
        predefined JSON schema.

        The function logs success or detailed error messages.

        Args:
            dd (dict): The Data Dictionary dictionary to be validated.
            dd_path (str): The file path of the Data Dictionary for logging purposes.
        """
        try:
            dd_schema_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "schemas", "data_dictionary.schema.json"
            )
            with open(dd_schema_path, "r", encoding="utf-8") as schema_file:
                schema = json.load(schema_file)

            validate(instance=dd, schema=schema)
            self.logfile.write(
                f"The JSON data in '{dd_path}' is valid according to schema '{dd_schema_path}'.",
                level="INFO",
            )
        except FileNotFoundError:
            log_message = f"Error: One of the files was not found. Please check the paths. Missing file: '{dd_path}' or '{dd_schema_path}'."
            self.logfile.write(log_message, level="ERROR")
        except json.JSONDecodeError as e:
            log_message = f"Error parsing the JSON file '{dd_path}': {e}"
            self.logfile.write(log_message, level="ERROR")
        except ValidationError as e:
            log_message = (
                f"Error while syntax validation of the workflow json file '{dd_path}': "
                f"Message: {e.message}. "
                f"Path: {' -> '.join(map(str, e.path))}. "
                f"Schema Path: {' -> '.join(map(str, e.schema_path))}. "
                f"Invalid Data: {json.dumps(e.instance, indent=2)}"
            )
            self.logfile.write(log_message, level="ERROR")
        except Exception as e:
            self.logfile.write(
                f"Unexpected error during data dictionary json file validation: {e}",
                level="ERROR",
            )

    @typechecked
    def _load_library(self, file_path: str) -> ctypes.CDLL | None:
        """
        Loads a shared library file using `ctypes`.

        This makes the symbols (variables and functions) from the C library accessible in Python.

        Args:
            file_path (str): The path to the shared library file.

        Returns:
            ctypes.CDLL | None: The loaded `ctypes.CDLL` object, or `None` if the library cannot be loaded.
        """
        try:
            library = ctypes.CDLL(file_path)
            self.logfile.write(
                f"Library '{file_path}' successfully loaded.", level="INFO"
            )
            return library
        except OSError as e:
            self.logfile.write(
                f"Error loading shared library '{file_path}': {e}", level="ERROR"
            )
            return None
        except Exception as e:
            self.logfile.write(
                f"Unexpected error loading library '{file_path}': {e}",
                level="ERROR",
            )
            return None

    @typechecked
    def _setup_c_interface(self) -> dict | None:
        """
        Maps global variables defined in the Data Dictionary to their corresponding ctypes objects.

        This process involves translating the datatype and size information from the DD into
        `ctypes` types and mapping them to the DLL's global variables.

        Returns:
            dict | None: A dictionary where keys are the variable names from the DD and values
                are the `ctypes` objects mapped to the DLL's global variables. Returns `None`
                if an error occurs during mapping (e.g., symbol not found).
        """
        c_types_map = {
            "int": ctypes.c_int,
            "float": ctypes.c_float,
            "double": ctypes.c_double,
            "char_p": ctypes.c_char_p,
            "void_p": ctypes.c_void_p,
            "bool": ctypes.c_bool,
            "short": ctypes.c_short,
            "long": ctypes.c_long,
            "longlong": ctypes.c_longlong,
            "ubyte": ctypes.c_ubyte,
            "ushort": ctypes.c_ushort,
            "uint": ctypes.c_uint,
            "ulong": ctypes.c_ulong,
            "ulonglong": ctypes.c_ulonglong,
        }

        dll_interface = {}

        for dd_element_name, dd_element_value in self.dd.items():
            try:
                datatype = dd_element_value["datatype"]
                size = dd_element_value["size"]
                base_ctypes_type = c_types_map.get(datatype)

                # Check if datatype exists
                if not base_ctypes_type:
                    self.logfile.write(
                        f"Invalid datatype '{datatype}' in variable '{dd_element_name}'.",
                        level="ERROR",
                    )
                    continue

                if len(size) == 1:
                    if size[0] == 1:  # Scalar or pointer to a single element
                        ctypes_type = base_ctypes_type
                    elif size[0] > 1:  # 1D array
                        ctypes_type = base_ctypes_type * size[0]
                    else:
                        self.logfile.write(
                            f"Invalid size '{size[0]}' for datatype '{datatype}' in variable '{dd_element_name}'. Expected > 0.",
                            level="ERROR",
                        )
                        continue
                elif len(size) == 2:  # 2D array
                    ctypes_type = (base_ctypes_type * size[1]) * size[0]
                else:
                    self.logfile.write(
                        f"Invalid size '{size}' for datatype '{datatype}' in variable '{dd_element_name}'. Expected 1 or 2 dimensions.",
                        level="ERROR",
                    )
                    continue

                dll_interface[dd_element_name] = ctypes_type.in_dll(
                    self.library, dd_element_name
                )

                self.logfile.write(
                    f"Global simulation variable '{dd_element_name}' defined with datatype '{dd_element_value['datatype']}' and size '{dd_element_value['size']}'.",
                    level="INFO",
                )
            except AttributeError as e:
                self.logfile.write(
                    f"Failed to map global simulation variable '{dd_element_name}': Symbol not found or type mismatch. {e}",
                    level="ERROR",
                )
                continue
            except Exception as e:
                self.logfile.write(
                    f"An unexpected error occurred while mapping global simulation variable '{dd_element_name}': {e}",
                    level="ERROR",
                )
                continue

        if not dll_interface:
            self.logfile.write(
                "No variables could be mapped successfully.", level="ERROR"
            )
            return None
        return dll_interface

    @typechecked
    def _setup_sim_function(self) -> Union[ctypes.CFUNCTYPE, None]:
        """
        Configures the main simulation function (`ares_simunit`) from the shared library.

        It sets the argument types (`argtypes`) and return type (`restype`) to ensure
        correct function calls via `ctypes`.

        Returns:
            ctypes.CFUNCTYPE | None: The `ctypes` function object for `ares_simunit`, or `None` if the
                function cannot be found in the library.
        """
        try:
            sim_function = self.library.ares_simunit
            sim_function.argtypes = []
            sim_function.restype = None
            self.logfile.write(
                f"Ares simulation function 'ares_simunit' successfully set up.",
                level="INFO",
            )
            return sim_function
        except AttributeError as e:
            sim_function = None
            self.logfile.write(
                f"Ares simulation function 'ares_simunit' not found in library: {e}",
                level="ERROR",
            )
            return None
        except Exception as e:
            sim_function = None
            self.logfile.write(
                f"An unexpected error occurred while setting up ares simulation function: {e}",
                level="ERROR",
            )
            return None

    @typechecked
    def run_simulation(self, data: dict, parameter: dict) -> dict | None:
        """
        Executes the main simulation function over multiple time steps.

        It processes input data, writes it to the C interface, calls the simulation
        function for each time step, and reads the output back into a dictionary.

        Args:
            data (dict): A dictionary containing all input signals, including a 'timestamp' array.
                Example: `{"timestamp": [t0, t1], "signal_A": [v0, v1]}`.
            parameter (dict): A dictionary containing simulation parameters.

        Returns:
            dict | None: A dictionary of NumPy arrays containing the output signals for all
                time steps, or `None` if an error occurs during the simulation.
        """
        self.logfile.write("Starting ares simulation...", level="INFO")

        try:
            sim_result = {}
            time_steps = len(data["timestamp"])
            self.logfile.write(
                f"The simulation starts at timestamp {data["timestamp"][0]} seconds and ends at timestamp {data["timestamp"][-1]} seconds - duration: {data["timestamp"][-1]-data["timestamp"][0]}seconds",
                level="INFO",
            )

            mapped_input = self._map_sim_input(input_data=data, time_steps=time_steps)

            for time_step_idx in range(time_steps):
                self._write_dll_interface(
                    input=mapped_input, time_step_idx=time_step_idx
                )
                self.sim_function()
                step_result = self._read_dll_interface()
                if step_result is None:
                    self.logfile.write(
                        "Aborting simulation due to a critical error while reading output data.",
                        level="ERROR",
                    )
                    return None
                step_result["timestamp"] = data["timestamp"][time_step_idx]

                for output_signal in step_result.keys():
                    if output_signal not in sim_result:
                        sim_result[output_signal] = np.array(
                            []
                        )  # TODO: set correct datatype to np.array
                    sim_result[output_signal] = np.append(
                        sim_result[output_signal], step_result[output_signal]
                    )

            self.logfile.write(f"ares simulation successfully finished.", level="INFO")
            return sim_result
        except Exception as e:
            self.logfile.write(
                f"Error while running ares simulation: {e}", level="ERROR"
            )
            return None

    @typechecked
    def _map_sim_input(self, input_data: dict, time_steps: int) -> dict | None:
        """
        Maps the provided input data to the expected simulation variables from the DD.

        This method handles missing signals by checking for alternative names or assigning
        a default static value of 0.

        Args:
            input_data (dict): The input data dictionary (e.g., from a data source).
            time_steps (int): The total number of simulation steps.

        Returns:
            dict | None: A dictionary of mapped input values, or `None` if a mapping error occurs.
        """
        try:
            mapped_input = {}
            for dll_interface_key in self.dll_interface.keys():
                if dll_interface_key in input_data:
                    mapped_input[dll_interface_key] = input_data[dll_interface_key]
                    self.logfile.write(
                        f"Simulation signal '{dll_interface_key}' could be mapped to the original signal.",
                        level="INFO",
                    )
                else:
                    size = self.dd[dll_interface_key]["size"]
                    if "input_alternatives" in self.dd[dll_interface_key]:
                        for alternative_value in self.dd[dll_interface_key][
                            "input_alternatives"
                        ]:
                            if isinstance(alternative_value, str):
                                if alternative_value in input_data:
                                    mapped_input[dll_interface_key] = input_data[
                                        alternative_value
                                    ]
                                    self.logfile.write(
                                        f"Simulation signal '{dll_interface_key}' has been mapped to alternative '{alternative_value}'.",
                                        level="INFO",
                                    )
                                    break
                            else:
                                mapped_input[dll_interface_key] = (
                                    self._map_sim_input_static(
                                        time_steps=time_steps,
                                        datatype=self.dd[dll_interface_key]["datatype"],
                                        size=size,
                                        value=alternative_value,
                                    )
                                )
                                self.logfile.write(
                                    f"Simulation signal '{dll_interface_key}' has been mapped to constant value {alternative_value}.",
                                    level="INFO",
                                )
                                break
                        if dll_interface_key not in mapped_input:
                            value = 0
                            mapped_input[dll_interface_key] = (
                                self._map_sim_input_static(
                                    time_steps=time_steps,
                                    datatype=self.dd[dll_interface_key]["datatype"],
                                    size=size,
                                    value=value,
                                )
                            )
                            self.logfile.write(
                                f"Simulation signal '{dll_interface_key}' has been mapped to constant value {value}.",
                                level="INFO",
                            )
                    else:
                        value = 0
                        mapped_input[dll_interface_key] = self._map_sim_input_static(
                            time_steps=time_steps,
                            datatype=self.dd[dll_interface_key]["datatype"],
                            size=size,
                            value=value,
                        )
                        self.logfile.write(
                            f"Simulation signal '{dll_interface_key}' has been mapped to constant value {value}.",
                            level="INFO",
                        )
            self.logfile.write("Mapping is successfully finished.", level="INFO")
            return mapped_input
        except Exception as e:
            self.logfile.write(
                f"Error during mapping of simulation input signals: {e}", level="ERROR"
            )
            return None

    @typechecked
    def _map_sim_input_static(
        self, time_steps: int, datatype: str, size: list, value
    ) -> np.ndarray | None:
        """
        Creates a NumPy array of a specified size and datatype, filled with a constant value.

        This is used to handle simulation variables that have a static value instead of a signal.

        Args:
            time_steps (int): The total number of simulation steps.
            datatype (str): The target datatype for the NumPy array (e.g., 'float', 'int').
            size (list): The size of the simulation variable (e.g., `[1]` for a scalar, `[10]` for an array).
            value: The constant value to assign to the variable.

        Returns:
            np.ndarray | None: A NumPy array containing the constant value for all time steps, or `None`
                if an error occurs.
        """
        try:
            if len(size) == 1:
                out = np.empty((time_steps, size[0]), dtype=datatype)
                for time_step_idx in range(time_steps):
                    out[time_step_idx] = value
                return out
            elif len(size) == 2:
                # TODO: Impelement vairant for 2D array
                self.logfile.write(
                    f"Static mapping for 2D array is not yet implemented. Skipping.",
                    level="WARNING",
                )
        except Exception as e:
            self.logfile.write(
                f"Error during mapping static value {value} : {e}", level="ERROR"
            )
            return None

    @typechecked
    def _write_dll_interface(self, input: dict, time_step_idx: int):
        """
        Writes the input data for a single time step from a Python dictionary to the
        global C variables in the shared library.

        It only writes to variables marked as `'in'` or `'inout'` in the Data Dictionary.

        Args:
            input (dict): A dictionary with variable names and their values for the current time step.
            time_step_idx (int): The index of the current time step.
        """
        for dll_interface_key in self.dll_interface.keys():
            try:
                sim_var = self.dll_interface[dll_interface_key]
                sim_var_info = self.dd.get(dll_interface_key)

                if sim_var_info and sim_var_info.get("type") not in ["in", "inout"]:
                    continue

                if isinstance(sim_var, ctypes._SimpleCData):
                    sim_var.value = input[dll_interface_key][time_step_idx]
                elif isinstance(sim_var, ctypes.Array):
                    if len(sim_var_info["size"]) == 1:
                        for i in range(sim_var_info["size"][0]):
                            sim_var[i] = input[dll_interface_key][time_step_idx][i]
                    elif len(sim_var_info["size"]) == 2:
                        # TODO: Impelement vairant for 2D array
                        self.logfile.write(
                            f"Writing to 2D array '{dll_interface_key}' is not yet implemented. Skipping.",
                            level="WARNING",
                        )
                        continue
                else:
                    self.logfile.write(
                        f"Unhandled ctypes type for '{dll_interface_key}': '{type(sim_var)}'. Cannot set values.",
                        level="ERROR",
                    )
            except Exception as e:
                self.logfile.write(
                    f"Error writing input value '{dll_interface_key}' of to 'ares_simunit' fucntion: {e}",
                    level="ERROR",
                )

    @typechecked
    def _read_dll_interface(self) -> dict | None:
        """
        Reads the current values of the global C variables from the shared library.

        It only reads from variables marked as `'out'` or `'inout'` in the Data Dictionary.

        Returns:
            dict | None: A dictionary where keys are the variable names and values are their current
                values read from the C library for the current time step. Returns `None` if an error occurs.
        """
        current_values = {}
        for dll_interface_key in self.dll_interface.keys():
            try:
                sim_var = self.dll_interface[dll_interface_key]
                sim_var_info = self.dd.get(dll_interface_key)

                if sim_var_info and sim_var_info.get("type") not in ["out", "inout"]:
                    continue

                if isinstance(sim_var, ctypes._SimpleCData):
                    current_values[dll_interface_key] = sim_var.value
                elif isinstance(sim_var, ctypes.Array):
                    if len(sim_var_info["size"]) == 1:
                        current_values[dll_interface_key] = [
                            sim_var[i] for i in range(sim_var_info["size"][0])
                        ]
                    elif len(sim_var_info["size"]) == 2:
                        # TODO: Impelement vairant for 2D array
                        self.logfile.write(
                            f"Reading 2D array '{dll_interface_key}' is not yet implemented. Skipping.",
                            level="WARNING",
                        )
                        continue
                else:
                    self.logfile.write(
                        f"Unhandled ctypes type for '{dll_interface_key}'. Cannot get value.",
                        level="ERROR",
                    )
            except Exception as e:
                self.logfile.write(
                    f"Error writing output value '{dll_interface_key}' of to 'ares_simunit' fucntion: {e}",
                    level="ERROR",
                )

        if not current_values:
            self.logfile.write(
                "No variables could be read successfully.", level="ERROR"
            )
            return None
        return current_values
