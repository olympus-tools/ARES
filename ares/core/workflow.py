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

Copyright 2025 olympus-tools contributors. Contributors to this project
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

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic_core import ValidationError

from ares.pydantic_models.workflow_model import WorkflowModel
from ares.utils.decorators import error_msg, safely_run
from ares.utils.decorators import typechecked_dev as typechecked
from ares.utils.logger import create_logger

logger = create_logger(__name__)


class Workflow:
    """Manages the loading, validation, and processing of workflow files."""

    @typechecked
    def __init__(
        self,
        file_path: Path,
    ):
        """Initializes a Workflow object by reading and validating a workflow JSON file.

        Args:
            file_path (Path): Path to the workflow JSON file (*.json).
        """
        self._file_path: Path = file_path
        self.workflow: WorkflowModel = self._load_and_validate_wf()
        self._evaluate_relative_paths()
        self.workflow_sinks: list[str] = self._find_sinks()
        self.workflow_order: list[str] = self._eval_workflow_order()
        self._sort_workflow()
        self._eval_element_workflow()

    @error_msg(
        exception_msg="Unexpected error loading workflow file.",
        exception_map={
            FileNotFoundError: "Workflow file not found",
            json.JSONDecodeError: "Error parsing workflow file",
            ValidationError: "Pydantic validation error in workflow file",
        },
        log=logger,
        instance_el=["_file_path"],
    )
    @typechecked
    def _load_and_validate_wf(self) -> WorkflowModel:
        """Reads and validates the workflow JSON file using Pydantic.

        Returns:
            WorkflowModel: A Pydantic object representing the workflow.
        """
        with open(str(self._file_path), "r", encoding="utf-8") as file:
            workflow_raw = json.load(file)

        workflow_raw_pydantic = WorkflowModel.model_validate(workflow_raw)

        logger.info(
            f"Workflow file {self._file_path} successfully loaded and validated.",
        )
        return workflow_raw_pydantic

    @error_msg(
        exception_msg="Error evaluating relative paths in workflow file.",
        log=logger,
        instance_el=["_file_path"],
    )
    @typechecked
    def _evaluate_relative_paths(self) -> None:
        """Converts all relative file paths in workflow elements to absolute paths.

        This method iterates over all workflow elements and inspects each of their fields.
        If a field contains a Path or a list of Paths that appear to be file paths,
        it converts any relative paths into absolute paths based on the directory of the
        workflow JSON file (`self._file_path`). Absolute paths are left unchanged.
        """
        base_dir = self._file_path.parent
        path_eval_pattern = r"\.[a-zA-Z0-9]+$"

        # TODO: make relative path evaluation easier and more intuitive

        for wf_element_name, wf_element_value in self.workflow.items():
            for field_name, field_value in wf_element_value.__dict__.items():
                # Case 1: single Path
                if isinstance(field_value, Path):
                    field_value = str(field_value)
                    if (
                        "/" in field_value_str
                        or "\\" in field_value_str
                        or re.search(path_eval_pattern, field_value_str) is not None
                    ):
                        if not field_value.is_absolute():
                            abs_path = (base_dir / field_value).resolve()
                            setattr(wf_element_value, field_name, abs_path)
                            logger.debug(
                                f"Resolved relative path in workflow file for '{wf_element_name}.{field_name}': {abs_path}",
                            )

                # Case 2: list of Paths
                elif isinstance(field_value, list) and all(
                    isinstance(x, Path) for x in field_value
                ):
                    abs_paths = []
                    changed = False
                    for path in field_value:
                        path = str(path)
                        if (
                            "/" in path_str
                            or "\\" in path_str
                            or re.search(path_eval_pattern, path_str) is not None
                        ):
                            if not path.is_absolute():
                                abs_paths.append((base_dir / path).resolve())
                                changed = True
                            else:
                                abs_paths.append(path)
                        else:
                            abs_paths.append(path)

                    if changed:
                        setattr(wf_element_value, field_name, abs_paths)
                        logger.debug(
                            f"Resolved relative paths in workflow file for '{wf_element_name}.{field_name}': {abs_paths}",
                        )

    @error_msg(
        exception_msg="Error while searching workflow sinks.",
        log=logger,
        instance_el=["_file_path"],
    )
    @typechecked
    def _find_sinks(self) -> list[str]:
        """Identifies the endpoints (sinks) of the workflow.

        These are elements that are not referenced as `input`, `dataset`, or `init`
        in any other element. They serve as the starting points for the backward
        analysis of the execution order.

        Returns:
            list[str]: A list of strings containing the names of the endpoint elements.
        """
        wf_sinks: list[str] = []
        ref_input_list: list[str] = []

        # loop searches all referenced elements from workflow-json
        for wf_element_value in self.workflow.values():
            if hasattr(wf_element_value, "parameter") and wf_element_value.parameter:
                ref_input_list.extend(wf_element_value.parameter)
            if (
                hasattr(wf_element_value, "cancel_condition")
                and wf_element_value.cancel_condition
            ):
                if hasattr(wf_element_value, "init") and wf_element_value.init:
                    ref_input_list.extend(wf_element_value.init)
            else:
                if hasattr(wf_element_value, "input") and wf_element_value.input:
                    ref_input_list.extend(wf_element_value.input)

        # referenced elements MUST NOT be sinks
        possible_sinks = [
            wf_element_name
            for wf_element_name in self.workflow.keys()
            if wf_element_name not in set(ref_input_list)
        ]

        # validate possible-sinks
        for sink in possible_sinks:
            wf_element_value = self.workflow.get(sink)

            if (
                hasattr(wf_element_value, "parameter")
                and not wf_element_value.parameter
            ) and (hasattr(wf_element_value, "input") and not wf_element_value.input):
                logger.debug(
                    f"""Workflow element "{sink}" is a unused workflow source."""
                )
            else:
                logger.debug(
                    f"""Workflow element "{sink}" is a workflow endpoint (sink)."""
                )
                wf_sinks.append(sink)

        return wf_sinks

    @error_msg(
        exception_msg="Error during evaluation of the execution order of the workflow.",
        log=logger,
        instance_el=["_file_path"],
    )
    @typechecked
    def _eval_workflow_order(self) -> list[str]:
        """Determines the correct execution order of the workflow elements.

        This is done by recursively searching backward from the sinks to the sources.
        The function logs the determined order.

        Returns:
            list[str]: A list of strings containing the elements in their execution
                order.
        """
        workflow_order: list[str] = []

        for wf_sink in self.workflow_sinks:
            path = self._recursive_search(sink=wf_sink, loop=False, element=wf_sink)
            if path is None:
                logger.error(
                    f"Failed to determine execution path for sink '{wf_sink}'.",
                )
                raise
            for step in path:
                if step not in workflow_order:
                    workflow_order.append(step)

        workflow_lin_string = " -> ".join(workflow_order)
        logger.info(
            f"Workflow execution order: {workflow_lin_string}",
        )

        return workflow_order

    @error_msg(
        exception_msg="Error during recursive dependency search in workflow.",
        log=logger,
        instance_el=["_file_path"],
    )
    @typechecked
    def _recursive_search(
        self, sink: str, loop: bool, element: str
    ) -> list[str] | None:
        """Recursively traces the execution path backward from a given element.

        The function follows connections (`input`, `parameter`, `init`, `parameter`) and detects and
        handles cyclic dependencies (`cancel_condition`).

        Args:
            sink (str): The initial starting element of the overall search. Used to
                differentiate between regular and loop inputs for a `cancel_condition`.
            loop (bool): A boolean flag indicating whether the search is currently inside a loop.
            element (str): The current workflow element (its key) being processed in the
                recursive search.

        Returns:
            list[str] | None: A list representing the backward-traced execution path, or `None`
                if an error occurs (e.g., an infinite loop is detected).
        """
        path: list[str] = []
        inputs: list[str] = []

        if self.workflow is None:
            return None

        elem_obj = self.workflow.get(element)

        if elem_obj is None:
            logger.warning(
                f"Workflow element '{element}' not found.",
            )
            return []

        if hasattr(elem_obj, "parameter") and elem_obj.parameter:
            inputs.extend(elem_obj.parameter)

        if hasattr(elem_obj, "cancel_condition") and elem_obj.cancel_condition:
            if hasattr(elem_obj, "input") and elem_obj.input:
                if sink in elem_obj.input or loop:
                    if hasattr(elem_obj, "init") and elem_obj.init:
                        inputs.extend(elem_obj.init)
                else:
                    loop = True
                    inputs.extend(elem_obj.input)
        else:
            if hasattr(elem_obj, "input") and elem_obj.input:
                inputs.extend(elem_obj.input)

        for input_name in inputs:
            sub_path = self._recursive_search(sink=sink, loop=loop, element=input_name)
            if sub_path is None:
                return None
            path.extend(sub_path)

        path.append(element)
        return path

    @error_msg(
        exception_msg="Error while sorting the workflow elements.",
        log=logger,
        instance_el=["_file_path"],
    )
    @typechecked
    def _sort_workflow(self) -> None:
        """Sorts the workflow Pydantic object based on the determined execution order."""
        workflow_sorted_dict: dict[str, Any] = {}
        for item in self.workflow_order:
            wf_element_obj = self.workflow.get(item)
            if wf_element_obj:
                workflow_sorted_dict[item] = wf_element_obj

        self.workflow = WorkflowModel(root=workflow_sorted_dict)

    @safely_run(
        default_return=None,
        exception_msg="Evaluating individual wf-element workflow has not been successful.",
        log=logger,
        instance_el=["_file_path"],
    )
    @typechecked
    def _eval_element_workflow(self) -> None:
        """Assigns the workflow from a data source to each workflow element."""
        for wf_element_name, wf_element in self.workflow.items():
            element_workflow: list[str] = []

            if hasattr(wf_element, "parameter") and wf_element.parameter:
                for param_name in wf_element.parameter:
                    param_elem = self.workflow.get(param_name)
                    if param_elem:
                        element_workflow.extend(param_elem.element_workflow)
                        element_workflow.append(param_name)

            if hasattr(wf_element, "init") and wf_element.init:
                for init_name in wf_element.init:
                    init_elem = self.workflow.get(init_name)
                    if init_elem:
                        element_workflow.extend(init_elem.element_workflow)
                        element_workflow.append(init_name)

            elif hasattr(wf_element, "input") and wf_element.input:
                for input_name in wf_element.input:
                    input_elem = self.workflow.get(input_name)
                    if input_elem:
                        element_workflow.extend(input_elem.element_workflow)
                        element_workflow.append(input_name)

            self.workflow[wf_element_name].element_workflow = list(
                dict.fromkeys(element_workflow)
            )

    @safely_run(
        default_return=None,
        exception_msg="Error writing workflow result to json file.",
        log=logger,
        include_args=["output_dir"],
        instance_el=["_file_path"],
    )
    @typechecked
    def save(self, output_dir: Path) -> None:
        """Writes the current, processed workflow object to a JSON file.

        Args:
            output_dir (Path): The path where the workflow should be saved.
        """
        output_file_path = self._eval_output_path(
            dir_path=output_dir, output_format="json"
        )

        with open(output_file_path, "w", encoding="utf-8") as file:
            file.write(self.workflow.model_dump_json(indent=4, exclude_none=True))

        logger.info(f"Workflow output file successfully written to {output_file_path}.")

    @safely_run(
        default_return=None,
        exception_msg="Evaluation of workflow output file name failed",
        log=logger,
        include_args=["dir_path", "output_format"],
        instance_el=["_file_path"],
    )
    @typechecked
    def _eval_output_path(self, dir_path: Path, output_format: str) -> Path:
        """Adds a timestamps to the filename and returns a complete, absolute file path.

        The timestamps prevents overwriting. The format is `*_YYYYMMDD_HHMMSS*` before
        the file extension.

        Args:
            dir_path (Path): The absolute path to the output directory.
            output_format (str): The desired file extension (e.g., 'mf4'). The leading dot
                is added automatically.

        Returns:
            Path: The new, complete file path with a timestamps.
        """
        dir_path.mkdir(parents=True, exist_ok=True)
        file_name = self._file_path.stem
        timestamps = datetime.now().strftime("%Y%m%d%H%M%S")
        new_file_name = f"{file_name}_{timestamps}.{output_format}"
        full_path = dir_path / new_file_name
        return full_path
