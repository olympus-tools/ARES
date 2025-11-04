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

from ares.core.data import get_data_handler
from ares.core.workflow import Workflow
from ares.utils.decorators import safely_run
from ares.utils.logger import create_logger

logger = create_logger("pipeline")


@safely_run([], message="Error while executing ARES pipeline.", log=logger)
def pipeline(wf_path: str, output_path: str, meta_data: dict):
    """Executes the ARES simulation pipeline based on a defined workflow.

    This function orchestrates the entire simulation process, from data acquisition and
    processing to running simulation units and exporting the final results. It
    iterates through a workflow defined in a JSON file and dynamically manages
    the necessary objects (Data, SimUnit, Parameter, etc.).

    Args:
        wf_path: The absolute path to the workflow's JSON file.
        output_path: The absolute path to the output directory. If `None`, results
            are written to the same directory as the workflow file.
        meta_data: Current ARES and workstation meta data.
    """
    logger.info("ARES pipeline is starting...")

    # XXX: data structure return value of this should be more clear (part of an ojbect?)
    ares_wf = Workflow(file_path=wf_path)

    data_objects = []
    parameter_objects = []
    simunit_objects = []
    custom_objects = []

    if output_path is None:
        output_path = os.path.dirname(wf_path)

    for wf_element_name, wf_element in ares_wf.workflow.items():
        if wf_element.type == "data":
            tmp_data_handler = get_data_handler(
                name=wf_element_name,
                data_element=wf_element,
                data_object_list=data_objects,
            )

            if tmp_data_handler is not None:
                data_objects.extend(tmp_data_handler)
