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

import numpy as np

# from ares.interface.parameter.ares_data_interface import AresDataInterface
from ares.interface.parameter.ares_param_interface import AresParamInterface
from ares.interface.parameter.parameter import AresParameter


def ares_plugin(plugin_input: dict):
    """ARES plugin function called by AresPluginInterface.

    Args:
        element_name: Name of the workflow element
        plugin_input: Dictionary containing all plugin configuration and data:
            - parameter: Dict[str, AresParamInterface] - AresParameter storage with hashes as keys
            - plugin_path: str - Path to this plugin file
            - type: str - Element type ("plugin" or "sim_unit")
            - element_workflow: List[str] - Workflow elements
            - ... other fields from WorkflowElement
    """
    parameters = plugin_input.get("parameter", {})

    new_params = [
        AresParameter(
            label="output_1",
            value=np.array([1.0]),
            unit="m",
            description="Result from plugin_example_1",
        )
    ]

    for param_interface in parameters.values():
        new_params.extend(param_interface.get())
        AresParamInterface.create(
            parameters=new_params, dependencies=[param_interface.hash]
        )
