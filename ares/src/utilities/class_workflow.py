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

import os
import json
from datetime import datetime
from jsonschema import validate, ValidationError
from .class_logfile import Logfile


class Workflow:
    def __init__(self, file_path: str = None, logfile: Logfile = None):
        """
        Initializes a Workflow object by reading and validating a workflow JSON file.

        :param file_path: Path to the workflow JSON file (*.json).
        :param logfile: The logfile object of the current ARES pipeline for logging purposes.
        :return: None. The initialization fills the instance variables `self.workflow` and `self.logfile`.
        """
        self.logfile = logfile
        self.workflow = self._load_wf(file_path=file_path)

    def _load_wf(self, file_path: str) -> dict | None:
        """
        Reads, validates, and processes the workflow JSON file.
        The function validates the JSON structure, identifies the endpoints (sinks),
        determines the execution order, and evaluates the original data sources.
        Errors are written to the logfile.

        :param file_path: Path to the workflow JSON file.
        :return: A dictionary representing the processed and sorted workflow,
                or None in case of an error.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                workflow_raw = json.load(file)
            self._workflow_validation(workflow=workflow_raw, file_path=file_path)
            workflow_sinks = self._find_sinks(workflow=workflow_raw)
            workflow_order = self._eval_workflow_order(
                workflow=workflow_raw, wf_sinks=workflow_sinks
            )
            workflow = self._sort_workflow(
                workflow_order=workflow_order, workflow=workflow_raw
            )
            workflow = self._eval_element_workflow(workflow=workflow)
            self.logfile.write(f"Workflow file {file_path} successfully loaded.")
            return workflow

        except FileNotFoundError:
            self.logfile.write(
                f"Workflow file json file not found at '{file_path}'.",
                level="ERROR",
            )
            return None
        except json.JSONDecodeError as e:
            self.logfile.write(
                f"Error parsing workflow file json file '{file_path}': {e}",
                level="ERROR",
            )
            return None
        except Exception as e:
            self.logfile.write(
                f"Unexpected error loading workflow file json file '{file_path}': {e}",
                level="ERROR",
            )
            return None

    def _workflow_validation(self, workflow: dict, file_path: str):
        """
        Checks the syntax and logical rules of the workflow against a JSON schema.
        The function writes a success or failure message to the logfile based on the
        validation result. If validation fails, the error is logged in detail.

        :param workflow: The workflow dictionary to be validated.
        :param file_path: Path to the workflow JSON file (used for error messages).
        :return: None. The function does not return a value but logs the validation status.
        """
        try:
            workflow_schema_path = os.path.join(
                (os.path.dirname(__file__)), "workflow_schema.json"
            )
            with open(workflow_schema_path, "r", encoding="utf-8") as schema_file:
                schema = json.load(schema_file)

            validate(instance=workflow, schema=schema)
            self.logfile.write(
                f"The JSON data in '{file_path}' is valid according to schema '{workflow_schema_path}'.",
                level="INFO",
            )
        except FileNotFoundError:
            log_message = f"Error: One of the files was not found. Please check the paths. Missing file: '{file_path}' or '{workflow_schema_path}'."
            self.logfile.write(log_message, level="ERROR")
        except json.JSONDecodeError as e:
            log_message = f"Error parsing the JSON file '{file_path}': {e}"
            self.logfile.write(log_message, level="ERROR")
        except ValidationError as e:
            log_message = (
                f"Error while syntax validation of the workflow json file '{file_path}': "
                f"Message: {e.message}. "
                f"Path: {' -> '.join(map(str, e.path))}. "
                f"Schema Path: {' -> '.join(map(str, e.schema_path))}. "
                f"Invalid Data: {json.dumps(e.instance, indent=2)}"
            )
            self.logfile.write(log_message, level="ERROR")
        except Exception as e:
            self.logfile.write(
                f"Unexpected error during workflow json file validation: {e}",
                level="ERROR",
            )

    def _find_sinks(self, workflow: dict) -> list | None:
        """
        Identifies the endpoints (sinks) of the workflow—elements that are not
        referenced as `input`, `dataset`, or `init` in any other element. These
        sinks serve as the starting points for the backward analysis of the
        execution order.

        :param workflow: The workflow dictionary.
        :return: A list of strings containing the names of the endpoint elements,
                or None in case of an error.
        """
        try:
            wf_sinks = []

            for wf_element_name in workflow.keys():
                call_count = 0

                for wf_element_value in workflow.values():
                    ref_input_list = []

                    if "dataset" in wf_element_value:
                        ref_input_list.extend(wf_element_value["dataset"])

                    if "cancel_condition" not in wf_element_value:
                        if "input" in wf_element_value:
                            ref_input_list.extend(wf_element_value["input"])
                    else:
                        if "init" in wf_element_value:
                            ref_input_list.extend(wf_element_value["init"])

                    if ref_input_list is not None:
                        for ref_input_list_member in ref_input_list:
                            if ref_input_list_member == wf_element_name:
                                call_count += 1
                                break

                if call_count > 0:
                    self.logfile.write(
                        f"""Workflow element "{wf_element_name}" is referenced {call_count} time(s) in other workflow elements."""
                    )
                else:
                    self.logfile.write(
                        f"""Workflow element "{wf_element_name}" is a workflow endpoint (sink)."""
                    )
                    wf_sinks.append(wf_element_name)

            return wf_sinks

        except Exception as e:
            self.logfile.write(f"Error while searching for sinks: {e}", level="ERROR")
            return None

    def _eval_workflow_order(self, workflow: dict, wf_sinks: list) -> list | None:
        """
        Determines the correct execution order of the workflow elements by
        recursively searching backward from the sinks to the sources. The
        function logs the determined order.

        :param workflow: The workflow dictionary.
        :param wf_sinks: A list of the workflow's endpoint elements.
        :return: A list of strings containing the elements in their execution
                order, or None in case of an error.
        """
        try:
            workflow_order = []

            for wf_sink in wf_sinks:
                path = self._recursive_search(
                    workflow=workflow, sink=wf_sink, loop=False, element=wf_sink
                )
                for step in path:
                    if step not in workflow_order:
                        workflow_order.append(step)

            workflow_lin_string = " -> ".join(workflow_order)
            self.logfile.write(
                f"Workflow execution order: {workflow_lin_string}", level="INFO"
            )

            return workflow_order

        except Exception as e:
            self.logfile.write(
                f"Error evaluating the execution order of the linear workflows at element {wf_sink}: {e}",
                level="ERROR",
            )
            return None

    def _recursive_search(
        self, workflow: dict, sink: str, loop: bool, element: str
    ) -> list | None:
        """
        Recursively traces the execution path backward from a given element,
        following connections (`input`, `dataset`, `init`). The function also
        detects and handles cyclic dependencies (`cancel_condition`).

        :param workflow: The complete workflow dictionary.
        :param sink: The initial starting element of the overall search. This is used
                    to differentiate between regular and loop inputs for a `cancel_condition`.
        :param loop: A boolean flag indicating whether the search is currently inside a loop.
        :param element: The current workflow element (its key) being processed in the
                        recursive search.
        :return: A list representing the backward-traced execution path, or None if an
                error occurs (e.g., an infinite loop is detected).
        """

        try:
            path = []
            inputs = []

            elem_data = workflow.get(element, {})
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
                path += self._recursive_search(
                    workflow=workflow, sink=sink, loop=loop, element=inp
                )
                if path is None:
                    return None

            path.append(element)
            return path

        except Exception as e:
            self.logfile.write(
                f"Error during recursive path tracing from {element}: {e}",
                level="ERROR",
            )
            return None

    def _sort_workflow(self, workflow_order: list, workflow: dict) -> dict | None:
        """
        Sorts the original workflow dictionary based on the determined execution order.

        :param workflow_order: The list of elements in the correct execution order.
        :param workflow: The unsorted workflow dictionary.
        :return: A new, sorted workflow dictionary, or None in case of an error.
        """
        try:
            workflow_sorted = {}
            for item in workflow_order:
                if item in workflow:
                    workflow_sorted[item] = workflow[item]

            return workflow_sorted

        except Exception as e:
            self.logfile.write(f"Error while sorting the workflow: {e}", level="ERROR")
            return None

    def _eval_element_workflow(self, workflow: dict) -> dict | None:
        """
        Assigns the workflow from a data source to each workflow element. The function
        iterates through the workflow and determines which 'input', 'init' and 'parameter'
        elements provide the initial input for each element.

        :param workflow: The workflow dictionary.
        :return: The updated workflow dictionary, which now includes an
                `element_workflow` list for each element, or None in case of an error.
        """
        try:
            for wf_element_name, wf_element in workflow.items():
                element_workflow = []

                if "init" in wf_element:
                    for init in wf_element["init"]:
                        element_workflow.extend(workflow[init]["element_workflow"])
                        element_workflow.append(init)
                elif "input" in wf_element:
                    for input in wf_element["input"]:
                        element_workflow.extend(workflow[input]["element_workflow"])
                        element_workflow.append(input)

                if "dataset" in wf_element:
                    for dataset in wf_element["dataset"]:
                        element_workflow.extend(workflow[dataset]["element_workflow"])
                        element_workflow.append(dataset)

                # remove duplicates and store it to workflow
                workflow[wf_element_name]["element_workflow"] = []
                unique_items = set()
                for item in element_workflow:
                    if item not in unique_items:
                        workflow[wf_element_name]["element_workflow"].append(item)
                        unique_items.add(item)

            self.logfile.write(
                "Workflow for each element evaluated successfully.", level="INFO"
            )
            return workflow
        except Exception as e:
            self.logfile.write(
                f"Error while evaluating element workflow: {e}", level="ERROR"
            )
            return None

    def write_out(self, file_path: str):
        """
        Writes the current, processed workflow dictionary to a JSON file.
        The file is saved in the same directory as the original file, with a
        timestamp appended to the filename.

        :param file_path: The path where the workflow should be saved.
        :return: None. The function performs a file write operation.
        """
        try:
            dir_name, file_name = os.path.split(file_path)
            file_name, file_extension = os.path.splitext(file_name)
            file_out_name = (
                f"{file_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}{file_extension}"
            )
            file_path = os.path.join(dir_name, file_out_name)

            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(self.workflow, file, indent=4, ensure_ascii=False)
            self.logfile.write(f"Workflow successfully written to {file_path}.")
        except Exception as e:
            self.logfile.write(
                f"Error writing workflow to {file_path}: {e}", level="ERROR"
            )
