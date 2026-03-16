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

import os
import re
from pathlib import Path
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, RootModel, model_validator
from typing_extensions import Literal


class BaseElement(BaseModel):
    """Base model for all workflow elements."""

    element_workflow: list[str] = []
    hash_list: dict[str, list[str]] = {}


class VStackPatternElement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pattern: str
    signal_name: str | int | None = None
    x_axis: int | None = None
    y_axis: int | None = None

    @model_validator(mode="after")
    def _validate_model(self):
        """Validates that required fields are present based on the given pattern (number of groups)."""
        pattern = re.compile(self.pattern)

        if pattern.groups >= 3:
            if (
                isinstance(self.signal_name, str)
                and any([self.x_axis, self.y_axis])
                and not all([self.x_axis, self.y_axis])
            ):
                raise ValueError(
                    "When 'signal_name' is a string, either both 'x_axis' or 'y_axis' must be provided or neither should be provided."
                )
            # case name is integer
            elif any([self.signal_name, self.x_axis, self.y_axis]) and not all(
                [self.signal_name, self.x_axis, self.y_axis]
            ):
                raise ValueError(
                    "At least one field of 'signal_name','x_axis','y_axis' was provided. Then for deterministic behaviour all others must be provided."
                )

        return self


class DataElement(BaseElement):
    model_config = ConfigDict(extra="forbid")
    type: Literal["data"] = "data"
    mode: Literal["read", "write"]
    file_path: list[Path] | None = []
    data: list[str] | None = []
    label_filter: list[str] | None = None
    vstack_pattern: list[VStackPatternElement] | list[str] | None = None
    output_format: Literal["mf4"] | None = None
    stepsize: int | None = None

    @model_validator(mode="after")
    def _validate_model(self):
        """Validates that required fields are present based on the mode and the given vstack pattern."""
        if self.mode == "read":
            if not self.file_path:
                raise ValueError("Field 'file_path' is required for mode='read'.")
        if self.mode == "write":
            if not self.data:
                raise ValueError("Field 'data' is required for mode='write'.")
            if not self.output_format:
                raise ValueError("Field 'output_format' is required for mode='write'.")

        if isinstance(self.vstack_pattern, list) and isinstance(
            self.vstack_pattern[0], str
        ):
            self.vstack_pattern = [
                VStackPatternElement(pattern=pattern, signal_name=1, x_axis=2, y_axis=3)
                for pattern in self.vstack_pattern
                if isinstance(pattern, str)
            ]

        return self


class ParameterElement(BaseElement):
    model_config = ConfigDict(extra="forbid")
    type: Literal["parameter"] = "parameter"
    mode: Literal["read", "write"]
    file_path: list[Path] | None = []
    parameter: list[str] | None = []
    label_filter: list[str] | None = None
    output_format: Literal["json", "dcm"] | None = None

    @model_validator(mode="after")
    def _validate_model(self):
        """Validates that required fields are present based on the mode."""
        if self.mode == "read":
            if not self.file_path:
                raise ValueError("Field 'file_path' is required for mode='read'.")
        if self.mode == "write":
            if not self.parameter:
                raise ValueError("Field 'parameter' is required for mode='write'.")
            if not self.output_format:
                raise ValueError("Field 'output_format' is required for mode='write'.")
        return self


class PluginElement(BaseElement):
    model_config = ConfigDict(extra="allow")
    type: Literal["plugin"] = "plugin"
    file_path: Path | None = None
    plugin_name: str | None = None


class SimUnitElement(PluginElement):
    model_config = ConfigDict(extra="forbid")
    type: Literal["sim_unit"] = "sim_unit"
    plugin_path: Path = Field(
        default_factory=lambda: Path(
            os.path.relpath(
                Path(__file__).parent.parent / "plugins" / "simunit.py",
                Path(__file__).parent,
            )
        )
    )
    file_path: Path
    stepsize: int
    data: list[str] | None = []
    parameter: list[str] | None = []
    data_dictionary: Path
    init: list[str] | None = []
    cancel_condition: str | None = None
    vstack_pattern: list[VStackPatternElement] | list[str] | None = Field(
        None, exclude=True
    )


class MergeElement(PluginElement):
    model_config = ConfigDict(extra="forbid")
    type: Literal["merge"] = "merge"
    plugin_path: Path = Field(
        default_factory=lambda: Path(
            os.path.relpath(
                Path(__file__).parent.parent / "plugins" / "merge.py",
                Path(__file__).parent,
            )
        )
    )
    data: list[str] | None = []
    parameter: list[str] | None = []

    @model_validator(mode="after")
    def _validate_model(self):
        if isinstance(self.vstack_pattern, list) and isinstance(
            self.vstack_pattern[0], str
        ):
            self.vstack_pattern = [
                VStackPatternElement(pattern=pattern, signal_name=1, x_axis=2, y_axis=3)
                for pattern in self.vstack_pattern
                if isinstance(pattern, str)
            ]

        return self


WorkflowElement = Annotated[
    DataElement | ParameterElement | PluginElement | SimUnitElement | MergeElement,
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
