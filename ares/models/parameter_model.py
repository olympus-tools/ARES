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

"""
parameter_model.py

Defines the Pydantic models for parameter validation and unified structure
for both DCM and JSON inputs.
"""

from enum import Enum
from typing import Annotated, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, RootModel

from ares.core.simunit import SimUnit

DataType = Enum("DataType", list(SimUnit.DATATYPES.keys()))


class DCMKeywordScalar(str, Enum):
    FESTWERT = "FESTWERT"
    TEXTSTRING = "TEXTSTRING"


class DCMKeywordArray1D(str, Enum):
    TEXTSTRING = "TEXTSTRING"
    FESTWERTEBLOCK = "FESTWERTEBLOCK"
    FESTKENNLINIE = "FESTKENNLINIE"
    KENNLINIE = "KENNLINIE"
    GRUPPENKENNLINIE = "GRUPPENKENNLINIE"
    STUETZSTELLENVERTEILUNG = "STUETZSTELLENVERTEILUNG"


class DCMKeywordArray2D(str, Enum):
    TEXTSTRING = "TEXTSTRING"
    FESTWERTEBLOCK = "FESTWERTEBLOCK"
    FESTKENNFELD = "FESTKENNFELD"
    KENNFELD = "KENNFELD"
    GRUPPENKENNFELD = "GRUPPENKENNFELD"


class BaseParameter(BaseModel):
    description: Optional[str] = None
    unit: Optional[str] = None

    class Config:
        extra = "forbid"


class ScalarParameter(BaseParameter):
    type: Literal["scalar"] = Field("scalar", exclude=True)
    dcm_keyword: Optional[DCMKeywordScalar] = Field(None, exclude=True)
    value: Union[int, float, str, bool]


class Array1DParameter(BaseParameter):
    type: Literal["array1d"] = Field("array1d", exclude=True)
    dcm_keyword: Optional[DCMKeywordArray1D] = Field(None, exclude=True)
    name_breakpoints_1: Optional[str] = None
    value: List[Union[int, float]]


class Array2DParameter(BaseParameter):
    type: Literal["array2d"] = Field("array2d", exclude=True)
    dcm_keyword: Optional[DCMKeywordArray2D] = Field(None, exclude=True)
    name_breakpoints_1: Optional[str] = None
    name_breakpoints_2: Optional[str] = None
    value: List[List[Union[int, float]]]


# Union type
ParameterElement = Annotated[
    Union[ScalarParameter, Array1DParameter, Array2DParameter],
    Field(discriminator="type"),
]


class ParameterModel(RootModel):
    root: Dict[str, ParameterElement]

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
