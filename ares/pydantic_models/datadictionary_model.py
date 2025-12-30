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

from enum import Enum
from typing import Annotated, Literal, TypeAlias

from pydantic import BaseModel, Field, RootModel


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


InputAlternatives: TypeAlias = list[str | float | list[float] | list[list[float]]]


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


class DataDictionaryModel(BaseModel):
    """Data Dictionary Model with separate signals and parameters sections.

    Args:
        signals (dict[str, SignalElement]): Dictionary of signal definitions (in, inout, out)
        parameters (dict[str, ParameterModel]): Dictionary of parameter definitions

    Returns:
        DataDictionaryModel: Validated data dictionary instance
    """

    signals: dict[Annotated[str, Field(pattern=r"^[a-zA-Z0-9_]+$")], SignalElement]
    parameters: dict[Annotated[str, Field(pattern=r"^[a-zA-Z0-9_]+$")], ParameterModel]

    class Config:
        extra = "forbid"
