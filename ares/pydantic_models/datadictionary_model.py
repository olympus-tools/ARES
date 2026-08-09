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

from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, Field


class Datatype(str, Enum):
    """Allowed C datatypes for signals and parameters in the Data Dictionary."""

    float = "float"
    double = "double"
    bool = "bool"
    short = "short"
    int8 = "int8"
    int16 = "int16"
    int32 = "int32"
    int64 = "int64"
    uint8 = "uint8"
    uint16 = "uint16"
    uint32 = "uint32"
    uint64 = "uint64"


type MappingAlternatives = list[str | float | list[float] | list[list[float]]]


class BaseDDModel(BaseModel):
    """Base Pydantic model shared by all Data Dictionary signal and parameter entries."""

    datatype: Datatype
    size: list[int]

    class Config:
        extra = "forbid"


class SignalModel(BaseDDModel):
    """Base model for signal entries in the Data Dictionary."""

    unit: str | None = None
    description: str | None = None


class InModel(SignalModel):
    """Data Dictionary model for input signals (type 'in')."""

    type: Literal["in"]
    mapping_alternatives: MappingAlternatives = []


class InoutModel(SignalModel):
    """Data Dictionary model for bidirectional signals (type 'inout')."""

    type: Literal["inout"]
    mapping_alternatives: MappingAlternatives = []


class OutModel(SignalModel):
    """Data Dictionary model for output signals (type 'out')."""

    type: Literal["out"]


class ParameterModel(BaseDDModel):
    """Data Dictionary model for simulation parameters."""

    mapping_alternatives: MappingAlternatives = []


SignalElement = InModel | InoutModel | OutModel


class ExecutionOrder(BaseModel):
    """Pydantic model for the execution order of initialization and cyclical simulation functions."""

    initialization: list[str] | None = []
    cyclical: list[str] | None = []


class DataDictionaryModel(BaseModel):
    """Pydantic model for a simulation unit Data Dictionary with signals, parameters, and execution order."""

    signals: (
        dict[Annotated[str, Field(pattern=r"^[a-zA-Z0-9_]+$")], SignalElement] | None
    ) = None
    parameters: (
        dict[Annotated[str, Field(pattern=r"^[a-zA-Z0-9_]+$")], ParameterModel] | None
    ) = None
    execution_order: ExecutionOrder | None = None

    class Config:
        extra = "forbid"
