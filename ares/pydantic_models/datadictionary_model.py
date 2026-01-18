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

from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, Field


class Datatype(str, Enum):
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


type InputAlternatives = list[str | float | list[float] | list[list[float]]]


class BaseDDModel(BaseModel):
    datatype: Datatype
    size: list[int]

    class Config:
        extra = "forbid"


class InModel(BaseDDModel):
    type: Literal["in"]
    input_alternatives: InputAlternatives = []


class InoutModel(BaseDDModel):
    type: Literal["inout"]
    input_alternatives: InputAlternatives = []


class OutModel(BaseDDModel):
    type: Literal["out"]


class ParameterModel(BaseDDModel):
    """Parameter model without type field."""

    pass


SignalElement = InModel | InoutModel | OutModel


class MetaDataModel(BaseModel):
    """Meta data model with optional fields.

    Args:
        function_name (str | None): Optional function name

    Returns:
        MetaDataModel: Validated meta data instance
    """

    function_name: str | None = None

    class Config:
        extra = "allow"


class DataDictionaryModel(BaseModel):
    """Data Dictionary Model with separate signals and parameters sections.

    Args:
        signals (dict[str, SignalElement]): Dictionary of signal definitions (in, inout, out)
        parameters (dict[str, ParameterModel]): Dictionary of parameter definitions
        meta_data (MetaDataModel | None): Optional meta data containing function name and other fields

    Returns:
        DataDictionaryModel: Validated data dictionary instance
    """

    signals: dict[Annotated[str, Field(pattern=r"^[a-zA-Z0-9_]+$")], SignalElement]
    parameters: dict[Annotated[str, Field(pattern=r"^[a-zA-Z0-9_]+$")], ParameterModel]
    meta_data: MetaDataModel | None = None

    class Config:
        extra = "forbid"
