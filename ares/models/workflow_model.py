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

from pydantic import BaseModel, RootModel, Field, model_validator
from typing import List, Dict, Optional, Any, Union, Literal


class BaseElement(BaseModel):
    """Base model for all workflow elements to share common fields."""
    type: str
    element_workflow: List[str] = Field(default_factory=list, description="A list of workflow elements that this element depends on, in execution order.")


class DataElement(BaseElement):
    """Model for workflow elements of type 'data'."""
    type: Literal["data"] = "data"
    mode: str
    path: Optional[List[str]] = Field(None, min_items=1)
    source: List[str] = Field(default_factory=lambda: ["all"], min_items=0)
    input: Optional[List[str]] = Field(None, min_items=1)
    cycle_time: int = Field(10, ge=1)
    output_format: Optional[str] = None
    element_workflow: List[str] = Field(default_factory=list)

    class Config:
        """Pydantic model configuration."""
        extra = 'forbid'

    @model_validator(mode='after')
    def check_mode_requirements(self):
        """Validate required fields based on 'mode'."""
        if self.mode == 'read' and not self.path:
            raise ValueError("Field 'path' is required when mode is 'read'.")
        if self.mode == 'write' and (not self.input or not self.output_format):
            raise ValueError("Fields 'input' and 'output_format' are required when mode is 'write'.")

        return self


class ParameterElement(BaseElement):
    """Model for workflow elements of type 'parameter'."""
    type: Literal["parameter"] = "parameter"
    path: List[str] = Field(min_items=1)
    element_workflow: List[str] = Field(default_factory=list)

    class Config:
        """Pydantic model configuration."""
        extra = 'forbid'


class SimUnitElement(BaseElement):
    """Model for workflow elements of type 'sim_unit'."""
    type: Literal["sim_unit"] = "sim_unit"
    path: str
    parameter: Optional[List[str]] = Field(None, min_items=1)
    cycle_time: int = Field(..., ge=1)
    input: List[str] = Field(min_items=1)
    data_dictionary: str
    init: Optional[List[str]] = Field(None, min_items=1)
    cancel_condition: Optional[str] = None
    element_workflow: List[str] = Field(default_factory=list)

    class Config:
        """Pydantic model configuration."""
        extra = 'forbid'


class CustomElement(BaseElement):
    """Model for workflow elements of type 'custom'."""
    type: Literal["custom"] = "custom"
    path: str
    input: Optional[List[str]] = Field(None, min_items=1)
    output: Optional[str] = None
    parameter: Optional[List[str]] = Field(None, min_items=1)
    init: Optional[List[str]] = Field(None, min_items=1)
    cancel_condition: Optional[str] = None
    plot_config: Optional[Dict[str, Any]] = None
    spec: Optional[str] = None
    element_workflow: List[str] = Field(default_factory=list)


WorkflowElement = Union[DataElement, ParameterElement, SimUnitElement, CustomElement]

class WorkflowSchema(RootModel):
    """The root model for the entire workflow JSON."""
    root: Dict[str, WorkflowElement]

    def model_dump_json(self, **kwargs: Any) -> str:
        """Dump the model to a JSON string."""
        return super().model_dump_json(**kwargs)
