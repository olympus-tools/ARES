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
# Licensed under the GNU LGPLv3 License. You may obtain a copy of the 
# License at
#
#     https://github.com/AndraeCarotta/ARES/blob/master/LICENSE
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""

from .. import ares_globals
import os
import json
from jsonschema import validate, ValidationError
import ctypes
import numpy as np

class SimUnit:
    def __init__(self, file_path: str, dd_path: str):
        """
        Initializes the simulation unit.

        Loads the shared library and the data dictionary, and performs validation.

        Args:
            file_path (str): The path to the shared library (.so, .dll, .dylib).
            dd_path (str): The path to the Data Dictionary JSON file.
        """
        self.file_path = file_path
        self.dd_path = dd_path
        self.library = None
        self.dd = None
        self.dll_interface = {}
        self.sim_function = None

        self._load_library()
        self._load_dd()

        self._dd_validation()
        self._setup_c_interface()
        self._setup_sim_function()

    def _load_dd(self) -> dict | None:
        """
        Loads the Data Dictionary from the JSON file.

        Returns:
            dict | None: The loaded Data Dictionary as a dictionary, or None on error.
        """
        try:
            with open(self.dd_path, 'r', encoding='utf-8') as file:
                self.dd = json.load(file)
            ares_globals.logfile.write(f"Data dictionary '{self.dd_path}' successfully loaded.", level="INFO")
            return self.dd
        except FileNotFoundError:
            ares_globals.logfile.write(f"Data dictionary file not found at '{self.dd_path}'.", level="ERROR")
            return None
        except json.JSONDecodeError as e:
            ares_globals.logfile.write(f"Error parsing data dictionary JSON file '{self.dd_path}': {e}", level="ERROR")
            return None
        except Exception as e:
            ares_globals.logfile.write(f"Unexpected error loading data dictionary file '{self.dd_path}': {e}", level="ERROR")
            return None

    def _dd_validation(self):
        """
        Checks whether logical rules in the Data Dictionary JSON are followed.
        Writes error messages to the logfile.
        """
        dd_schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dd_schema.json')
        with open(dd_schema_path , 'r', encoding='utf-8') as schema_file:
            schema = json.load(schema_file)

        try:
            validate(instance=self.dd, schema=schema)
            ares_globals.logfile.write(f"The JSON data in '{self.dd_path}' is valid according to schema '{dd_schema_path}'.", level="INFO")
        except ValidationError as e:
            log_message = (
                f"Validation Error in data dictionary JSON file '{self.dd_path}': "
                f"Message: {e.message}. "
                f"Path: {' -> '.join(map(str, e.path))}. "
                f"Schema Path: {' -> '.join(map(str, e.schema_path))}. "
                f"Invalid Data: {json.dumps(e.instance, indent=2)}"
            )
            ares_globals.logfile.write(log_message, level="ERROR")
        except Exception as e:
            ares_globals.logfile.write(f"Unexpected error during data dictionary JSON file validation: {e}", level="ERROR")

    def _load_library(self) -> ctypes.CDLL | None:
        """
        Loads the shared library into ctypes.

        Returns:
            ctypes.CDLL | None: The loaded library or None on error.
        """
        try:
            self.library = ctypes.CDLL(self.file_path)
            ares_globals.logfile.write(f"Library '{self.file_path}' successfully loaded.", level="INFO")
            return self.library
        except OSError as e:
            ares_globals.logfile.write(f"Error loading shared library '{self.file_path}': {e}", level="ERROR")
            return None
        except Exception as e:
            ares_globals.logfile.write(f"Unexpected error loading library '{self.file_path}': {e}", level="ERROR")
            return None

    def _setup_c_interface(self):
        """
        Maps the global variables from the data dictionary to their ctypes counterparts in the loaded library.
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
            "ulonglong": ctypes.c_ulonglong
        }
        
        for var_name, var_info in self.dd.items():
            try:
                datatype = var_info["datatype"]
                size = var_info["size"]
                base_ctypes_type = c_types_map.get(datatype)

                if len(size) == 1:
                    if size[0] == 1: # Scalar or pointer to a single element
                        ctypes_type = base_ctypes_type 
                    elif size[0] > 1: # 1D array
                        ctypes_type = base_ctypes_type * size[0]
                    else:
                        ares_globals.logfile.write(f"Invalid size '{size[0]}' for datatype '{datatype}' in variable '{var_name}'. Expected > 0.", level="ERROR")
                elif len(size) == 2: # 2D array
                    ctypes_type = (base_ctypes_type * size[1]) * size[0]
                else:
                        ares_globals.logfile.write(f"Invalid size '{size}' for datatype '{datatype}' in variable '{var_name}'. Expected > 0.", level="ERROR")

                self.dll_interface[var_name] = ctypes_type.in_dll(self.library, var_name)
                ares_globals.logfile.write(f"Global simulation variable '{var_name}' defined with datatype '{var_info['datatype']}' and size '{var_info['size']}'.", level="INFO")
            except AttributeError as e:
                ares_globals.logfile.write(f"Failed to map global simulation variable '{var_name}': Symbol not found or type mismatch. {e}", level="ERROR")
            except Exception as e:
                ares_globals.logfile.write(f"An unexpected error occurred while mapping global simulation variable '{var_name}': {e}", level="ERROR")

    def _setup_sim_function(self):
        """
        Sets up the main simulation function (ares_simunit).
        """
        try:
            self.sim_function = self.library.ares_simunit
            self.sim_function.argtypes = []
            self.sim_function.restype = None
            ares_globals.logfile.write(f"ares simulation function 'ares_simunit' successfully set up.", level="INFO")
        except AttributeError as e:
            self.sim_function = None
            ares_globals.logfile.write(f"ares simulation function 'ares_simunit' not found in library: {e}", level="ERROR")
        except Exception as e:
            self.sim_function = None
            ares_globals.logfile.write(f"An unexpected error occurred while setting up ares simulation function: {e}", level="ERROR")

    def run_simulation(self, simulation_input: dict) -> dict | None:
        """
        Executes the main simulation function (ares_simunit).
        Processes simulations over multiple time steps.

        Args:
            simulation_input (dict): A dictionary containing all input signals,
                                      typically including a 'timestamps' list.
                                      Example: {"timestamps": [t0, t1], "signal_A": [v0, v1]}

        Returns:
            list[dict] | None: A list of dictionaries containing the output values per time step,
                               or None on error.
        """
        ares_globals.logfile.write("Starting ares simulation...", level="INFO")

        try:
            sim_result = {}
            num_steps = len(simulation_input["timestamps"])
            ares_globals.logfile.write(f"The simulation starts at timestamp {simulation_input["timestamps"][0]} seconds and ends at timestamp {simulation_input["timestamps"][-1]} seconds - duration: {simulation_input["timestamps"][-1]-simulation_input["timestamps"][0]}seconds", level="INFO")
           
            mapped_input = self._map_sim_input(input_data=simulation_input, num_steps=num_steps)

            for i in range(num_steps):
                self._write_dll_interface(input = mapped_input, timestep = i)
                self.sim_function()
                step_result = self._read_dll_interface()
                step_result["timestamp"] = simulation_input["timestamps"][i]
                
                for output_signal in step_result.keys():
                    if output_signal not in sim_result:
                        sim_result[output_signal] = []
                    sim_result[output_signal].append(step_result[output_signal])
            
            ares_globals.logfile.write(f"ares simulation successfully finished.", level="INFO")
            return sim_result
        except Exception as e:
            ares_globals.logfile.write(f"Error while running ares simulation: {e}", level="ERROR")
            return None

    def _map_sim_input(self, input_data: dict, num_steps: int) -> dict | None:
        """
        Maps user input signals to the expected Data Dictionary variables.
        Considers alternative input names and sets missing values to 0.

        Args:
            input_data (dict): The input data from an input (e.g. data source).
            num_steps (int): Number of simulation steps.

        Returns:
            dict | None: The mapped input values, ready to be written to the DLL,
                         or None on error.
        """
        ares_globals.logfile.write("Starting mapping of simulation signals...", level="INFO")
        try:
            mapped_input = {}
            for var_name_dll_interface in self.dll_interface.keys():
                if var_name_dll_interface in input_data:
                    mapped_input[var_name_dll_interface] = input_data[var_name_dll_interface]
                    ares_globals.logfile.write(f"Simulation signal '{var_name_dll_interface}' could be mapped to the original signal.", level="INFO")
                else:
                    size = self.dd[var_name_dll_interface]["size"]
                    if "input_alternatives" in self.dd[var_name_dll_interface]:
                        for alternative_value in self.dd[var_name_dll_interface]["input_alternatives"]:
                            if isinstance(alternative_value, str):
                                if alternative_value in input_data:
                                    mapped_input[var_name_dll_interface] = input_data[alternative_value]
                                    ares_globals.logfile.write(f"Simulation signal '{var_name_dll_interface}' has been mapped to alternative '{alternative_value}'.", level="INFO")
                                    break
                            else:
                                mapped_input[var_name_dll_interface] = self._map_sim_input_static(num_steps=num_steps, datatype=self.dd[var_name_dll_interface]["datatype"], size=size, value=alternative_value)
                                ares_globals.logfile.write(f"Simulation signal '{var_name_dll_interface}' has been mapped to constant value {alternative_value}.", level="INFO")
                                break
                        if var_name_dll_interface not in mapped_input:
                            value = 0
                            mapped_input[var_name_dll_interface] = self._map_sim_input_static(num_steps=num_steps, datatype=self.dd[var_name_dll_interface]["datatype"], size=size, value=value)
                            ares_globals.logfile.write(f"Simulation signal '{var_name_dll_interface}' has been mapped to constant value {value}.", level="INFO")
                    else:
                        value = 0
                        mapped_input[var_name_dll_interface] = self._map_sim_input_static(num_steps=num_steps, datatype=self.dd[var_name_dll_interface]["datatype"], size=size, value=value)
                        ares_globals.logfile.write(f"Simulation signal '{var_name_dll_interface}' has been mapped to constant value {value}.", level="INFO")
            ares_globals.logfile.write("Mapping is successfully finished.", level="INFO")
            return mapped_input
        except Exception as e:
            ares_globals.logfile.write(f"Error during mapping of simulation input signals: {e}", level="ERROR")
            return None
        
    def _map_sim_input_static(self, num_steps: int, datatype: str, size: list, value) -> list | None:
        """
        Assigns a constant value, from signal alternatives or the default value 0 to a
        simulation variable.

        Args:
            num_steps (int): Number of simulation steps (based on timestamps list).
            datatype (str): Datatype of simulation variable, that has to be mapped.
            size (list): Size of simulation variable, that has to be mapped.
            value (int | list): Value, that has to be assigned to simulation variable.

        Returns:
            list | None: Simulation variable, that got assigned with a constant value|array.
        """
        try:
            if len(size) == 1:
                out = np.empty((num_steps, size[0]), dtype=datatype)
                for i in range(num_steps):
                    out[i] = value
                return out
            elif len(size) == 2:
                #TODO: Impelement vairant for 2D array
                ares_globals.logfile.write(f"Static mapping for 2D array is not yet implemented. Skipping.", level="WARNING")
        except Exception as e:
            ares_globals.logfile.write(f"Error during mapping static value {value} : {e}", level="ERROR")
            return None

    def _write_dll_interface(self, input: dict, timestep: int):
        """
        Sets the input of the global C variables before the simulation run.

        Args:
            input (dict): A dictionary with variable names and their new input for one time step.
            timestep (int): Timestep which should be written to 'ares_simunit' function.
        """
        for sim_var_name in self.dll_interface.keys():
            try:
                sim_var = self.dll_interface[sim_var_name]
                sim_var_info = self.dd.get(sim_var_name)

                if sim_var_info and sim_var_info.get("type") not in ["in", "inout"]:
                    continue
            
                if isinstance(sim_var, ctypes._SimpleCData):
                    sim_var.value = input[sim_var_name][timestep]
                elif isinstance(sim_var, ctypes.Array):
                    if len(sim_var_info["size"]) == 1:
                        for i in range(sim_var_info["size"][0]):
                            sim_var[i] = input[sim_var_name][timestep][i]
                    elif len(sim_var_info["size"]) == 2:
                        #TODO: Impelement vairant for 2D array
                        ares_globals.logfile.write(f"Writing to 2D array '{sim_var_name}' is not yet implemented. Skipping.", level="WARNING")
                        continue
                else:
                    ares_globals.logfile.write(f"Unhandled ctypes type for '{sim_var_name}': '{type(sim_var)}'. Cannot set values.", level="ERROR")
            except Exception as e:
                ares_globals.logfile.write(f"Error writing input value '{sim_var_name}' of to 'ares_simunit' fucntion: {e}", level="ERROR")

    def _read_dll_interface(self) -> dict:
        """
        Reads the current values of the global C variables.

        Returns:
            dict: A dictionary with variable names and their current values.
        """
        current_values = {}
        for sim_var_name in self.dll_interface.keys():
            try:
                sim_var = self.dll_interface[sim_var_name]
                sim_var_info = self.dd.get(sim_var_name)

                if sim_var_info and sim_var_info.get("type") not in ["out", "inout"]:
                    continue

                if isinstance(sim_var, ctypes._SimpleCData):
                    current_values[sim_var_name] = sim_var.value
                elif isinstance(sim_var, ctypes.Array):
                    if len(sim_var_info["size"]) == 1:
                        current_values[sim_var_name] = [sim_var[i] for i in range(sim_var_info["size"][0])]
                    elif len(sim_var_info["size"]) == 2:
                        #TODO: Impelement vairant for 2D array
                        ares_globals.logfile.write(f"Reading 2D array '{sim_var_name}' is not yet implemented. Skipping.", level="WARNING")
                        continue
                else:
                    ares_globals.logfile.write(f"Unhandled ctypes type for '{sim_var_name}'. Cannot get value.", level="ERROR")
            except Exception as e:
                ares_globals.logfile.write(f"Error writing output value '{sim_var_name}' of to 'ares_simunit' fucntion: {e}", level="ERROR")
        return current_values