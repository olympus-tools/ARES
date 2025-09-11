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

logger = create_logger("simunit")


class SimUnit:
    DATATYPES: ClassVar[Dict[str, List[Any]]] = {
        "float": [ctypes.c_float, np.float32],
        "double": [ctypes.c_double, np.float64],
        "bool": [ctypes.c_bool, np.bool_],
        "int8": [ctypes.c_int8, np.int8],
        "int16": [ctypes.c_int16, np.int16],
        "int32": [ctypes.c_int32, np.int32],
        "int64": [ctypes.c_int64, np.int64],
        "uint8": [ctypes.c_uint8, np.uint8],
        "uint16": [ctypes.c_uint16, np.uint16],
        "uint32": [ctypes.c_uint32, np.uint32],
        "uint64": [ctypes.c_uint64, np.uint64],
    }

    @typechecked
    def __init__(
        self,
        type: str = "sim_unit",
        input: Optional[List[str]] = None,
        parameter: Optional[List[str]] = None,
        cancel_condition: Optional[str] = None,
        init: Optional[List[str]] = None,
        cycle_time: Optional[int] = None,
        element_workflow: Optional[List[str]] = None,
        file_path: Optional[str] = None,
        dd_path: Optional[str] = None,
    ):
        """
        Initializes the simulation unit and sets up all required simulation parameters.

        This constructor performs the following steps:
        - Loads and validates the Data Dictionary (DD) from a JSON file
        - Loads the C shared library (.so, .dll, .dylib)
        - Maps C global variables to ctypes objects
        - Sets up the main simulation function
        - Stores all configuration parameters as instance variables

        Args:
            type (str, optional): The type of the simulation unit. Default is "sim_unit".
            input (List[str], optional): List of input signal names.
            parameter (List[str], optional): List of parameter names.
            cancel_condition (str, optional): Condition to cancel the simulation.
            init (List[str], optional): List of initialization steps or signals.
            cycle_time (int, optional): Simulation cycle time in milliseconds.
            element_workflow (List[str], optional): Workflow elements for the simulation.
            file_path (str, optional): Path to the shared library file (e.g., .so, .dll, .dylib).
            dd_path (str, optional): Path to the Data Dictionary JSON file.
        """
        self.type: str = type
        self.input: Optional[List[str]] = input
        self.parameter: Optional[List[str]] = parameter
        self.cancel_condition: Optional[str] = cancel_condition
        self.init: Optional[List[str]] = init
        self.cycle_time: Optional[int] = cycle_time
        self.element_workflow: Optional[List[str]] = element_workflow
        self.file_path: Optional[str] = file_path
        self.dd_path: Optional[str] = dd_path

        self._dd: Optional[DataDictionaryModel] = self._load_and_validate_dd(
            dd_path=dd_path
        )
        self._library: Optional[ctypes.CDLL] = self._load_library()
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
    def _load_library(self) -> Optional[ctypes.CDLL]:
        """Loads a shared library file using `ctypes`.

        This makes the symbols (variables and functions) from the C library accessible in Python.

        Returns:
            Optional[ctypes.CDLL]: The loaded `ctypes.CDLL` object, or `None` if the library cannot be loaded.
        """
        try:
            library = ctypes.CDLL(self.file_path)

            # sumunit should be always a void void function
            library.argtypes = []
            library.restype = None

            logger.info(
                f"Library '{self.file_path}' successfully loaded.",
            )
            return library
        except OSError as e:
            logger.error(
                f"Error loading shared library '{self.file_path}': {e}",
            )
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error loading library '{self.file_path}': {e}",
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

                if len(size) == 0:
                    ctypes_type = base_ctypes_type
                elif len(size) == 1:
                    ctypes_type = base_ctypes_type * size[0]
                elif len(size) == 2:
                    ctypes_type = (base_ctypes_type * size[1]) * size[0]
                else:
                    logger.warning(
                        f"Invalid size '{size}' for '{dd_element_name}'. Expected 0 (scalar), 1 (1D), or 2 (2D) dimensions.",
                    )
                    continue

                dll_interface[dd_element_name] = ctypes_type.in_dll(
                    self._library, dd_element_name
                )
                logger.debug(
                    f"Global simulation variable '{dd_element_name}' defined with datatype '{datatype}' and size '{size}'.",
                )
            except AttributeError as e:
                logger.warning(
                    f"Failed to map global simulation variable '{dd_element_name}': Symbol not found or type mismatch. {e}",
                )
                continue
            except Exception as e:
                logger.warning(
                    f"An unexpected failure occurred while mapping global simulation variable '{dd_element_name}': {e}",
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
            logger.debug(
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
            data (dict): A dictionary containing all input signals, including a 'timestamps' array.
                Example: `{"timestamps": [t0, t1], "signal_A": [v0, v1]}`.
            parameter (dict): A dictionary containing simulation parameters.

        Returns:
            Optional[Dict[str, Any]]: A dictionary of NumPy arrays containing the output signals for all
                time steps, or `None` if an error occurs during the simulation.
        """

        try:
            logger.info("Starting ares simulation...")

            sim_result: Dict[str, np.ndarray] = {}
            time_steps = len(data["timestamps"])
            logger.info(
                f"The simulation starts at timestamps {data['timestamps'][0]} seconds "
                f"and ends at timestamps {data['timestamps'][-1]} seconds - duration: "
                f"{data['timestamps'][-1] - data['timestamps'][0]} seconds",
            )

            self._write_dll_interface(input=parameter)

            mapped_input = self._map_sim_input(input=data, time_steps=time_steps)

            output_signals = [
                k for k, v in self._dd.items() if v.type in ["out", "inout"]
            ]
            for signal in output_signals:
                size = self._dd[signal].size
                np_dtype = self.DATATYPES[self._dd[signal].datatype][1]
                if len(size) == 0:
                    sim_result[signal] = np.empty((time_steps,), dtype=np_dtype)
                elif len(size) == 1:
                    sim_result[signal] = np.empty((time_steps, size[0]), dtype=np_dtype)
                elif len(size) == 2:
                    sim_result[signal] = np.empty(
                        (time_steps, size[0], size[1]), dtype=np_dtype
                    )
            sim_result["timestamps"] = np.empty((time_steps,), dtype=np.float64)

            for time_step_idx in range(time_steps):
                self._write_dll_interface(
                    input=mapped_input, time_step_idx=time_step_idx
                )
                self._sim_function()
                step_result = self._read_dll_interface()
                for signal in output_signals:
                    sim_result[signal][time_step_idx] = step_result[signal]
                sim_result["timestamps"][time_step_idx] = data["timestamps"][
                    time_step_idx
                ]

            logger.info("ares simulation successfully finished.")
            return sim_result
        except Exception as e:
            logger.error(f"Error while running ares simulation: {e}")
            return None

    @typechecked
    def _map_sim_input(
        self, input: Dict[str, Any], time_steps: int = 1
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

        mapped_input: Dict[str, Any] = {}
        for dd_element_name, dd_element_value in self._dd.items():
            try:
                mapped = False

                if dd_element_value.type not in ["in", "inout", "parameter"]:
                    continue

                if dd_element_name in input:
                    mapped_input[dd_element_name] = input[dd_element_name]
                    logger.debug(
                        f"Simulation signal '{dd_element_name}' could be mapped to the original signal.",
                    )
                    continue

                if (
                    hasattr(dd_element_value, "input_alternatives")
                    and dd_element_value.input_alternatives
                ):
                    for alternative_value in dd_element_value.input_alternatives:
                        mapped = False

                        if isinstance(alternative_value, str):
                            if alternative_value in input:
                                mapped_input[dd_element_name] = input[alternative_value]
                                logger.debug(
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
                            logger.debug(
                                f"Simulation signal '{dd_element_name}' has been mapped to constant value {alternative_value}.",
                            )
                            mapped = True
                            break

                if not mapped:
                    logger.debug(
                        f"Simulation signal '{dd_element_name}' has been mapped to default constant value 0.",
                    )

            except Exception as e:
                logger.warning(
                    f"Error while mapping signal {dd_element_name}: {e}",
                )
                return None

        logger.debug("Mapping is successfully finished.")
        return mapped_input

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
            if len(size) == 0:
                return np.full((time_steps,), value, dtype=np_dtype)
            elif len(size) == 1:
                return np.tile(np.array(value, dtype=np_dtype), (time_steps, 1))
            elif len(size) == 2:
                return np.tile(np.array(value, dtype=np_dtype), (time_steps, 1, 1))
            else:
                logger.warning(
                    f"Invalid size '{size}'. Expected 0 (scalar), 1 (1D), or 2 (2D) dimensions.",
                )
                return None

        except Exception as e:
            logger.warning(
                f"Warnging during mapping static value {value}: {e}",
            )
            return None

    @typechecked
    def _write_dll_interface(self, input: Dict[str, Any], time_step_idx: int = 0):
        """Writes the input data for a single time step from a Python dictionary to the
        global C variables in the shared library.

        It only writes to variables marked as `'in'`, `'inout'` or `'parameter'` in the Data Dictionary.

        Args:
            input (dict): A dictionary with variable names and their values for the current time step.
            time_step_idx (int): The index of the current time step.
        """
        for dd_element_name, dd_element_value in self._dd.items():
            try:
                if dd_element_value.type not in ["in", "inout", "parameter"]:
                    continue

                elif dd_element_name in input:
                    input_value = input[dd_element_name][time_step_idx]
                    size = dd_element_value.size

                    if len(size) == 0:
                        self._dll_interface[dd_element_name].value = input_value.item()
                    elif len(size) == 1:
                        self._dll_interface[dd_element_name][:] = input_value.tolist()
                    elif len(size) == 2:
                        for i in range(size[0]):
                            self._dll_interface[dd_element_name][i][:] = input_value[
                                i
                            ].tolist()
                    else:
                        logger.warning(
                            f"Invalid size '{size}' for '{dd_element_name}'. Expected 0 (scalar), 1 (1D), or 2 (2D) dimensions.",
                        )
                        continue

            except Exception as e:
                logger.warning(
                    f"Warning writing input value '{dd_element_name}' to 'ares_simunit' function: {e}",
                )

    @typechecked
    def _read_dll_interface(self) -> Optional[Dict[str, Any]]:
        """Reads the current values of the global C variables from the shared library.

        It only reads from variables marked as `'out'` or `'inout'` in the Data Dictionary.

        Returns:
            Optional[Dict[str, Any]]: A dictionary where keys are the variable names and values are their current
                values read from the C library for the current time step. Returns `None` if an error occurs.
        """
        step_result: Dict[str, Any] = {}
        for dd_element_name, dd_element_value in self._dd.items():
            try:
                if dd_element_value.type not in ["out", "inout"]:
                    continue

                sim_var = self._dll_interface[dd_element_name]
                size = dd_element_value.size
                np_dtype = self.DATATYPES[dd_element_value.datatype][1]

                if len(size) == 0:
                    step_result[dd_element_name] = np.array(
                        sim_var.value, dtype=np_dtype
                    )
                elif len(size) == 1:
                    step_result[dd_element_name] = np.array(
                        list(sim_var), dtype=np_dtype
                    )
                elif len(size) == 2:
                    step_result[dd_element_name] = np.zeros(
                        (size[0], size[1]), dtype=np_dtype
                    )
                    for i in range(size[0]):
                        step_result[dd_element_name][i, :] = np.array(
                            list(sim_var[i]), dtype=np_dtype
                        )
                else:
                    logger.warning(
                        f"Invalid size '{size}' for '{dd_element_name}'. Expected 0 (scalar), 1 (1D), or 2 (2D) dimensions.",
                    )
                    continue

            except Exception as e:
                logger.error(
                    f"Error reading output value '{dd_element_name}' from 'ares_simunit' function: {e}",
                )

        return step_result
