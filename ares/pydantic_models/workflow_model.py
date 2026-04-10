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

import re
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    ValidationInfo,
    model_validator,
)
from typing_extensions import Literal


class DataFormat(StrEnum):
    """Allowed output formats for data elements."""

    MF4 = "mf4"


class ParameterFormat(StrEnum):
    """Allowed output formats for parameter elements."""

    JSON = "json"
    DCM = "dcm"


class SimUnitFormat(StrEnum):
    """Allowed file formats for sim unit shared libraries."""

    SO = "so"
    DLL = "dll"


class PluginFormat(StrEnum):
    """Allowed file formats for plugin elements."""

    PY = "py"


class BaseElement(BaseModel):
    """Base model for all workflow elements."""

    name: str | None = None
    element_workflow: list[str] = []
    hash_list: dict[str, list[str]] = {}

    @staticmethod
    def _resolve_single_path(
        base_dir: Path, file_path: Path, path_eval_pattern: str
    ) -> Path:
        """Resolve a single path to an absolute path if it is path-like and relative.

        A path is considered path-like when it contains a path separator
        (``/`` or ``\\``) or ends with a file extension matched by
        *path_eval_pattern*. Leaves the path unchanged if it is already
        absolute or not considered path-like.

        Args:
            base_dir (Path): Base directory used to anchor relative paths.
            file_path (Path): The path to potentially resolve.
            path_eval_pattern (str): Regex pattern used to detect file extensions.

        Returns:
            Path: The resolved absolute path, or the original path if no change is needed.
        """
        file_path_str = str(file_path)
        is_path_like = (
            "/" in file_path_str
            or "\\" in file_path_str
            or re.search(path_eval_pattern, file_path_str) is not None
        )
        if is_path_like and not file_path.is_absolute():
            return (base_dir / file_path).resolve()
        return file_path

    @staticmethod
    def _validate_file_path_format(
        file_path: list[Path] | Path | None,
        allowed_format: type[StrEnum],
    ):
        """Validates that all provided paths have a suffix matching the allowed formats.

        Derives the allowed suffixes from the enum values by prepending a dot
        (e.g. ``DataFormat.MF4 = "mf4"`` → ``.mf4``).

        Args:
            file_path (list[Path] | Path | None): Single path or list of paths to validate.
                Empty lists and ``None`` are silently accepted.
            allowed_format (type[StrEnum]): The ``StrEnum`` class whose values define
                the allowed file extensions (without leading dot).
        """
        paths = [file_path] if isinstance(file_path, Path) else file_path
        allowed_suffixes = {f".{fmt.value}" for fmt in allowed_format}
        for path in paths:
            if path.suffix not in allowed_suffixes:
                raise ValueError(
                    f"File '{path.name}' has unsupported format '{path.suffix or '(no extension)'}'."
                    f" Allowed: {sorted(allowed_suffixes)}."
                )

    @staticmethod
    def _expand_file_path(
        file_path: list[Path] | None,
        allowed_format: type[StrEnum],
    ) -> list[Path]:
        """Expands directories in a path list to all matching files within them.

        For each entry in *file_path*:

        - **File**: kept unchanged.
        - **Directory**: scanned non-recursively; only files whose suffix matches
          an entry in *allowed_format* are included. All other files are silently
          skipped.

        Args:
            file_path (list[Path] | None): Paths to expand. ``None`` and empty
                lists are returned as an empty list without error.
            allowed_format (type[StrEnum]): The ``StrEnum`` class whose values
                define the allowed file extensions (without leading dot).

        Returns:
            list[Path]: Flat, expanded list of file paths, sorted within each
                expanded directory.
        """
        if not file_path:
            return []
        allowed_suffixes = {f".{fmt.value}" for fmt in allowed_format}
        result: list[Path] = []
        for path in file_path:
            if path.is_dir():
                result.extend(
                    sorted(
                        p
                        for p in path.iterdir()
                        if p.is_file() and p.suffix in allowed_suffixes
                    )
                )
            else:
                result.append(path)
        return result

    @model_validator(mode="after")
    def _resolve_paths(self, info: ValidationInfo) -> "BaseElement":
        """Resolves relative Path fields to absolute paths using the workflow file's base directory.

        Requires validation context with key 'base_dir' (Path). Handles both single
        Path fields and list[Path] fields. Paths without path separators or file
        extensions are left unchanged.

        Args:
            info (ValidationInfo): Pydantic validation context, expected to contain
                a 'base_dir' key with the base directory as a Path.

        Returns:
            BaseElement: The model instance with all relative Path fields resolved
                to absolute paths.
        """
        if not info.context or "base_dir" not in info.context:
            return self
        base_dir: Path = info.context["base_dir"]
        path_eval_pattern = r"\.[a-zA-Z0-9]+$"
        skip_fields = {"plugin_path"}

        for field_name, field_value in self.__dict__.items():
            if field_name in skip_fields:
                continue
            if isinstance(field_value, Path):
                resolved_path = self._resolve_single_path(
                    base_dir=base_dir,
                    file_path=field_value,
                    path_eval_pattern=path_eval_pattern,
                )
                if resolved_path != field_value:
                    setattr(self, field_name, resolved_path)

            elif (
                isinstance(field_value, list)
                and field_value
                and all(isinstance(p, Path) for p in field_value)
            ):
                resolved_list = [
                    self._resolve_single_path(
                        base_dir=base_dir,
                        file_path=p,
                        path_eval_pattern=path_eval_pattern,
                    )
                    for p in field_value
                ]
                if resolved_list != field_value:
                    setattr(self, field_name, resolved_list)
        return self


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
                    "When 'signal_name' is a string, either both 'x_axis' and 'y_axis' must be provided or neither should be provided."
                )
            elif any([self.signal_name, self.x_axis, self.y_axis]) and not all(
                [self.signal_name, self.x_axis, self.y_axis]
            ):
                raise ValueError(
                    "At least one field of 'signal_name','x_axis','y_axis' was provided. Then for deterministic behaviour all others must be provided."
                )
        elif pattern.groups == 2:
            if self.y_axis:
                raise ValueError(
                    "Only 2 groups are given, field 'y_axis' is only valid with 3 groups."
                )
            elif self.x_axis and not self.signal_name:
                raise ValueError(
                    "The field of 'x_axis' was provided. Then for deterministic behaviour 'signal_name' must be provided."
                )

        return self


class DataElement(BaseElement):
    model_config = ConfigDict(extra="forbid")
    type: Literal["data"] = "data"
    mode: Literal["read", "write"]
    file_path: list[Path] | None = []
    data: list[str] | None = []
    label_filter: list[str] | None = None
    vstack_pattern: list[VStackPatternElement | str] | None = None
    output_format: DataFormat | None = None
    stepsize: int | None = None

    @model_validator(mode="after")
    def _validate_model(self):
        """Validates that required fields are present based on the mode and the given vstack pattern."""
        if self.mode == "read":
            if not self.file_path:
                raise ValueError("Field 'file_path' is required for mode='read'.")
            else:
                self.file_path = self._expand_file_path(
                    file_path=self.file_path, allowed_format=DataFormat
                )
                self._validate_file_path_format(
                    file_path=self.file_path, allowed_format=DataFormat
                )
        if self.mode == "write":
            if not self.data:
                raise ValueError("Field 'data' is required for mode='write'.")
            if not self.output_format:
                raise ValueError("Field 'output_format' is required for mode='write'.")

        if self.vstack_pattern is not None:
            self.vstack_pattern = [
                VStackPatternElement(pattern=pattern, signal_name=1, x_axis=2, y_axis=3)
                if isinstance(pattern, str)
                else pattern
                for pattern in self.vstack_pattern
            ]

        return self


class ParameterElement(BaseElement):
    model_config = ConfigDict(extra="forbid")
    type: Literal["parameter"] = "parameter"
    mode: Literal["read", "write"]
    file_path: list[Path] | None = []
    parameter: list[str] | None = []
    label_filter: list[str] | None = None
    output_format: ParameterFormat | None = None

    @model_validator(mode="after")
    def _validate_model(self):
        """Validates that required fields are present based on the mode."""
        if self.mode == "read":
            if not self.file_path:
                raise ValueError("Field 'file_path' is required for mode='read'.")
            else:
                self.file_path = self._expand_file_path(
                    file_path=self.file_path, allowed_format=ParameterFormat
                )
                self._validate_file_path_format(
                    file_path=self.file_path, allowed_format=ParameterFormat
                )
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
    parameter_obj: list[Any] | None = None
    data_obj: list[Any] | None = None
    parameter_hash_lists: list[list[str]] = []
    data_hash_lists: list[list[str]] = []

    @model_validator(mode="after")
    def _validate_model(self):
        """Validates that file_path, if provided, points to a Python (.py) file."""
        self._validate_file_path_format(
            file_path=self.file_path, allowed_format=PluginFormat
        )
        return self


class SimUnitElement(PluginElement):
    model_config = ConfigDict(extra="forbid")
    type: Literal["sim_unit"] = "sim_unit"
    plugin_path: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent / "plugins" / "simunit.py"
    )
    file_path: Path
    stepsize: int
    data: list[str] | None = []
    parameter: list[str] | None = []
    data_dictionary: Path
    init: list[str] | None = []
    cancel_condition: str | None = None
    vstack_pattern: list[VStackPatternElement | str] | None = None
    parameter_obj: list[Any] | None = None
    data_obj: list[Any] | None = None
    parameter_hash_lists: list[list[str]] = []
    data_hash_lists: list[list[str]] = []

    @model_validator(mode="after")
    def _validate_model(self):
        self._validate_file_path_format(
            file_path=self.file_path, allowed_format=SimUnitFormat
        )
        if self.vstack_pattern is not None:
            self.vstack_pattern = [
                VStackPatternElement(pattern=pattern, signal_name=1, x_axis=2, y_axis=3)
                if isinstance(pattern, str)
                else pattern
                for pattern in self.vstack_pattern
            ]

        return self


class MergeElement(PluginElement):
    model_config = ConfigDict(extra="forbid")
    type: Literal["merge"] = "merge"
    plugin_path: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent / "plugins" / "merge.py"
    )
    data: list[str] | None = []
    parameter: list[str] | None = []
    label_filter_data: list[str] | None = None
    label_filter_parameter: list[str] | None = None
    vstack_pattern_data: list[VStackPatternElement] | list[str] | None = None
    vstack_pattern_parameter: list[VStackPatternElement] | list[str] | None = None
    stepsize: int | None = None
    parameter_obj: list[Any] | None = None
    data_obj: list[Any] | None = None
    parameter_hash_lists: list[list[str]] = []
    data_hash_lists: list[list[str]] = []

    @model_validator(mode="after")
    def _validate_model(self):
        if self.vstack_pattern_data is not None and isinstance(
            self.vstack_pattern_data[0], str
        ):
            self.vstack_pattern_data = [
                VStackPatternElement(pattern=pattern, signal_name=1, x_axis=2, y_axis=3)
                for pattern in self.vstack_pattern_data
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

    @model_validator(mode="after")
    def _inject_element_names(self):
        """Inject the workflow key name into each element's 'name' field."""
        for key, element in self.root.items():
            element.name = key
        return self

    def values(self):
        return self.root.values()

    def keys(self):
        return self.root.keys()

    def __getitem__(self, key: str) -> WorkflowElement:
        return self.root[key]

    def __setitem__(self, key: str, value: WorkflowElement) -> None:
        self.root[key] = value

    def __delitem__(self, key: str) -> None:
        del self.root[key]

    def get(self, key: str, default: Any = None):
        """Get an item from the workflow.

        Args:
            key (str): The key to look up.
            default (Any): The default value if key is not found.

        Returns:
            WorkflowElement | Any: The found element or the default value.
        """
        return self.root.get(key, default)
