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
from ares.plugins.sim_interface import (
    GTYPE,
    MappingEntry,
    PROGRESS_CB,
    SimulationRunner,
    build_signal_list,
)
from ares.pydantic_models.datadictionary_model import (
    DataDictionaryModel,
    ParameterModel,
    SignalElement,
)
from ares.pydantic_models.workflow_model import SimUnitElement
from ares.utils.decorators import error_msg, safely_run
from ares.utils.decorators import typechecked_dev as typechecked
from ares.utils.logger import create_logger

logger = create_logger(name=__name__)

AresBaseType = TypeVar("AresBaseType", AresSignal, AresParameter)


class SimUnit:
    """Wrapper for a C shared library simulation unit that manages the full simulation lifecycle.

    Loads and validates the Data Dictionary, maps C global variables to ctypes objects,
    and provides methods to run the simulation over a sequence of time steps.
    """

    DATATYPES: ClassVar[dict[str, list[Any]]] = {
        "float": [ctypes.c_float, np.float32],
        "double": [ctypes.c_double, np.float64],
        "bool": [ctypes.c_bool, np.bool_],
        "int8": [ctypes.c_int8, np.int8],
        "int16": [ctypes.c_int16, np.int16],
        "short": [ctypes.c_int16, np.int16],
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

        # The C simulation runner steps the whole time series in one ctypes
        # call. When it cannot be built (no C compiler) it is None and the
        # per-step Python loop is used instead; both paths produce the same
        # results.
        self._sim_runner: SimulationRunner | None = SimulationRunner.load()
        self._static_input_labels: set[str] = set()

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
        # XXX: according to:
        # https://numpy.org/doc/stable/reference/routines.ctypeslib.html
        # https://numpy.org/devdocs/user/c-info.python-as-glue.html#index-2
        # https://chan-y-park.github.io/blog/numpy_ctypeslib.html
        # using ctypes via numpy holds the "advanctage" that we can transfer pointers to C
        # library = np.ctypeslib.load_library(self.file_path)
        # Test?

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
        self._static_input_labels = set()
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

        self._write_parameters_to_dll(base_parameter_dict=mapped_parameter_dict)

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
        # The whole time series is stepped inside one C call by the simulation
        # runner (per-step memcpy of the signal mappings + function calls). The
        # Python loop below is the fully-equivalent fallback used when the
        # runner cannot be built.
        if self._sim_runner is not None:
            logger.info(
                f"Running cyclical functions in C for {time_steps} time steps..."
            )
            self._run_c_loop(
                sim_result=sim_result,
                mapped_data_dict=mapped_data_dict,
                output_signals=output_signals,
                time_steps=time_steps,
                timestamps=timestamps,
                data=data,
            )
        else:
            logger.info(f"Running cyclical functions for {time_steps} time steps...")
            self._run_python_loop(
                sim_result=sim_result,
                mapped_data_dict=mapped_data_dict,
                output_signals=output_signals,
                time_steps=time_steps,
                timestamps=timestamps,
                data=data,
            )

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
                            self._static_input_labels.add(dd_element_name)
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
                    self._static_input_labels.add(dd_element_name)

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
    def _write_parameters_to_dll(
        self,
        base_parameter_dict: Mapping[str, AresParameter],
    ) -> None:
        """Writes all parameters to the DLL interface once before the simulation starts.

        Parameters have no time dimension and are written exactly once, before
        the initialization and cyclical functions run.
        """
        for dd_element_name, dd_element_value in (self._dd.parameters or {}).items():
            try:
                if dd_element_name in base_parameter_dict:
                    raw_value = base_parameter_dict[dd_element_name].value
                    size = dd_element_value.size
                    self._write_value_to_dll(
                        dd_element_name=dd_element_name,
                        input_value=raw_value,
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
    def _write_step_input_to_dll(
        self,
        mapped_data_dict: Mapping[str, AresSignal],
        time_step_idx: int,
    ) -> None:
        """Writes the values of one time step of every input signal to the DLL globals.

        Used by the Python stepping loop fallback.
        """
        for dd_element_name, dd_element_value in (self._dd.signals or {}).items():
            try:
                if dd_element_value.type not in ["in", "inout"]:
                    continue
                if dd_element_name in mapped_data_dict:
                    size = dd_element_value.size
                    self._write_value_to_dll(
                        dd_element_name=dd_element_name,
                        input_value=mapped_data_dict[dd_element_name].value[
                            time_step_idx
                        ],
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
        """Cast all values in the input dictionary to the numpy dtypes defined in the Data Dictionary.

        Ensures all AresSignal and AresParameter values are in the correct numeric format
        before being written to the simulation interface.

        Args:
            sim_input (dict[str, AresBaseType]): Dictionary of AresSignal or AresParameter
                objects keyed by label.
            dd_element_dict (Mapping[str, SignalElement | ParameterModel]): Data Dictionary
                section (signals or parameters) providing the expected dtypes.

        Returns:
            dict[str, AresBaseType]: The input dictionary with ``dtype_cast`` applied to
                each matching entry.
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
    def _run_python_loop(
        self,
        sim_result: dict[str, AresSignal],
        mapped_data_dict: dict[str, AresSignal],
        output_signals: list[str],
        time_steps: int,
        timestamps: np.ndarray,
        data: list[AresSignal] | None,
    ) -> None:
        """Steps the whole simulation in Python, one ctypes round-trip per step.

        This is the fallback used when the C runner could not be built and is
        behaviour-identical to :meth:`_run_c_loop`.
        """
        if not self._sim_functions_cyclical:
            return

        progress_indices = [round(i * (time_steps - 1) / 10) for i in range(11)]
        progress_step = 0
        time_real_start = time.perf_counter()
        time_sim_start = float(timestamps[0]) if data else 0.0

        for time_step_idx in range(time_steps):
            self._write_step_input_to_dll(
                mapped_data_dict=mapped_data_dict,
                time_step_idx=time_step_idx,
            )
            for sim_function in self._sim_functions_cyclical:
                sim_function()

            for signal in output_signals:
                sim_var = self._dll_interface[signal]
                size = self._dd.signals[signal].size
                if len(size) == 0:
                    sim_result[signal].value[time_step_idx] = sim_var.value
                else:
                    sim_result[signal].value[time_step_idx] = np.ctypeslib.as_array(
                        sim_var
                    )

            if time_step_idx >= progress_indices[progress_step]:
                time_real_elapsed = time.perf_counter() - time_real_start
                time_sim_elapsed = (
                    float(timestamps[time_step_idx]) - time_sim_start if data else 0.0
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

    @typechecked
    def _run_c_loop(
        self,
        sim_result: dict[str, AresSignal],
        mapped_data_dict: dict[str, AresSignal],
        output_signals: list[str],
        time_steps: int,
        timestamps: np.ndarray,
        data: list[AresSignal] | None,
    ) -> None:
        """Steps the whole time series inside one C call via the simulation runner.

        Each input/output signal is described by a byte mapping. The runner
        memcpy's the per-step values in and out of the simulation unit globals
        and calls the cyclical functions in order; static inputs are written
        once before the loop.
        """
        if self._sim_runner is None or not self._sim_functions_cyclical:
            return

        input_entries: list[MappingEntry] = []
        for dd_element_name, dd_element_value in (self._dd.signals or {}).items():
            if dd_element_value.type not in ["in", "inout"]:
                continue
            if dd_element_name not in mapped_data_dict:
                continue
            value = np.ascontiguousarray(mapped_data_dict[dd_element_name].value)
            input_entries.append(
                MappingEntry(
                    data_buffer=value.ctypes.data,
                    target_global=ctypes.addressof(
                        self._dll_interface[dd_element_name]
                    ),
                    num_bytes=self._mapping_num_bytes(value, dd_element_value.size),
                    write_once=dd_element_name in self._static_input_labels,
                )
            )

        output_entries: list[MappingEntry] = []
        for signal in output_signals:
            value = np.ascontiguousarray(sim_result[signal].value)
            output_entries.append(
                MappingEntry(
                    data_buffer=value.ctypes.data,
                    target_global=ctypes.addressof(self._dll_interface[signal]),
                    num_bytes=self._mapping_num_bytes(
                        value, self._dd.signals[signal].size
                    ),
                )
            )

        input_list, _ = build_signal_list(input_entries)
        output_list, _ = build_signal_list(output_entries)

        towards_c_func = (GTYPE * len(self._sim_functions_cyclical))()
        for i, sim_function in enumerate(self._sim_functions_cyclical):
            towards_c_func[i] = GTYPE(ctypes.cast(sim_function, ctypes.c_void_p).value)

        time_real_start = time.perf_counter()
        time_sim_start = float(timestamps[0]) if data else 0.0
        progress_step = 0

        def progress(step_idx: int) -> None:
            nonlocal time_real_start, time_sim_start, progress_step
            time_real_elapsed = time.perf_counter() - time_real_start
            time_sim_elapsed = (
                float(timestamps[step_idx]) - time_sim_start if data else 0.0
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
            time_sim_start = float(timestamps[step_idx]) if data else 0.0

        self._sim_runner.run(
            functions=towards_c_func,
            num_functions=len(self._sim_functions_cyclical),
            sim_steps=time_steps,
            input_list=input_list,
            output_list=output_list,
            progress_cb=PROGRESS_CB(progress),
        )

    @staticmethod
    def _mapping_num_bytes(value: np.ndarray, size: list[int]) -> int:
        """Bytes transferred per time step = ``itemsize * element count``."""
        element_count = 1
        for dim in size:
            element_count *= dim
        return element_count * value.dtype.itemsize

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

    Instantiates a :class:`SimUnit`, resolves input data and parameters from the
    workflow caches, runs the simulation for every data/parameter combination, and
    stores the results back into the :class:`AresDataInterface` cache.

    Args:
        plugin_input (SimUnitElement): Pydantic model containing all plugin configuration
            and data, including ``file_path``, ``data_dictionary``, ``parameter_obj``,
            ``data_obj``, and related workflow fields.
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
                            resample_method=plugin_input.resample_method,
                            resample_tolerance=plugin_input.resample_tolerance,
                        ),
                        parameters=parameter_obj.get(
                            label_filter=label_filter_parameter,
                            transpose=plugin_input.transpose_parameter,
                        ),
                    )

                    if sim_result is not None:
                        AresDataInterface.create(
                            data=sim_result,
                            dependencies=dependencies,
                            stepsize=plugin_input.stepsize,
                        )
