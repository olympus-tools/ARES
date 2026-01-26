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

import os
from pathlib import Path
from typing import Annotated, Any

from pydantic import BaseModel, Field, RootModel
from typing_extensions import Literal

# TODO: After thinking about it: in my oppinion, we should think about defining the fields with "paths" that are resolved instead of trying to automatically detect, resolve them
FIELD_IGNORE_LIST = ["vstack_pattern"]


class BaseElement(BaseModel):
    """Base model for all workflow elements."""

    type: str
    element_workflow: list[str] = []
    hash_list: dict[str, list[str]] = {}


class DataElement(BaseElement):
    type: Literal["data"] = "data"
    mode: Literal["read", "write"]
    file_path: list[str] | None = []
    input: list[str] | None = []
    label_filter: list[str] | None = None
    vstack_pattern: list[str] | None = None
    output_format: Literal["mf4"] | None = None
    stepsize: int | None = None

    class Config:
        extra = "forbid"

    def validate_mode_requirements(self):
        """Validates that required fields are present based on the mode."""
        if self.mode == "read" and not self.file_path:
            raise ValueError("Field 'file_path' is required for mode='read'.")
        if self.mode == "write" and (
            (not self.input or not self.output_format) or (self.vstack_pattern)
        ):
            raise ValueError(
                "Fields 'input' and 'output_format' are required for mode='write'. Additional 'vstack_pattern' can only be used in mode='input'."
            )


class ParameterElement(BaseElement):
    type: Literal["parameter"] = "parameter"
    mode: Literal["read", "write"]
    file_path: list[str] | None = []
    parameter: list[str] | None = []
    label_filter: list[str] | None = None
    output_format: Literal["json", "dcm"] | None = None

    class Config:
        extra = "forbid"

    def validate_mode_requirements(self):
        """Validates that required fields are present based on the mode."""
        if self.mode == "read" and not self.file_path:
            raise ValueError("Field 'file_path' is required for mode='read'.")
        if self.mode == "write" and (not self.parameter or not self.output_format):
            raise ValueError(
                "Fields 'input' and 'output_format' are required for mode='write'."
            )


class PluginElement(BaseElement):
    type: Literal["plugin"] = "plugin"
    file_path: str
    plugin_name: str | None = None

    class Config:
        extra = "allow"


class SimUnitElement(PluginElement):
    type: Literal["sim_unit"] = "sim_unit"
    plugin_path: str = Field(
        default_factory=lambda: os.path.relpath(
            Path(__file__).parent.parent / "plugins" / "simunit.py",
            Path(__file__).parent,
        )
    )
    file_path: str
    stepsize: int
    input: list[str] | None = []
    parameter: list[str] | None = []
    data_dictionary: str
    init: list[str] | None = []
    cancel_condition: str | None = None

    class Config:
        extra = "forbid"


WorkflowElement = Annotated[
    DataElement | ParameterElement | SimUnitElement | PluginElement,
    Field(discriminator="type"),
]


# TODO: don't add this extra methods => userdict???
class WorkflowModel(RootModel):
    root: dict[str, WorkflowElement]

    def __getitem__(self, key: str) -> WorkflowElement:
        return self.root[key]

    def __setitem__(self, key: str, value: WorkflowElement) -> None:
        self.root[key] = value

    def __delitem__(self, key: str) -> None:
        del self.root[key]

    def __iter__(self):
        return iter(self.root)

    def __len__(self) -> int:
        return len(self.root)

    def items(self):
        return self.root.items()

    def values(self):
        return self.root.values()

    def keys(self):
        return self.root.keys()

    def get(self, key: str, default: Any = None):
        """Get an item from the workflow.

        Args:
            key (str): The key to look up.
            default (Any): The default value if key is not found.

        Returns:
            WorkflowElement | Any: The found element or the default value.
        """
        return self.root.get(key, default)

    def model_dump_json(self, **kwargs) -> str:
        """Dump workflow JSON as string."""
        return super().model_dump_json(**kwargs)
