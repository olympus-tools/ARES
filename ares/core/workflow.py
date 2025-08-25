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
from ares.models.workflow_model import WorkflowModel
import os
import re
import json
from datetime import datetime
from jsonschema import ValidationError
from typeguard import typechecked


class Workflow:
    @typechecked
    def __init__(self, file_path: str = None, logfile: Logfile = None):
        """
        Initializes a Workflow object by reading and validating a workflow JSON file.

        Args:
            file_path (str): Path to the workflow JSON file (*.json).
            logfile (Logfile): The logfile object of the current ARES pipeline for logging purposes.
        """
        self._logfile = logfile
        self._file_path = file_path
        self.workflow: WorkflowModel = self._load_and_validate_wf()
        self._evaluate_relative_paths()
        workflow_sinks = self._find_sinks()
        workflow_order = self._eval_workflow_order(wf_sinks=workflow_sinks)
        self._sort_workflow(workflow_order=workflow_order)
        self._eval_element_workflow()

    @typechecked
    def _load_and_validate_wf(self) -> WorkflowModel | None:
        """
        Reads and validates the workflow JSON file using Pydantic.
        The function also performs the sorting and element workflow evaluation.

        Returns:
            WorkflowModel | None: A Pydantic object representing the workflow,
                                      or None in case of an error.
        """
        try:
            with open(self._file_path, "r", encoding="utf-8") as file:
                workflow_raw = json.load(file)

            # Pydantic-Validierung des rohen Dictionaries
            workflow_raw_pydantic = WorkflowModel.model_validate(workflow_raw)

            self._logfile.write(
                f"Workflow file {self._file_path} successfully loaded and validated with Pydantic.",
                level="INFO",
            )
            return workflow_raw_pydantic

        except FileNotFoundError:
            self._logfile.write(
                f"Workflow file not found at '{self._file_path}'.",
                level="ERROR",
            )
            return None
        except json.JSONDecodeError as e:
            self._logfile.write(
                f"Error parsing workflow file '{self._file_path}': {e}",
                level="ERROR",
            )
            return None
        except ValidationError as e:
            self._logfile.write(
                f"Validation error in workflow file '{self._file_path}': {e}",
                level="ERROR",
            )
            return None
        except Exception as e:
            self._logfile.write(
                f"Unexpected error loading workflow file '{self._file_path}': {e}",
                level="ERROR",
            )
            return None

    @typechecked
    def _evaluate_relative_paths(self):
        """Convert all relative file paths in workflow elements to absolute paths.

        This method iterates over all workflow elements and inspects each of their fields.
        If a field contains a string or a list of strings that appear to be file paths,
        it converts any relative paths into absolute paths based on the directory of the
        workflow JSON file (`self._file_path`). Absolute paths are left unchanged.
        """
        try:
            base_dir = os.path.dirname(os.path.abspath(self._file_path))
            path_eval_pattern = r"\.[a-zA-Z0-9]+$"

            for wf_element_name, wf_element_value in self.workflow.items():
                for field_name, field_value in wf_element_value.__dict__.items():
                    if field_value is None:
                        continue

                    # Case 1: single string
                    if isinstance(field_value, str):
                        if (("/" in field_value or "\\" in field_value or
                            re.search(path_eval_pattern, field_value) is not None)):
                            if not os.path.isabs(field_value):
                                abs_path = os.path.abspath(os.path.join(base_dir, field_value))
                                setattr(wf_element_value, field_name, abs_path)
                                self._logfile.write(
                                    f"Resolved relative path for '{wf_element_name}.{field_name}': {abs_path}",
                                    level="INFO",
                                )

                    # Case 2: list of strings
                    elif isinstance(field_value, list) and all(isinstance(x, str) for x in field_value):
                        abs_paths = []
                        changed = False
                        for path in field_value:
                            if ("/" in path or "\\" in path or
                                re.search(path_eval_pattern, path) is not None):
                                if not os.path.isabs(path):
                                    abs_paths.append(os.path.abspath(os.path.join(base_dir, path)))
                                    changed = True
                                else:
                                    abs_paths.append(path)
                            else:
                                abs_paths.append(path)

                        if changed:
                            setattr(wf_element_value, field_name, abs_paths)
                            self._logfile.write(
                                f"Resolved relative paths for '{wf_element_name}.{field_name}': {abs_paths}",
                                level="INFO",
                            )

        except Exception as e:
            self._logfile.write(
                f"Error evaluating relative paths: {e}",
                level="ERROR",
            )

    @typechecked
    def _find_sinks(self) -> list | None:
        """
        Identifies the endpoints (sinks) of the workflow.

        These are elements that are not referenced as `input`, `dataset`, or `init`
        in any other element. They serve as the starting points for the backward
        analysis of the execution order.

        Returns:
            list | None: A list of strings containing the names of the endpoint elements,
                or `None` in case of an error.
        """
        try:
            wf_sinks = []

            for wf_element_name in self.workflow.keys():
                call_count = 0

                for wf_element_value in self.workflow.values():
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
                    self._logfile.write(
                        f"""Workflow element "{wf_element_name}" is referenced {call_count} time(s) in other workflow elements."""
                    )
                else:
                    self._logfile.write(
                        f"""Workflow element "{wf_element_name}" is a workflow endpoint (sink)."""
                    )
                    wf_sinks.append(wf_element_name)

            return wf_sinks

        except Exception as e:
            self._logfile.write(f"Error while searching for sinks: {e}", level="ERROR")
            return None

    @typechecked
    def _eval_workflow_order(self, wf_sinks: list) -> list | None:
        """
        Determines the correct execution order of the workflow elements.

        This is done by recursively searching backward from the sinks to the sources.
        The function logs the determined order.

        Args:
            wf_sinks (list): A list of the workflow's endpoint elements.

        Returns:
            list | None: A list of strings containing the elements in their execution
                order, or `None` in case of an error.
        """
        try:
            workflow_order = []

            for wf_sink in wf_sinks:
                path = self._recursive_search(sink=wf_sink, loop=False, element=wf_sink)
                if path is None:
                    return None
                for step in path:
                    if step not in workflow_order:
                        workflow_order.append(step)

            workflow_lin_string = " -> ".join(workflow_order)
            self._logfile.write(f"Workflow execution order: {workflow_lin_string}", level="INFO")

            return workflow_order

        except Exception as e:
            self._logfile.write(
                f"Error evaluating the execution order of the linear workflows at element {wf_sink}: {e}",
                level="ERROR",
            )
            return None

    @typechecked
    def _recursive_search(self, sink: str, loop: bool, element: str) -> list | None:
        """
        Recursively traces the execution path backward from a given element.

        The function follows connections (`input`, `parameter`, `init`, `parameter`) and detects and
        handles cyclic dependencies (`cancel_condition`).

        Args:
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

            elem_obj = self.workflow.get(element)

            if elem_obj is None:
                self._logfile.write(f"Workflow element '{element}' not found.", level="WARNING")
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
                path.extend(self._recursive_search(sink=sink, loop=loop, element=input))
                if path is None:
                    return None

            path.append(element)
            return path

        except Exception as e:
            self._logfile.write(
                f"Error during recursive path tracing from {element}: {e}",
                level="ERROR",
            )
            return None

    @typechecked
    def _sort_workflow(self, workflow_order: list):
        """
        Sorts the workflow Pydantic object based on the determined execution order.

        Args:
            workflow_order (list): The list of elements in the correct execution order.
        """
        try:
            workflow_sorted_dict = {}
            for item in workflow_order:
                wf_element_obj = self.workflow.get(item)
                if wf_element_obj:
                    workflow_sorted_dict[item] = wf_element_obj

            self.workflow = WorkflowModel(root=workflow_sorted_dict)

        except Exception as e:
            self._logfile.write(f"Error while sorting the workflow: {e}", level="ERROR")

    @typechecked
    def _eval_element_workflow(self):
        """
        Assigns the workflow from a data source to each workflow element.
        """
        try:
            for wf_element_name, wf_element in self.workflow.items():
                element_workflow = []

                if hasattr(wf_element, "init") and wf_element.init is not None:
                    for init in wf_element.init:
                        init_elem = self.workflow.get(init)
                        if init_elem is not None:
                            element_workflow.extend(init_elem.element_workflow)
                            element_workflow.append(init)

                if hasattr(wf_element, "input") and wf_element.input is not None:
                    for input_name in wf_element.input:
                        input_elem = self.workflow.get(input_name)
                        if input_elem is not None:
                            element_workflow.extend(input_elem.element_workflow)
                            element_workflow.append(input_name)

                if hasattr(wf_element, "parameter") and wf_element.parameter is not None:
                    for param_name in wf_element.parameter:
                        param_elem = self.workflow.get(param_name)
                        if param_elem is not None:
                            element_workflow.extend(param_elem.element_workflow)
                            element_workflow.append(param_name)

                # remove duplicates and store it to the dictionary
                self.workflow[wf_element_name].element_workflow = list(dict.fromkeys(element_workflow))

        except Exception as e:
            self._logfile.write(
                f"Error while evaluating element workflow: {e}", level="ERROR"
            )

    @typechecked
    def write_out(self, output_path: str):
        """
        Writes the current, processed workflow object to a JSON file.

        Args:
            output_path (str): The path where the workflow should be saved.
        """
        try:
            output_file_path = self._eval_output_path(dir_path=output_path, output_format='json')

            with open(output_file_path, "w", encoding="utf-8") as file:
                file.write(self.workflow.model_dump_json(indent=4, exclude_none=True))

            self._logfile.write(f"File successfully written to {output_file_path}.")
        except Exception as e:
            self._logfile.write(f"Error writing workflow to {output_file_path}: {e}", level="ERROR")

    @typechecked
    def _eval_output_path(self, dir_path: str, output_format: str) -> str | None:
        """
        Adds a timestamp to the filename and returns a complete, absolute file path to prevent overwriting.

        The format is `*_YYYYMMDD_HHMMSS*` before the file extension.

        Args:
            dir_path (str): The absolute path to the output directory.
            output_format (str): The desired file extension (e.g., 'mf4'). The leading dot is added automatically.

        Returns:
            str | None: The new, complete file path with a timestamp, or `None` if an error occurs.
        """
        try:
            os.makedirs(dir_path, exist_ok=True)
            file_name = os.path.splitext(os.path.basename(self._file_path))[0]
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            new_file_name = f"{file_name}_{timestamp}.{output_format}"
            full_path = os.path.join(dir_path, new_file_name)
            return full_path

        except Exception as e:
            self._logfile.write(
                f"Evaluation of data output name failed: {e}", level="ERROR"
            )
            return None
