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

class Workflow:
    def __init__(self, file_path: str):
        """
        Reads and evaluates a new ares workflow.

        :param file_path: Path to the workflow *.json file.
        """
        self.file_path = file_path
        self.workflow = self._load_wf()
        self._workflow_validation()
        sinks = self._find_sinks()
        workflow_lin = self._eval_wf(sinks=sinks)
        self._sort_wf(workflow_lin)

    def _load_wf(self) -> dict | None:
        """
        Reads the workflow JSON file and parses it into a dictionary.

        :return: Dictionary representing the workflow, or None on error.
        """
        try:
            with open(self.file_path, 'r', encoding='utf-8') as file:
                wf = json.load(file)
            ares_globals.logfile.write(f"Workflow file {self.file_path} successfully loaded.")
            return wf
        except FileNotFoundError:
            ares_globals.logfile.write(f"Workflow file json file not found at '{self.file_path}'.", level="ERROR")
            return None
        except json.JSONDecodeError as e:
            ares_globals.logfile.write(f"Error parsing workflow file json file '{self.file_path}': {e}", level="ERROR")
            return None
        except Exception as e:
            ares_globals.logfile.write(f"Unexpected error loading workflow file json file '{self.file_path}': {e}", level="ERROR")
            return None

    def _workflow_validation(self):
        """
        Checks whether logical rules in the workflow JSON are followed.
        """
        workflow_schema_path = os.path.join((os.path.dirname(__file__)), 'workflow_schema.json')
        with open(workflow_schema_path , 'r', encoding='utf-8') as schema_file:
            schema = json.load(schema_file)
        
        try:
            validate(instance=self.workflow, schema=schema)
            ares_globals.logfile.write(f"The JSON data in '{self.file_path}' is valid according to schema '{workflow_schema_path}'.", level="INFO")
        except FileNotFoundError:
            log_message = f"Error: One of the files was not found. Please check the paths. Missing file: '{self.file_path}' or '{workflow_schema_path}'."
            ares_globals.logfile.write(log_message, level="ERROR")
        except json.JSONDecodeError as e:
            log_message = f"Error parsing the JSON file '{self.file_path}': {e}"
            ares_globals.logfile.write(log_message, level="ERROR")
        except ValidationError as e:
            log_message = (
                f"Error while syntax validation of the workflow json file '{self.file_path}': "
                f"Message: {e.message}. "
                f"Path: {' -> '.join(map(str, e.path))}. "
                f"Schema Path: {' -> '.join(map(str, e.schema_path))}. "
                f"Invalid Data: {json.dumps(e.instance, indent=2)}"
            )
            ares_globals.logfile.write(log_message, level="ERROR")
        except Exception as e:
            ares_globals.logfile.write(f"Unexpected error during workflow json file validation: {e}", level="ERROR")


    def _find_sinks(self) -> list | None:
        """
        Finds workflow elements that are not referenced as input in any other element.
        
        :return: List of workflow endpoint element keys (sinks).
        """
        try:
            sinks = []

            for primary_key in self.workflow.keys():
                call_count = 0
                
                for secondary_value in self.workflow.values():
                    input = list()

                    if "dataset" in secondary_value:
                        input.extend(secondary_value["dataset"])
                        
                    if "cancel_condition" not in secondary_value:
                        if "input" in secondary_value:
                            input.extend(secondary_value["input"])
                    else:
                        if "init" in secondary_value:
                            input.extend(secondary_value["init"])

                    if input is not None:
                        for input_member in input:
                            if input_member == primary_key:
                                call_count += 1
                                break
                
                if call_count > 0:
                    ares_globals.logfile.write(f"""Workflow element "{primary_key}" is referenced {call_count} time(s) in other workflow elements.""")
                else:
                    ares_globals.logfile.write(f"""Workflow element "{primary_key}" is a workflow endpoint (sink).""")
                    sinks.append(primary_key)

            return sinks
        
        except Exception as e:
            ares_globals.logfile.write(f"Error while searching for sinks: {e}", level="ERROR")
            return None

    def _eval_wf(self, sinks: list) -> list | None:
        """
        Evaluates the linear execution order of the workflow from its endpoints (sinks).

        :param sinks: List of elements that are endpoints of the workflow.
        :return: List of elements in execution order.
        """
        try:
            workflow_lin = []

            for sink in sinks:
                path = self._recursive_search(sink=sink, loop=False, element=sink)
                for step in path:
                    if step not in workflow_lin:
                        workflow_lin.append(step)

            workflow_lin_string = " -> ".join(workflow_lin)
            ares_globals.logfile.write(f"Workflow execution order: {workflow_lin_string}", level="INFO")

            return workflow_lin

        except Exception as e:
            ares_globals.logfile.write(f"Error evaluating the execution order of the linear workflows at element {sink}: {e}", level="ERROR")
            return None

    def _sort_wf(self, workflow_lin: list):
        """
        Sorts the workflow based on the recursive search from _eval_wf.

        :param workflow_lin: List of elements in execution order.
        """
        try:
            workflow_sorted = {}
            for item in workflow_lin:
                if item in self.workflow:
                    workflow_sorted[item] = self.workflow[item]

            self.workflow = workflow_sorted

        except Exception as e:
            ares_globals.logfile.write(f"Error while sorting the workflow: {e}", level="ERROR")

    def _recursive_search(self, sink: str, loop: bool, element: str) -> list | None:
        """
        Recursively collects the execution path starting from a given element and traversing backwards
        via inputs, datasets, and init connections. It also handles cyclic dependencies.

        :param sink: The initial sink (endpoint) element from which the overall workflow evaluation started.
                     This is used to determine if a 'cancel_condition' input should be followed.
        :param loop: A boolean flag indicating whether the current traversal is inside a detected loop.
                     If True, 'input' connections are prioritized. If False, 'init' connections are considered
                     for 'cancel_condition' elements unless the 'sink' itself is in 'input'.
        :param element: The current workflow element (its key) being processed in the recursive search.
                        This is the node from which the trace is currently extending backwards.
        :return: A list representing the execution path from the given element to its sources.
                 Returns None if an infinite loop is detected to propagate the error.
        """

        try:
            path = []
            inputs = []

            elem_data = self.workflow.get(element, {})
            if isinstance(elem_data, dict):
                if "cancel_condition" in elem_data:
                    if sink in elem_data["input"] or loop:
                        if "init" in elem_data:
                            inputs += elem_data["init"]
                    else:
                        loop = True
                        if "input" in elem_data:
                            inputs += elem_data["input"]
                else:
                    if "input" in elem_data:
                        inputs += elem_data["input"]
                if "dataset" in elem_data:
                    inputs += elem_data["dataset"]

            for inp in inputs:
                path += self._recursive_search(sink=sink, loop=loop, element=inp)
                if path is None:
                    return None

            path.append(element)
            return path

        except Exception as e:
            ares_globals.logfile.write(f"Error during recursive path tracing from {element}: {e}", level="ERROR")
            return None

    def write_out(self, file_path: str):
        """
        Writes the current workflow dictionary to a JSON file.

        :param file_path: Path where the JSON file will be saved.
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(self.workflow, file, indent=4, ensure_ascii=False)
            ares_globals.logfile.write(f"Workflow successfully written to {file_path}.")
        except Exception as e:
            ares_globals.logfile.write(f"Error writing workflow to {file_path}: {e}", level="ERROR")



