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

import ctypes
import json
from itertools import chain
from pathlib import Path
from typing import Any, ClassVar, TypeVar

import numpy as np
from pydantic import ValidationError

from ares.interface.data.ares_data_interface import AresDataInterface
from ares.interface.data.ares_signal import AresSignal
from ares.interface.parameter.ares_parameter import AresParameter
from ares.interface.parameter.ares_parameter_interface import AresParamInterface
from ares.pydantic_models.datadictionary_model import DataDictionaryModel
from ares.utils.decorators import error_msg, safely_run
from ares.utils.decorators import typechecked_dev as typechecked
from ares.utils.logger import create_logger

logger = create_logger(__name__)

AresBaseType = TypeVar("AresBaseType", AresSignal, AresParameter)


class SimUnit:
    DATATYPES: ClassVar[dict[str, list[Any]]] = {
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
        file_path: Path,
        dd_path: Path,
    ):
        """Initializes the simulation unit and sets up all required simulation parameters.

        This constructor performs the following steps:
        - Loads and validates the Data Dictionary (DD) from a JSON file
        - Loads the C shared library (.so, .dll, .dylib)
        - Maps C global variables to ctypes objects
        - Sets up the main simulation function
        - Stores all configuration parameters as instance variables

        Args:
            file_path (Path): Path to the shared library file (.so, .dll, .dylib).
            dd_path (Path): Path to the Data Dictionary JSON file.
        """

        self.file_path: Path = file_path
        self.dd_path: Path = dd_path
        self.function_name: str

        self._dd: DataDictionaryModel | None = self._load_and_validate_dd(
            dd_path=dd_path
        )
        self._library: ctypes.CDLL | None = self._load_library()
        self._dll_interface: dict[str, Any] | None = self._setup_c_interface()
        self._sim_function: Any = self._setup_sim_function()

    @error_msg(
        exception_msg="Unexpected error loading data dictionary json-file.",
        exception_map={
            FileNotFoundError: "Data dictionary file not found",
            json.JSONDecodeError: "Error parsing data dictionary JSON file",
            ValidationError: "Validation error for data dictionary",
        },
        log=logger,
        instance_el=["dd_path"],
    )
    @typechecked
    def _load_and_validate_dd(self, dd_path: Path) -> DataDictionaryModel | None:
        """Loads the Data Dictionary from a JSON file and validates its structure using Pydantic.

        If the file cannot be found or parsed, or if validation fails, an error is
        logged and `None` is returned.

        Args:
            dd_path (Path): The path to the Data Dictionary JSON file.

        Returns:
            DataDictionaryModel | None: The loaded and validated Data Dictionary as a Pydantic
                object, or `None` if an error occurs.
        """
        with open(dd_path, "r", encoding="utf-8") as file:
            dd_data = json.load(file)

        dd = DataDictionaryModel.model_validate(dd_data)
        logger.info(
            f"Data dictionary '{dd_path}' successfully loaded and validated.",
        )
        return dd

    @error_msg(
        exception_msg="Unexpected error during loading library.",
        exception_map={OSError: "Error loading shared library."},
        log=logger,
        instance_el=["file_path"],
    )
    @typechecked
    def _load_library(self) -> ctypes.CDLL | None:
        """Loads a shared library file using `ctypes`.

        This makes the symbols (variables and functions) from the C library accessible in Python.

        Returns:
            ctypes.CDLL | None: The loaded `ctypes.CDLL` object, or `None` if the library cannot be loaded.
        """
        library = ctypes.CDLL(self.file_path)

        # sumunit should be always a void void function
        # TODO: linter is throwing warning here - reportAttributeAccessIssue - i.O.?
        library.argtypes = []
        library.restype = None

        logger.info(
            f"Library '{self.file_path}' successfully loaded.",
        )
        return library

    @error_msg(
        exception_msg="Unexpected error during setting up C interface.",
        log=logger,
        instance_el=["file_path", "dd_path"],
    )
    @typechecked
    def _setup_c_interface(self) -> dict[str, Any] | None:
        """Maps global variables defined in the Data Dictionary to their corresponding ctypes objects.

        This process involves translating the datatype and size information from the DD into
        `ctypes` types and mapping them to the DLL's global variables.

        Returns:
            dict[str, Any] | None: A dictionary where keys are the variable names from the DD and values
                are the `ctypes` objects mapped to the DLL's global variables. Returns `None`
                if an error occurs during mapping (e.g., symbol not found).
        """
        dll_interface: dict[str, Any] = {}

        # iterate over both data and parameters
        for dd_element_name, dd_element_value in chain(
            self._dd.signals.items(), self._dd.parameters.items()
        ):
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
                logger.info(
                    f"Data dictionary variable '{dd_element_name}' defined with datatype '{datatype}' and size '{size}' found successfully in simulation unit.",
                )
            except AttributeError as e:
                logger.warning(
                    f"Failed to find data dictionary variable '{dd_element_name}' in simulation unit: Symbol not found or type mismatch. {e}",
                )
                continue
            except Exception as e:
                logger.warning(
                    f"An unexpected failure occurred while finding data dictionary variable '{dd_element_name}' in simulation unit: {e}",
                )
                continue

        if not dll_interface:
            logger.warning(
                "There is no data dictionary variable that could be found in simulation unit."
            )
            return None
        return dll_interface

    @error_msg(
        exception_msg="An unexpected error occurred while setting up ares simulation function.",
        exception_map={
            AttributeError: "Ares simulation function not found in library."
        },
        log=logger,
        instance_el=["file_path", "dd_path"],
    )
    @typechecked
    def _setup_sim_function(self) -> Any:
        """Configures the main simulation function (`ares_simunit`) from the shared library.

        It sets the argument types (`argtypes`) and return type (`restype`) to ensure
        correct function calls via `ctypes`.

        Returns:
            Any: The `ctypes` function object for `ares_simunit`, or `None` if the
                function cannot be found in the library.
        """
        # TODO: Should function name be defined in dd or in workflow file (same as for plugin entry point name)?
        if self._dd.meta_data and self._dd.meta_data.function_name:
            self.function_name = self._dd.meta_data.function_name
        else:
            self.function_name = "ares_simunit"

        sim_function = getattr(self._library, self.function_name)
        sim_function.argtypes = []
        sim_function.restype = None
        logger.debug(
            f"Ares simulation unit '{self.function_name}' successfully set up.",
        )
        return sim_function

    @error_msg(
        exception_msg="An unexpected error occurred during execution of ares simulation.",
        log=logger,
        instance_el=["file_path", "dd_path"],
    )
    @typechecked
    def run(
        self, data: list[AresSignal] | None, parameters: list[AresParameter] | None
    ) -> list[AresSignal] | None:
        """Executes the main simulation function over multiple time steps.

        It processes input data, writes it to the C interface, calls the simulation
        function for each time step, and reads the output back as AresSignal objects.

        Args:
            data (list[AresSignal] | None): List of AresSignal objects containing input signals with timestamps,
                or None if no input data is available.
            parameters (list[AresParameter] | None): List of AresParameter objects containing simulation parameters,
                or None if no parameters are available.

        Returns:
            list[AresSignal] | None: List of AresSignal objects containing output signals for all
                time steps, or `None` if an error occurs during the simulation.
        """
        logger.info("Starting ares simulation...")

        sim_result: dict[str, np.ndarray] = {}
        time_steps = len(data[0].timestamps) if data else 1

        data_dict = self._list_to_dict(data if data else [])
        data_dict = self._input_typecast(
            sim_input=data_dict, dd_element_dict=self._dd.signals
        )

        parameter_dict = self._list_to_dict(parameters if parameters else [])
        parameter_dict = self._input_typecast(
            sim_input=parameter_dict, dd_element_dict=self._dd.parameters
        )

        if data:
            logger.info(
                f"The simulation starts at timestamps {min(data[0].timestamps)} seconds "
                f"and ends at timestamps {max(data[0].timestamps)} seconds - duration: "
                f"{max(data[0].timestamps) - min(data[0].timestamps)} seconds",
            )
        else:
            logger.info(
                "No input data (time array) provided => executing single time step."
            )

        mapped_input = self._map_sim_input_data(
            data_dict=data_dict, time_steps=time_steps
        )

        self._write_parameters_to_dll(parameters=parameter_dict)

        output_signals = [
            k for k, v in self._dd.signals.items() if v.type in ["out", "inout"]
        ]
        for signal in output_signals:
            size = self._dd.signals[signal].size
            np_dtype = self.DATATYPES[self._dd.signals[signal].datatype][1]
            if len(size) == 0:
                sim_result[signal] = np.empty((time_steps,), dtype=np_dtype)
            elif len(size) == 1:
                sim_result[signal] = np.empty((time_steps, size[0]), dtype=np_dtype)
            elif len(size) == 2:
                sim_result[signal] = np.empty(
                    (time_steps, size[0], size[1]), dtype=np_dtype
                )
        sim_result["timestamps"] = np.empty((time_steps,), dtype=np.float32)

        for time_step_idx in range(time_steps):
            self._write_signals_to_dll(data=mapped_input, time_step_idx=time_step_idx)
            self._sim_function()
            step_result = self._read_dll_interface()
            for signal in output_signals:
                sim_result[signal][time_step_idx] = step_result[signal]
            if data:
                sim_result["timestamps"][time_step_idx] = data[0].timestamps[
                    time_step_idx
                ]
            else:
                sim_result["timestamps"][time_step_idx] = 0.0

        logger.info("ares simulation successfully finished.")
        return [
            AresSignal(
                label=signal_name,
                timestamps=sim_result["timestamps"],
                value=signal_value,
            )
            for signal_name, signal_value in sim_result.items()
            if signal_name != "timestamps"
        ]

    @typechecked
    def _list_to_dict(self, items: list[AresBaseType]) -> dict[str, AresBaseType]:
        """Converts a list of AresSignal or AresParameter objects to a dictionary keyed by label.

        Args:
            items (list[AresBaseType]): List of AresSignal or AresParameter objects.

        Returns:
            dict[str, AresBaseType]: Dictionary mapping item labels to the objects.
        """
        result_dict = {}
        for item in items:
            if item.label in result_dict:
                logger.warning(
                    f"Duplicate label '{item.label}' found - overwriting previous value."
                )
            result_dict[item.label] = item
        return result_dict

    @safely_run(
        default_return=None,
        exception_msg="Mapping dynamic simulation input to data source could not be executed.",
        log=logger,
        instance_el=["file_path", "dd_path"],
    )
    @typechecked
    def _map_sim_input_data(
        self, data_dict: dict[str, AresSignal], time_steps: int
    ) -> dict[str, AresSignal] | None:
        """Maps the provided input data to the expected simulation variables from the DD.

        This method handles missing signals by checking for alternative names or assigning
        a default static value of 0.

        Args:
            data_dict (dict[str, AresSignal]): Dictionary of input signals keyed by signal label.
            time_steps (int): The total number of simulation steps.

        Returns:
            dict[str, AresSignal] | None: A dictionary of mapped AresSignal objects, or `None` if a mapping error occurs.
        """

        mapped_input: dict[str, AresSignal] = {}

        timestamps = (
            data_dict[next(iter(data_dict))].timestamps
            if data_dict
            else np.arange(time_steps, dtype=np.float64)
        )
        for dd_element_name, dd_element_value in self._dd.signals.items():
            try:
                mapped = False

                if dd_element_value.type not in ["in", "inout"]:
                    continue

                if dd_element_name in data_dict:
                    mapped_input[dd_element_name] = data_dict[dd_element_name]
                    logger.info(
                        f"Data dictionary variable '{dd_element_name}' could be mapped to the original signal in data source.",
                    )
                    continue

                if (
                    hasattr(dd_element_value, "input_alternatives")
                    and dd_element_value.input_alternatives
                ):
                    for alternative_value in dd_element_value.input_alternatives:
                        mapped = False

                        if isinstance(alternative_value, str):
                            if alternative_value in data_dict:
                                mapped_input[dd_element_name] = data_dict[
                                    alternative_value
                                ]
                                logger.info(
                                    f"Data dictionary variable '{dd_element_name}' has been mapped to alternative '{alternative_value}' from data source.",
                                )
                                mapped = True
                                break
                        else:
                            static_value = self._map_sim_input_static(
                                time_steps=time_steps,
                                datatype=dd_element_value.datatype,
                                size=dd_element_value.size,
                                value=alternative_value,
                            )
                            mapped_input[dd_element_name] = AresSignal(
                                label=dd_element_name,
                                value=static_value,
                                timestamps=timestamps,
                                description=f"Static value: {alternative_value}",
                            )
                            logger.info(
                                f"Data dictionary variable '{dd_element_name}' has been mapped to constant value {alternative_value}.",
                            )
                            mapped = True
                            break

                if not mapped:
                    size = dd_element_value.size

                    if len(size) == 0:
                        default_init_value = 0
                    elif len(size) == 1:
                        default_init_value = [0] * size[0]
                    elif len(size) == 2:
                        default_init_value = [[0] * size[1] for _ in range(size[0])]
                    else:
                        default_init_value = 0

                    default_value = self._map_sim_input_static(
                        time_steps=time_steps,
                        datatype=dd_element_value.datatype,
                        size=size,
                        value=default_init_value,
                    )
                    mapped_input[dd_element_name] = AresSignal(
                        label=dd_element_name,
                        value=default_value,
                        timestamps=timestamps,
                        description="Default value: 0",
                    )
                    logger.info(
                        f"Data dictionary variable '{dd_element_name}' has been mapped to default constant value 0.",
                    )

            except Exception as e:
                logger.warning(
                    f"Mapping dynamic simulation input to signal {dd_element_name} could not be executed: {e}",
                )
                return None

        logger.debug(
            "Mapping dynamic simulation input to data source has been successfully finished."
        )
        return mapped_input

    @safely_run(
        default_return=None,
        exception_msg="Mapping static simulation input to data source could not be executed.",
        log=logger,
        include_args=["time_steps", "datatype", "size", "value"],
        instance_el=["file_path", "dd_path"],
    )
    @typechecked
    def _map_sim_input_static(
        self, time_steps: int, datatype: str, size: list[int], value: Any
    ) -> np.ndarray | None:
        """Creates a NumPy array of a specified size and datatype, filled with a constant value.

        This is used to handle simulation variables that have a static value instead of a signal.
        The function supports scalar, 1D, and 2D arrays as static values.

        Args:
            time_steps (int): The total number of simulation steps.
            datatype (str): The target datatype for the NumPy array (e.g., 'float', 'int').
            size (list[int]): The size of the simulation variable (e.g., `[1]` for a scalar, `[10]` for an array).
            value (any): The constant value to assign to the variable.

        Returns:
            np.ndarray | None: A NumPy array containing the constant value for all time steps, or `None`
                if an error occurs.
        """
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
            raise

    @safely_run(
        default_return=None,
        exception_msg="Writing value to library interface could not be executed.",
        log=logger,
        include_args=["dd_element_name", "input_value", "size"],
        instance_el=["file_path", "dd_path"],
    )
    @typechecked
    def _write_value_to_dll(
        self,
        dd_element_name: str,
        input_value: np.ndarray | np.generic,
        size: list[int],
    ) -> None:
        """Core method to write a single value to the DLL interface.

        Handles scalar, 1D, and 2D arrays by writing the appropriate data structure
        to the ctypes interface. Logs warnings if write fails.

        Args:
            dd_element_name (str): Name of the variable in the DLL interface.
            input_value (np.ndarray | np.generic): The value to write (numpy array or numpy scalar).
            size (list[int]): Size specification from Data Dictionary (0=scalar, 1=1D array, 2=2D array).
        """
        if len(size) == 0:
            self._dll_interface[dd_element_name].value = input_value.item()
        elif len(size) == 1:
            self._dll_interface[dd_element_name][:] = input_value.tolist()
        elif len(size) == 2:
            for i in range(size[0]):
                self._dll_interface[dd_element_name][i][:] = input_value[i].tolist()
        else:
            logger.warning(
                f"Invalid size '{size}' for '{dd_element_name}'. Expected 0 (scalar), 1 (1D), or 2 (2D) dimensions.",
            )
            raise

    @typechecked
    def _write_signals_to_dll(
        self, data: dict[str, AresSignal], time_step_idx: int
    ) -> None:
        """Writes signal values for a single time step to the DLL interface.

        Args:
            data (dict[str, AresSignal]): Dictionary with signal names as keys and AresSignal objects as values.
            time_step_idx (int): The index of the current time step.
        """
        for dd_element_name, dd_element_value in self._dd.signals.items():
            try:
                if dd_element_value.type not in ["in", "inout"]:
                    continue

                if dd_element_name in data:
                    input_value = data[dd_element_name].value[time_step_idx]
                    size = dd_element_value.size
                    self._write_value_to_dll(dd_element_name, input_value, size)

            except Exception as e:
                logger.warning(
                    f"Warning writing signal '{dd_element_name}' to '{self.function_name}' function: {e}",
                )

    @typechecked
    def _write_parameters_to_dll(self, parameters: dict[str, AresParameter]) -> None:
        """Writes parameter values to the DLL interface.

        Parameters have no time dimension and are written once.

        Args:
            parameters (dict[str, AresParameter]): Dictionary with parameter names as keys and AresParameter objects as values.
        """
        for dd_element_name, dd_element_value in self._dd.parameters.items():
            try:
                if dd_element_name in parameters:
                    input_value = parameters[dd_element_name].value
                    size = dd_element_value.size
                    self._write_value_to_dll(dd_element_name, input_value, size)

            except Exception as e:
                logger.warning(
                    f"Warning writing parameter '{dd_element_name}' to '{self.function_name}' function not possible: {e}",
                )

    @typechecked
    def _input_typecast(
        self, sim_input: dict[str, AresBaseType], dd_element_dict
    ) -> dict[str, AresBaseType]:
        """
        Typecasts the values of a dictionary of AresParameter or AresSignal objects to the numpy dtypes
        defined in the Data Dictionary. This ensures all values are in the correct format for simulation.

        Args:
            input: Dictionary of AresParameter or AresSignal objects keyed by label.
            dd_element_dict: Data Dictionary section (parameters or signals) providing expected dtypes.

        Returns:
            The input dictionary with dtype_cast applied to each matching entry.
        """
        for dd_element_name, dd_element_value in dd_element_dict.items():
            try:
                if dd_element_name in sim_input:
                    sim_input[dd_element_name].dtype_cast(
                        self.DATATYPES[dd_element_value.datatype][1]
                    )
            except Exception as e:
                logger.warning(
                    f"Typecast of dd element '{dd_element_name}' to '{dd_element_value.datatype}' failed: {e}",
                )
        return sim_input

    @typechecked
    def _read_dll_interface(self) -> dict[str, Any] | None:
        """Reads the current values of the global C variables from the shared library.

        It only reads from variables marked as `'out'` or `'inout'` in the Data Dictionary.

        Returns:
            dict[str, Any] | None: A dictionary where keys are the variable names and values are their current
                values read from the C library for the current time step. Returns `None` if an error occurs.
        """
        step_result: dict[str, Any] = {}
        for dd_element_name, dd_element_value in self._dd.signals.items():
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
                logger.warning(
                    f"Reading output value '{dd_element_name}' from '{self.function_name}' function has not been successful: {e}",
                )

        return step_result

    def input_signal_keys(self) -> list[str]:
        """Returns a list of unique signal keys defined in the Data Dictionary.

        Includes both signal names from the DD and string entries from input_alternatives.

        Returns:
            list[str]: A list of unique signal keys and alternative signal names.
        """
        signal_keys = []

        for dd_element_name, dd_element_value in self._dd.signals.items():
            if dd_element_value.type in ["in", "inout"]:
                if dd_element_name not in signal_keys:
                    signal_keys.append(dd_element_name)
                if (
                    hasattr(dd_element_value, "input_alternatives")
                    and dd_element_value.input_alternatives
                ):
                    for alternative in dd_element_value.input_alternatives:
                        if (
                            isinstance(alternative, str)
                            and alternative not in signal_keys
                        ):
                            signal_keys.append(alternative)

        return signal_keys

    def parameter_keys(self) -> list[str]:
        """Returns a list of unique parameter keys defined in the Data Dictionary.

        Returns:
            list[str]: A list of unique parameter keys.
        """
        parameter_keys = []

        for parameter_name in self._dd.parameters.keys():
            if parameter_name not in parameter_keys:
                parameter_keys.append(parameter_name)

        return parameter_keys


def ares_plugin(plugin_input):
    """ARES plugin entrypoint for sim_unit elements.

    Args:
        plugin_input (dict): Dictionary containing all plugin configuration and data.
            wf_element_name (str): Name of the workflow element.
            parameter (dict[str, AresParamInterface]): AresParameter storage with hashes as keys.
            plugin_path (Path): Path to this plugin file.
            type (str): Element type ("plugin" or "sim_unit").
            element_workflow (list[str]): Workflow elements.
            ...: Other fields from WorkflowElement as needed.

    Returns:
        None
    """

    element_parameter_lists: list[list[AresParamInterface]] = plugin_input.get(
        "parameter", None
    )
    element_data_lists: list[list[AresDataInterface]] = plugin_input.get("input", None)

    if not element_parameter_lists:
        element_parameter_lists = [[AresParamInterface.create()]]
    if not element_data_lists:
        element_data_lists = [[AresDataInterface.create()]]

    sim_unit = SimUnit(
        file_path=plugin_input["file_path"],
        dd_path=plugin_input["data_dictionary"],
    )

    label_filter_signal = sim_unit.input_signal_keys()
    label_filter_parameter = sim_unit.parameter_keys()

    for element_parameter_list in element_parameter_lists:
        for element_parameter_obj in element_parameter_list:
            for element_data_list in element_data_lists:
                for element_data_obj in element_data_list:
                    dependencies = [element_parameter_obj.hash, element_data_obj.hash]

                    sim_result = sim_unit.run(
                        data=element_data_obj.get(
                            stepsize=plugin_input["stepsize"],
                            label_filter=label_filter_signal,
                            vstack_pattern=plugin_input.get("vstack_pattern"),
                        ),
                        parameters=element_parameter_obj.get(
                            label_filter=label_filter_parameter
                        ),
                    )

                    if sim_result is not None:
                        AresDataInterface.create(
                            data=sim_result,
                            dependencies=dependencies,
                            source_name=plugin_input.get("wf_element_name"),
                        )
