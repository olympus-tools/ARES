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
import time
from collections.abc import Mapping
from itertools import chain
from pathlib import Path
from typing import Any, ClassVar, Literal, TypeVar

import numpy as np
from pydantic import ValidationError

from ares.interface.data.ares_data_interface import AresDataInterface
from ares.interface.data.ares_signal import AresSignal
from ares.interface.parameter.ares_parameter import AresParameter
from ares.interface.parameter.ares_parameter_interface import AresParamInterface
from ares.pydantic_models.datadictionary_model import (
    DataDictionaryModel,
    ParameterModel,
    SignalElement,
)
from ares.pydantic_models.workflow_model import SimUnitElement
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
        source_name: str | None = None,
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
            source_name (str | None): Optional name of the simulation unit source, used for logging and traceability.
        """

        self.file_path: Path = file_path
        self.dd_path: Path = dd_path
        self.source_name: str | None = source_name
        self._sim_functions_init: list[Any] = []
        self._sim_functions_cyclical: list[Any] = []

        self._dd: DataDictionaryModel = self._load_and_validate_dd(dd_path=dd_path)
        self._library: ctypes.CDLL = self._load_library()
        self._dll_interface: dict[str, Any] | None = self._setup_c_interface()
        self._setup_sim_function()

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
    def _load_and_validate_dd(self, dd_path: Path) -> DataDictionaryModel:
        """Loads the Data Dictionary from a JSON file and validates its structure using Pydantic.

        If the file cannot be found or parsed, or if validation fails, an error is
        logged and `None` is returned.

        Args:
            dd_path (Path): The path to the Data Dictionary JSON file.

        Returns:
            DataDictionaryModel: The loaded and validated Data Dictionary as a Pydantic
                object.
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
    def _load_library(self) -> ctypes.CDLL:
        """Loads a shared library file using `ctypes`.

        This makes the symbols (variables and functions) from the C library accessible in Python.

        Returns:
            ctypes.CDLL: The loaded `ctypes.CDLL` object.
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

        for dd_element_name, dd_element_value in chain(
            (self._dd.signals or {}).items(), (self._dd.parameters or {}).items()
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
                logger.debug(
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
    def _setup_sim_function(self):
        """Configures initialization and cyclical simulation functions from the shared library.

        Reads the execution_order from the Data Dictionary and sets up function lists for
        initialization and cyclical execution phases. If no execution_order is defined,
        defaults to using 'ares_simunit' as the cyclical function.

        For each function, it sets the argument types (`argtypes`) and return type (`restype`)
        to ensure correct function calls via `ctypes`.
        """

        if self._dd.execution_order:
            function_names_init = self._dd.execution_order.initialization
            function_names_cyclical = self._dd.execution_order.cyclical or [
                "ares_simunit"
            ]
        else:
            function_names_init = []
            function_names_cyclical = ["ares_simunit"]

        if function_names_init:
            for function_name in function_names_init:
                sim_function = getattr(self._library, function_name)
                sim_function.argtypes = []
                sim_function.restype = None
                self._sim_functions_init.append(sim_function)
                logger.debug(
                    f"Ares simulation unit initialization function '{function_name}' successfully set up.",
                )

        if function_names_cyclical:
            for function_name in function_names_cyclical:
                sim_function = getattr(self._library, function_name)
                sim_function.argtypes = []
                sim_function.restype = None
                self._sim_functions_cyclical.append(sim_function)
                logger.debug(
                    f"Ares simulation unit cyclical function '{function_name}' successfully set up.",
                )

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

        sim_result: dict[str, AresSignal] = {}
        if data:
            timestamps = np.empty((len(data[0].timestamps),), dtype=np.float32)
            timestamps[:] = data[0].timestamps
        else:
            timestamps = np.empty((1,), dtype=np.float32)
            timestamps[:] = 0.0
        time_steps = len(timestamps) if data else 1

        # mapping and casting of signal list
        data_dict = self._list_to_dict(data if data else [])
        mapped_data_dict = self._map_sim_input_data(
            data_dict=data_dict, time_steps=time_steps
        )
        mapped_data_dict = self._input_typecast(
            sim_input=mapped_data_dict, dd_element_dict=self._dd.signals or {}
        )
        self._interface_consistency_check(
            interface_dict=mapped_data_dict, direction="Input"
        )
        # mapping and casting of parameter list
        parameter_dict = self._list_to_dict(parameters if parameters else [])
        mapped_parameter_dict = self._map_sim_input_parameters(
            parameter_dict=parameter_dict
        )
        mapped_parameter_dict = self._input_typecast(
            sim_input=mapped_parameter_dict, dd_element_dict=self._dd.parameters or {}
        )
        self._interface_consistency_check(
            interface_dict=mapped_parameter_dict, direction="Input"
        )

        if data:
            logger.info(
                f"The simulation starts at timestamps {min(timestamps):.3f} seconds "
                f"and ends at timestamps {max(timestamps):.3f} seconds - duration: "
                f"{max(timestamps) - min(timestamps):.3f} seconds",
            )
        else:
            logger.info(
                "No input data (time array) provided => executing single time step."
            )

        self._write_base_elements_to_dll(
            base_element_dict=mapped_parameter_dict, dd_scope=self._dd.parameters or {}
        )

        output_signals = [
            k for k, v in (self._dd.signals or {}).items() if v.type in ["out", "inout"]
        ]
        for signal in output_signals:
            size = self._dd.signals[signal].size
            np_dtype = self.DATATYPES[self._dd.signals[signal].datatype][1]
            if len(size) == 0:
                value = np.empty((time_steps,), dtype=np_dtype)
            elif len(size) == 1:
                value = np.empty((time_steps, size[0]), dtype=np_dtype)
            elif len(size) == 2:
                value = np.empty((time_steps, size[0], size[1]), dtype=np_dtype)
            else:
                continue
            sim_result[signal] = AresSignal(
                label=signal,
                timestamps=timestamps,
                value=value,
                description=self._dd.signals[signal].description,
                source=self.source_name,
                unit=self._dd.signals[signal].unit,
            )

        # running initialization function
        if self._sim_functions_init:
            logger.info("Running initialization functions...")
            for sim_function in self._sim_functions_init:
                sim_function()

        # running cyclical functions
        if self._sim_functions_cyclical:
            logger.info(f"Running cyclical functions for {time_steps} time steps...")
            progress_indices = [round(i * (time_steps - 1) / 10) for i in range(11)]
            progress_step = 0
            time_real_start = time.perf_counter()
            time_sim_start = float(timestamps[0]) if data else 0.0
            for time_step_idx in range(time_steps):
                self._write_base_elements_to_dll(
                    base_element_dict=mapped_data_dict,
                    dd_scope=self._dd.signals or {},
                    time_step_idx=time_step_idx,
                )
                for sim_function in self._sim_functions_cyclical:
                    sim_function()
                step_result = self._read_dll_interface()
                for signal in output_signals:
                    sim_result[signal].value[time_step_idx] = step_result[signal]

                if time_step_idx >= progress_indices[progress_step]:
                    time_real_elapsed = time.perf_counter() - time_real_start
                    time_sim_elapsed = (
                        float(timestamps[time_step_idx]) - time_sim_start
                        if data
                        else 0.0
                    )
                    time_speedup_hint = (
                        f" - speedup factor {time_sim_elapsed / time_real_elapsed:.1f}"
                        if time_real_elapsed > 0 and time_sim_elapsed > 0
                        else ""
                    )
                    logger.info(
                        f"Simulation progress: {progress_step * 10}%{time_speedup_hint}"
                    )
                    progress_step += 1
                    time_real_start = time.perf_counter()
                    time_sim_start = float(timestamps[time_step_idx]) if data else 0.0

        self._interface_consistency_check(interface_dict=sim_result, direction="Output")

        logger.info("ares simulation successfully finished.")
        return list(sim_result.values())

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
    ) -> dict[str, AresSignal]:
        """Maps the provided input data to the expected simulation variables from the DD.

        This method handles missing signals by checking for alternative names or assigning
        a default static value of 0.

        Args:
            data_dict (dict[str, AresSignal]): Dictionary of input signals keyed by signal label.
            time_steps (int): The total number of simulation steps.

        Returns:
            dict[str, AresSignal]: A dictionary of mapped AresSignal objects.
        """

        mapped_data_dict: dict[str, AresSignal] = {}

        timestamps = (
            data_dict[next(iter(data_dict))].timestamps
            if data_dict
            else np.arange(time_steps, dtype=np.float64)
        )

        for dd_element_name, dd_element_value in (self._dd.signals or {}).items():
            try:
                mapped = False

                if dd_element_value.type not in ["in", "inout"]:
                    continue

                if dd_element_name in data_dict:
                    mapped_data_dict[dd_element_name] = data_dict[dd_element_name]
                    logger.debug(
                        f"Data dictionary signal '{dd_element_name}' could be mapped to the original signal in data source.",
                    )
                    continue

                if dd_element_value.mapping_alternatives:
                    for alternative_value in dd_element_value.mapping_alternatives:
                        mapped = False

                        if isinstance(alternative_value, str):
                            if alternative_value in data_dict:
                                mapped_data_dict[dd_element_name] = data_dict[
                                    alternative_value
                                ]
                                logger.info(
                                    f"Data dictionary signal '{dd_element_name}' has been mapped to alternative '{alternative_value}' from data source.",
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
                            mapped_data_dict[dd_element_name] = AresSignal(
                                label=dd_element_name,
                                value=static_value,
                                timestamps=timestamps,
                                description=f"Static value as alternative: {alternative_value}",
                            )
                            logger.info(
                                f"Data dictionary signal '{dd_element_name}' has been mapped to constant value {alternative_value}.",
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
                    mapped_data_dict[dd_element_name] = AresSignal(
                        label=dd_element_name,
                        value=default_value,
                        timestamps=timestamps,
                        description=f"Static value as alternative: {default_value}",
                    )
                    logger.warning(
                        f"Data dictionary signal '{dd_element_name}' could not be mapped. Default constant value 0 has been assigned.",
                    )

            except Exception as e:
                logger.warning(
                    f"Mapping dynamic simulation input to signal {dd_element_name} could not be executed: {e}",
                )

        logger.debug(
            "Mapping dynamic simulation input to data source has been successfully finished."
        )
        return mapped_data_dict

    @safely_run(
        default_return=None,
        exception_msg="Mapping parameter input could not be executed.",
        log=logger,
        instance_el=["file_path", "dd_path"],
    )
    @typechecked
    def _map_sim_input_parameters(
        self, parameter_dict: dict[str, AresParameter]
    ) -> dict[str, AresParameter]:
        """Maps the provided parameters to the expected simulation variables from the DD.

        Handles missing parameters by checking mapping_alternatives or assigning a
        default value of 0. Unlike signal mapping, parameters have no time dimension.

        Args:
            parameter_dict (dict[str, AresParameter]): Dictionary of input parameters
                keyed by label.

        Returns:
            dict[str, AresParameter]: A dictionary of all DD parameters, mapped to
                either a provided, alternative, or default value.
        """
        mapped_parameter_dict: dict[str, AresParameter] = {}

        for dd_element_name, dd_element_value in (self._dd.parameters or {}).items():
            try:
                mapped = False

                if dd_element_name in parameter_dict:
                    mapped_parameter_dict[dd_element_name] = parameter_dict[
                        dd_element_name
                    ]
                    logger.debug(
                        f"Data dictionary parameter '{dd_element_name}' could be mapped to the original parameter in parameter sourcee.",
                    )
                    continue

                if dd_element_value.mapping_alternatives:
                    for alternative_value in dd_element_value.mapping_alternatives:
                        mapped = False

                        if isinstance(alternative_value, str):
                            if alternative_value in parameter_dict:
                                mapped_parameter_dict[dd_element_name] = parameter_dict[
                                    alternative_value
                                ]
                                logger.info(
                                    f"Data dictionary parameter '{dd_element_name}' has been mapped to alternative '{alternative_value}' from parameter source.",
                                )
                                mapped = True
                                break
                        else:
                            np_dtype = self.DATATYPES[dd_element_value.datatype][1]
                            mapped_parameter_dict[dd_element_name] = AresParameter(
                                label=dd_element_name,
                                value=np.array(alternative_value, dtype=np_dtype),
                                description=f"Static value: {alternative_value}",
                            )
                            logger.info(
                                f"Data dictionary parameter '{dd_element_name}' has been mapped to constant value {alternative_value}.",
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

                    np_dtype = self.DATATYPES[dd_element_value.datatype][1]
                    mapped_parameter_dict[dd_element_name] = AresParameter(
                        label=dd_element_name,
                        value=np.array(default_init_value, dtype=np_dtype),
                        description="Default value: 0",
                    )
                    logger.warning(
                        f"Data dictionary parameter '{dd_element_name}' could not be mapped. Default constant value 0 has been assigned.",
                    )

            except Exception as e:
                logger.warning(
                    f"Mapping parameter '{dd_element_name}' could not be executed: {e}",
                )

        logger.debug("Mapping parameter input has been successfully finished.")
        return mapped_parameter_dict

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
    ) -> np.ndarray:
        """Creates a NumPy array of a specified size and datatype, filled with a constant value.

        This is used to handle simulation variables that have a static value instead of a signal.
        The function supports scalar, 1D, and 2D arrays as static values.

        Args:
            time_steps (int): The total number of simulation steps.
            datatype (str): The target datatype for the NumPy array (e.g., 'float', 'int').
            size (list[int]): The size of the simulation variable (e.g., `[1]` for a scalar, `[10]` for an array).
            value (any): The constant value to assign to the variable.

        Returns:
            np.ndarray: A NumPy array containing the constant value for all time steps.
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
        else:
            np.ctypeslib.as_array(self._dll_interface[dd_element_name])[:] = input_value

    @typechecked
    def _write_base_elements_to_dll(
        self,
        base_element_dict: Mapping[str, AresSignal | AresParameter],
        dd_scope: Mapping[str, SignalElement | ParameterModel],
        time_step_idx: int | None = None,
    ):
        """Writes base elements (parameters or signals) to the DLL interface.

        This method handles both parameters (no time dimension) and signals (with time
        dimension). For signals, provide ``time_step_idx`` to index into the value array.

        Args:
            base_element_dict (dict[str, AresSignal | AresParameter]): Dictionary of
                AresSignal or AresParameter objects keyed by label.
            dd_scope (dict[str, SignalElement | ParameterModel]): The corresponding
                section from the Data Dictionary (signals or parameters).
            time_step_idx (int | None): Time step index for signal values. Use ``None``
                for parameters which have no time dimension.
        """
        for dd_element_name, dd_element_value in dd_scope.items():
            try:
                element_type = getattr(dd_element_value, "type", None)
                if element_type is not None and element_type not in ["in", "inout"]:
                    continue

                if dd_element_name in base_element_dict:
                    raw_value = base_element_dict[dd_element_name].value
                    input_value = (
                        raw_value[time_step_idx]
                        if time_step_idx is not None
                        else raw_value
                    )
                    size = dd_element_value.size
                    self._write_value_to_dll(
                        dd_element_name=dd_element_name,
                        input_value=input_value,
                        size=size,
                    )
                else:
                    logger.warning(
                        f"Element '{dd_element_name}' defined in data dictionary but not provided in input.",
                    )

            except Exception as e:
                logger.warning(
                    f"Warning writing element '{dd_element_name}' to '{self.file_path}' library not possible: {e}",
                )

    @typechecked
    def _input_typecast(
        self,
        sim_input: dict[str, AresBaseType],
        dd_element_dict: Mapping[str, SignalElement | ParameterModel],
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
        for dd_element_name, dd_element_value in (self._dd.signals or {}).items():
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
                else:
                    step_result[dd_element_name] = np.ctypeslib.as_array(sim_var)

            except Exception as e:
                logger.warning(
                    f"Reading output value '{dd_element_name}' from '{self.file_path}' library has not been successful: {e}",
                )

        return step_result

    @typechecked
    def input_keys(
        self, dd_element_type: Literal["signals", "parameters"]
    ) -> list[str]:
        """Returns a list of unique keys defined in the Data Dictionary for the given element type.

        For ``"signals"``, only entries with type ``"in"`` or ``"inout"`` are included.
        For ``"parameters"``, all entries are included regardless of direction.

        In both cases, string entries from ``mapping_alternatives`` are appended as
        additional lookup keys.

        Args:
            dd_element_type (Literal["signals", "parameters"]): The DD section to read.
                Must be either ``"signals"`` or ``"parameters"``.

        Returns:
            list[str]: Ordered list of unique DD keys and their string alternatives.
        """
        dd_element_keys = []

        for dd_element_name, dd_element_value in (
            getattr(self._dd, dd_element_type) or {}
        ).items():
            if dd_element_type == "parameters" or dd_element_value.type in [
                "in",
                "inout",
            ]:
                if dd_element_name not in dd_element_keys:
                    dd_element_keys.append(dd_element_name)
                if (
                    hasattr(dd_element_value, "mapping_alternatives")
                    and dd_element_value.mapping_alternatives
                ):
                    for alternative in dd_element_value.mapping_alternatives:
                        if (
                            isinstance(alternative, str)
                            and alternative not in dd_element_keys
                        ):
                            dd_element_keys.append(alternative)

        return dd_element_keys

    @typechecked
    def _interface_consistency_check(
        self,
        interface_dict: Mapping[str, AresSignal | AresParameter],
        direction: Literal["Input", "Output"],
    ):
        """Checks all values in the interface dictionary for NaN or Inf and logs warnings.

        Iterates over each entry in the interface dictionary. For floating-point
        dtypes, checks whether any element contains NaN or Inf. Integer and boolean
        dtypes are skipped as they cannot represent these special values.

        Args:
            interface_dict (dict[str, AresSignal | AresParameter]): Dictionary of
                AresSignal or AresParameter objects to validate.
            direction (Literal["Input", "Output"]): Direction context used in warning
                messages to indicate whether the affected variable is an input or output.
        """
        for label, element in interface_dict.items():
            try:
                value = element.value
                if not np.issubdtype(value.dtype, np.floating):
                    continue
                if np.any(np.isnan(value)):
                    logger.warning(
                        f"There might be a problem regarding data consistency. {direction} variable '{label}' contains NaN values."
                    )
                if np.any(np.isinf(value)):
                    logger.warning(
                        f"There might be a problem regarding data consistency. {direction} variable '{label}' contains Inf values."
                    )
            except Exception as e:
                logger.warning(
                    f"Could not check {direction} variable '{label}' for NaN/Inf: {e}"
                )


def ares_plugin(plugin_input: SimUnitElement):
    """ARES plugin entrypoint for sim_unit elements.

    Args:
        plugin_input (SimUnitElement): Pydantic model containing all plugin configuration and data.
            name (str): Name of the workflow element.
            file_path (Path): Path to the shared library file (.so, .dll, .dylib).
            data_dictionary (Path): Path to the Data Dictionary JSON file.
            parameter_obj (dict[str, AresParamInterface]): AresParameter storage with hashes as keys.
            data_obj (dict[str, AresDataInterface]): AresData storage with hashes as keys.
            ...: Other fields from WorkflowElement as needed.

    Returns:
        None
    """

    parameter_lists: list[list[AresParamInterface]] = plugin_input.parameter_obj
    data_lists: list[list[AresDataInterface]] = plugin_input.data_obj

    if not parameter_lists:
        parameter_lists = [[AresParamInterface.create()]]
    if not data_lists:
        data_lists = [[AresDataInterface.create()]]

    sim_unit = SimUnit(
        file_path=plugin_input.file_path,
        dd_path=plugin_input.data_dictionary,
        source_name=plugin_input.name,
    )

    label_filter_signal = sim_unit.input_keys("signals")
    label_filter_parameter = sim_unit.input_keys("parameters")

    for parameter_list in parameter_lists:
        for parameter_obj in parameter_list:
            for data_list in data_lists:
                for data_obj in data_list:
                    dependencies = [parameter_obj.hash, data_obj.hash]

                    sim_result = sim_unit.run(
                        data=data_obj.get(
                            stepsize=plugin_input.stepsize,
                            label_filter=label_filter_signal,
                            vstack_pattern=plugin_input.vstack_pattern,
                        ),
                        parameters=parameter_obj.get(
                            label_filter=label_filter_parameter
                        ),
                    )

                    if sim_result is not None:
                        AresDataInterface.create(
                            data=sim_result,
                            dependencies=dependencies,
                            stepsize=plugin_input.stepsize,
                        )
