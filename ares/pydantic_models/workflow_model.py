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

import os
from pathlib import Path
from typing import Annotated, Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, RootModel
from typing_extensions import Literal


class BaseElement(BaseModel):
    """Base model for all workflow elements."""

    type: str
    element_workflow: List[str] = []
    hash_list: Dict[str, List[str]] = {}


class DataElement(BaseElement):
    type: Literal["data"] = "data"
    mode: Literal["read", "write"]
    path: Optional[List[str]] = []
    input: Optional[List[str]] = []
    output_format: Optional[Literal["json", "mf4"]] = None
    source: Optional[List[str]] = []
    cycle_time: Optional[int] = None

    class Config:
        extra = "forbid"

    def validate_mode_requirements(self):
        if self.mode == "read" and not self.path:
            raise ValueError("Field 'path' is required for mode='read'.")
        if self.mode == "write" and (not self.input or not self.output_format):
            raise ValueError(
                "Fields 'input' and 'output_format' are required for mode='write'."
            )


class ParameterElement(BaseElement):
    type: Literal["parameter"] = "parameter"
    mode: Literal["read", "write"]
    path: Optional[List[str]] = []
    parameter: Optional[List[str]] = []
    output_format: Optional[Literal["json", "dcm"]] = None

    class Config:
        extra = "forbid"

    def validate_mode_requirements(self):
        if self.mode == "read" and not self.path:
            raise ValueError("Field 'path' is required for mode='read'.")
        if self.mode == "write" and (not self.parameter or not self.output_format):
            raise ValueError(
                "Fields 'input' and 'output_format' are required for mode='write'."
            )


class PluginElement(BaseElement):
    type: Literal["plugin"] = "plugin"
    file_path: str

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
    path: str
    cycle_time: int
    input: List[str]
    parameter: Optional[List[str]] = []
    data_dictionary: str
    init: Optional[List[str]] = []
    cancel_condition: Optional[str] = None

    class Config:
        extra = "forbid"


WorkflowElement = Annotated[
    Union[DataElement, ParameterElement, SimUnitElement, PluginElement],
    Field(discriminator="type"),
]


# TODO: don't add this extra methods => userdict???
class WorkflowModel(RootModel):
    root: Dict[str, WorkflowElement]

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
        return self.root.get(key, default)

    def model_dump_json(self, **kwargs) -> str:
        """Dump workflow JSON as string."""
        return super().model_dump_json(**kwargs)
