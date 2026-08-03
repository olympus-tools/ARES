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

"""
parameter_model.py

Defines the Pydantic models for parameter validation and unified structure
for both DCM and JSON inputs.
"""

from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, Field, RootModel

from ares.plugins.simunit import SimUnit

DataType = Enum("DataType", list(SimUnit.DATATYPES.keys()))


class BaseParameter(BaseModel):
    """Base Pydantic model shared by all parameter types."""

    description: str | None = None
    unit: str | None = None

    class Config:
        extra = "forbid"


class ScalarParameter(BaseParameter):
    """Pydantic model for a scalar (0-dimensional) parameter."""

    type: Literal["scalar"] = Field("scalar")
    value: int | float | str | bool


class Array1DParameter(BaseParameter):
    """Pydantic model for a one-dimensional array parameter."""

    type: Literal["array1d"] = Field("array1d")
    name_breakpoints_1: str | None = None
    value: list[int | float]


class Array2DParameter(BaseParameter):
    """Pydantic model for a two-dimensional array parameter."""

    type: Literal["array2d"] = Field("array2d")
    name_breakpoints_1: str | None = None
    name_breakpoints_2: str | None = None
    value: list[list[int | float]]


# Union type
ParameterElement = Annotated[
    ScalarParameter | Array1DParameter | Array2DParameter,
    Field(discriminator="type"),
]


class ParameterModel(RootModel):
    """Pydantic root model representing a parameter set as a mapping of parameter names to parameter elements."""

    root: dict[str, ParameterElement]

    def __getitem__(self, key: str) -> ParameterElement:
        """Return the parameter element with the given name.

        Args:
            key (str): The name of the parameter element to retrieve.

        Returns:
            ParameterElement: The parameter element associated with the key.
        """
        return self.root[key]

    def __setitem__(self, key: str, value: ParameterElement) -> None:
        """Set or replace a parameter element by name.

        Args:
            key (str): The name of the parameter element.
            value (ParameterElement): The parameter element to store.
        """
        self.root[key] = value

    def __delitem__(self, key: str) -> None:
        """Delete a parameter element by name.

        Args:
            key (str): The name of the parameter element to delete.
        """
        del self.root[key]

    def __iter__(self):
        """Iterate over parameter element names.

        Returns:
            Iterator[str]: An iterator over the parameter element keys.
        """
        return iter(self.root)

    def __len__(self) -> int:
        """Return the number of parameter elements.

        Returns:
            int: The total count of parameter elements in this model.
        """
        return len(self.root)

    def items(self):
        """Return parameter name–element pairs.

        Returns:
            ItemsView[str, ParameterElement]: A view of all name–element pairs.
        """
        return self.root.items()

    def values(self):
        """Return the parameter elements.

        Returns:
            ValuesView[ParameterElement]: A view of all parameter elements.
        """
        return self.root.values()

    def keys(self):
        """Return the parameter element names.

        Returns:
            KeysView[str]: A view of all parameter element names.
        """
        return self.root.keys()
