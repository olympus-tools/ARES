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

from ares.core.logfile import Logfile
from ares.models.workflow_model import WorkflowSchema
import os
import json
from datetime import datetime
from jsonschema import ValidationError
from typeguard import typechecked
from typing import Optional


class Workflow:
    @typechecked
    def __init__(self, file_path: str = None, logfile: Logfile = None):
        """
        Initializes a Workflow object by reading and validating a workflow JSON file.

        Args:
            file_path (str): Path to the workflow JSON file (*.json).
            logfile (Logfile): The logfile object of the current ARES pipeline for logging purposes.
        """
        self.logfile = logfile
        self._file_path = file_path
        self.workflow: Optional[WorkflowSchema] = self._load_and_validate_wf()

    @typechecked
    def _load_and_validate_wf(self) -> Optional[WorkflowSchema]:
        """
        Reads and validates the workflow JSON file using Pydantic.
        The function also performs the sorting and element workflow evaluation.

        Returns:
            Optional[WorkflowSchema]: A Pydantic object representing the workflow,
                                      or None in case of an error.
        """
        try:
            with open(self._file_path, "r", encoding="utf-8") as file:
                workflow_raw = json.load(file)

            # Pydantic-Validierung des rohen Dictionaries
            workflow_raw_pydantic = WorkflowSchema.model_validate(workflow_raw)

            self.logfile.write(
                f"Workflow file {self._file_path} successfully loaded and validated with Pydantic.",
                level="INFO",
            )

            # Verarbeitung des Pydantic-Objekts in der richtigen Reihenfolge
            workflow_sinks = self._find_sinks(workflow=workflow_raw_pydantic)
            workflow_order = self._eval_workflow_order(workflow=workflow_raw_pydantic, wf_sinks=workflow_sinks)
            workflow_sorted_pydantic = self._sort_workflow(workflow_order=workflow_order, workflow=workflow_raw_pydantic)
            workflow = self._eval_element_workflow(workflow=workflow_sorted_pydantic)

            return workflow

        except FileNotFoundError:
            self.logfile.write(
                f"Workflow file not found at '{self._file_path}'.",
                level="ERROR",
            )
            return None
        except json.JSONDecodeError as e:
            self.logfile.write(
                f"Error parsing workflow file '{self._file_path}': {e}",
                level="ERROR",
            )
            return None
        except ValidationError as e:
            self.logfile.write(
                f"Validation error in workflow file '{self._file_path}': {e}",
                level="ERROR",
            )
            return None
        except Exception as e:
            self.logfile.write(
                f"Unexpected error loading workflow file '{self._file_path}': {e}",
                level="ERROR",
            )
            return None

    @typechecked
    def _find_sinks(self, workflow: Optional[WorkflowSchema]) -> list | None:
        """
        Identifies the endpoints (sinks) of the workflow.

        These are elements that are not referenced as `input`, `dataset`, or `init`
        in any other element. They serve as the starting points for the backward
        analysis of the execution order.

        Args:
            workflow (WorkflowSchema): The workflow Pydantic object.

        Returns:
            list | None: A list of strings containing the names of the endpoint elements,
                or `None` in case of an error.
        """
        try:
            wf_sinks = []

            for wf_element_name in workflow.root.keys():
                call_count = 0

                for wf_element_value in workflow.root.values():
                    ref_input_list = []

                    if hasattr(wf_element_value, "parameter") and wf_element_value.parameter is not None:
                        ref_input_list.extend(wf_element_value.parameter)

                    if hasattr(wf_element_value, "cancel_condition") and wf_element_value.cancel_condition is not None:
                        if hasattr(wf_element_value, "init") and wf_element_value.init is not None:
                            ref_input_list.extend(wf_element_value.init)
                    else:
                        if hasattr(wf_element_value, "input") and wf_element_value.input is not None:
                            ref_input_list.extend(wf_element_value.input)

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

    @typechecked
    def _eval_workflow_order(self, workflow: Optional[WorkflowSchema], wf_sinks: list) -> list | None:
        """
        Determines the correct execution order of the workflow elements.

        This is done by recursively searching backward from the sinks to the sources.
        The function logs the determined order.

        Args:
            workflow (WorkflowSchema): The Pydantic workflow object.
            wf_sinks (list): A list of the workflow's endpoint elements.

        Returns:
            list | None: A list of strings containing the elements in their execution
                order, or `None` in case of an error.
        """
        try:
            workflow_order = []

            for wf_sink in wf_sinks:
                path = self._recursive_search(workflow=workflow, sink=wf_sink, loop=False, element=wf_sink)
                if path is None:
                    return None
                for step in path:
                    if step not in workflow_order:
                        workflow_order.append(step)

            workflow_lin_string = " -> ".join(workflow_order)
            self.logfile.write(f"Workflow execution order: {workflow_lin_string}", level="INFO")

            return workflow_order

        except Exception as e:
            self.logfile.write(
                f"Error evaluating the execution order of the linear workflows at element {wf_sink}: {e}",
                level="ERROR",
            )
            return None

    @typechecked
    def _recursive_search(
        self, workflow: Optional[WorkflowSchema], sink: str, loop: bool, element: str
    ) -> list | None:
        """
        Recursively traces the execution path backward from a given element.

        The function follows connections (`input`, `parameter`, `init`, `parameter`) and detects and
        handles cyclic dependencies (`cancel_condition`).

        Args:
            workflow (WorkflowSchema): The complete workflow Pydantic object.
            sink (str): The initial starting element of the overall search. Used to
                differentiate between regular and loop inputs for a `cancel_condition`.
            loop (bool): A boolean flag indicating whether the search is currently inside a loop.
            element (str): The current workflow element (its key) being processed in the
                recursive search.

        Returns:
            list | None: A list representing the backward-traced execution path, or `None`
                if an error occurs (e.g., an infinite loop is detected).
        """
        try:
            path = []
            inputs = []

            elem_obj = workflow.root.get(element)

            if elem_obj is None:
                self.logfile.write(f"Workflow element '{element}' not found.", level="WARNING")
                return []

            if hasattr(elem_obj, "cancel_condition") and elem_obj.cancel_condition is not None:
                if hasattr(elem_obj, "input") and elem_obj.input is not None:
                    if sink in elem_obj.input or loop:
                        if hasattr(elem_obj, "init") and elem_obj.init is not None:
                            inputs.extend(elem_obj.init)
                    else:
                        loop = True
                        inputs.extend(elem_obj.input)
            else:
                if hasattr(elem_obj, "input") and elem_obj.input is not None:
                    inputs.extend(elem_obj.input)

            if hasattr(elem_obj, "parameter") and elem_obj.parameter is not None:
                inputs.extend(elem_obj.parameter)

            for input in inputs:
                path.extend(self._recursive_search(workflow=workflow, sink=sink, loop=loop, element=input))
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

    @typechecked
    def _sort_workflow(self, workflow_order: list, workflow: WorkflowSchema) -> Optional[WorkflowSchema]:
        """
        Sorts the workflow Pydantic object based on the determined execution order.

        Args:
            workflow_order (list): The list of elements in the correct execution order.
            workflow (WorkflowSchema): The unsorted workflow Pydantic object.

        Returns:
            Optional[WorkflowSchema]: A new, sorted workflow Pydantic object, or `None` in case of an error.
        """
        try:
            workflow_sorted_dict = {}
            for item in workflow_order:
                wf_element_obj = workflow.root.get(item)
                if wf_element_obj:
                    workflow_sorted_dict[item] = wf_element_obj

            return WorkflowSchema(root=workflow_sorted_dict)

        except Exception as e:
            self.logfile.write(f"Error while sorting the workflow: {e}", level="ERROR")
            return None

    @typechecked
    def _eval_element_workflow(self, workflow: Optional[WorkflowSchema]) -> Optional[WorkflowSchema]:
        """
        Assigns the workflow from a data source to each workflow element.

        Args:
            workflow (WorkflowSchema): The Pydantic workflow object.

        Returns:
            Optional[WorkflowSchema]: The workflow Pydantic object with the 'element_workflow'
                field populated, or None in case of an error.
        """
        try:
            for wf_element_name, wf_element in workflow.root.items():
                element_workflow = []

                if hasattr(wf_element, "init") and wf_element.init is not None:
                    for init in wf_element.init:
                        init_elem = workflow.root.get(init)
                        if init_elem is not None:
                            element_workflow.extend(init_elem.element_workflow)
                            element_workflow.append(init)

                if hasattr(wf_element, "input") and wf_element.input is not None:
                    for input_name in wf_element.input:
                        input_elem = workflow.root.get(input_name)
                        if input_elem is not None:
                            element_workflow.extend(input_elem.element_workflow)
                            element_workflow.append(input_name)

                if hasattr(wf_element, "parameter") and wf_element.parameter is not None:
                    for param_name in wf_element.parameter:
                        param_elem = workflow.root.get(param_name)
                        if param_elem is not None:
                            element_workflow.extend(param_elem.element_workflow)
                            element_workflow.append(param_name)

                # remove duplicates and store it to the dictionary
                workflow.root[wf_element_name].element_workflow = list(dict.fromkeys(element_workflow))

            return workflow

        except Exception as e:
            self.logfile.write(
                f"Error while evaluating element workflow: {e}", level="ERROR"
            )
            return None

    @typechecked
    def write_out(self, output_path: str):
        """
        Writes the current, processed workflow object to a JSON file.

        Args:
            output_path (str): The path where the workflow should be saved.
        """
        try:
            file_name = os.path.splitext(os.path.basename(self._file_path))[0]
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            new_file_name = f"{file_name}_{timestamp}.json"
            output_file_path = os.path.join(output_path, new_file_name)

            with open(output_file_path, "w", encoding="utf-8") as file:
                file.write(self.workflow.model_dump_json(indent=4, exclude_none=True))

            self.logfile.write(f"Workflow successfully written to {output_file_path}.")
        except Exception as e:
            self.logfile.write(f"Error writing workflow to {output_path}: {e}", level="ERROR")
