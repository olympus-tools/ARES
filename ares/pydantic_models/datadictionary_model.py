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
from typing import Annotated, Dict, List, Literal, TypeAlias, Union

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


InputAlternatives: TypeAlias = List[Union[str, float, List[float], List[List[float]]]]


class BaseDDModel(BaseModel):
    datatype: Datatype
    size: List[int]

    class Config:
        extra = "forbid"


class InModel(BaseDDModel):
    type: Literal["in"]
    input_alternatives: Union[InputAlternatives, None] = None


class InoutModel(BaseDDModel):
    type: Literal["inout"]
    input_alternatives: Union[InputAlternatives, None] = None


class OutModel(BaseDDModel):
    type: Literal["out"]


class ParameterModel(BaseDDModel):
    type: Literal["parameter"]


DDElement = Union[InModel, InoutModel, OutModel, ParameterModel]


class DataDictionaryModel(RootModel):
    root: Dict[Annotated[str, Field(pattern=r"^[a-zA-Z0-9_]+$")], DDElement]

    def __getitem__(self, key: str) -> DDElement:
        return self.root[key]

    def __setitem__(self, key: str, value: DDElement) -> None:
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
