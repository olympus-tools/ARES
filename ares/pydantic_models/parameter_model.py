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
    description: str | None = None
    unit: str | None = None

    class Config:
        extra = "forbid"


class ScalarParameter(BaseParameter):
    type: Literal["scalar"] = Field("scalar")
    value: int | float | str | bool


class Array1DParameter(BaseParameter):
    type: Literal["array1d"] = Field("array1d")
    name_breakpoints_1: str | None = None
    value: list[int | float]


class Array2DParameter(BaseParameter):
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
    root: dict[str, ParameterElement]

    def __getitem__(self, key: str) -> ParameterElement:
        return self.root[key]

    def __setitem__(self, key: str, value: ParameterElement) -> None:
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
