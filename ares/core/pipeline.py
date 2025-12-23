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
from typing import Any, Dict, List

from ares.core.workflow import Workflow
from ares.interface.data.ares_data_interface import AresDataInterface
from ares.interface.parameter.ares_parameter_interface import AresParamInterface
from ares.interface.plugin.ares_plugin_interface import AresPluginInterface
from ares.utils.logger import create_logger

logger = create_logger(__name__)


# TODO: use meta_data from files like e.g. mf4,mat,????
def pipeline(wf_path: str, output_dir: str, meta_data: Dict[str, Any]) -> None:
    """Executes the ARES simulation pipeline based on a defined workflow.

    This function orchestrates the entire simulation process, from data acquisition and
    processing to running simulation units and exporting the final results. It
    iterates through a workflow defined in a JSON file and dynamically manages
    the necessary objects (Data, SimUnit, Parameter, etc.).

    Args:
        wf_path: The absolute path to the workflow's JSON file.
        output_dir: The absolute path to the output directory. If `None`, results
            are written to the same directory as the workflow file.
        meta_data: Current ARES and workstation meta data.
    """
    try:
        logger.info("ARES pipeline is starting...")

        ares_wf = Workflow(file_path=wf_path)

        param_storage: List[AresParamInterface] = AresParamInterface.cache
        data_storage: List[AresDataInterface] = AresDataInterface.cache

        if output_dir is None:
            output_dir = os.path.dirname(wf_path)

        # evaluation of all sinks, that were found in workflow json files
        for wf_sink in ares_wf.workflow_sinks:
            wf_element_workflow = list(ares_wf.workflow[wf_sink].element_workflow) + [
                wf_sink
            ]

            for wf_element_name in wf_element_workflow:
                wf_element_value = ares_wf.workflow[wf_element_name]

                prev_param_hash_list: List[str] = list(param_storage.keys())
                # prev_data_hash_list: List[str] = list(data_storage.keys())

                tmp_param_hash_list: List[List[str]] = []
                for parameter in getattr(wf_element_value, "parameter", []):
                    tmp_param_hash_list.append(
                        list(ares_wf.workflow[parameter].hash_list.keys())
                    )
                tmp_data_hash_list: List[List[str]] = []
                # for data in getattr(wf_element_value, "input", []):
                #     tmp_param_hash_list.append(
                #         list(ares_wf.workflow[input].hash_list.keys())
                #     )

                # handle workflow elements based on their type
                match wf_element_value.type:
                    case "data":
                        AresDataInterface.wf_element_handler(
                            element_name=wf_element_name,
                            element_value=wf_element_value,
                            input_hash_list=tmp_data_hash_list,
                        )

                    case "parameter":
                        AresParamInterface.wf_element_handler(
                            element_name=wf_element_name,
                            element_value=wf_element_value,
                            input_hash_list=tmp_param_hash_list,
                            output_dir=output_dir,
                        )

                    case "sim_unit" | "plugin":
                        plugin_input: Dict[str, Any] = wf_element_value.model_dump()
                        plugin_input["element_name"] = wf_element_name

                        if wf_element_value.type == "sim_unit":
                            plugin_input["plugin_path"] = os.path.join(
                                os.path.dirname(
                                    os.path.dirname(os.path.abspath(__file__))
                                ),
                                "plugins",
                                "simunit.py",
                            )
                        else:
                            plugin_input["plugin_path"] = plugin_input["file_path"]

                        # filtering relevant parameter for plugin element
                        plugin_input["parameter"] = [
                            [
                                param_storage[key]
                                for key in hash_list
                                if key in param_storage
                            ]
                            for hash_list in tmp_param_hash_list
                        ]
                        # # filtering relevant data for plugin element
                        # plugin_input["data"] = [
                        #     [data_storage[key] for key in hash_list if key in data_storage]
                        #     for hash_list in tmp_data_hash_list
                        # ]

                        AresPluginInterface(
                            plugin_input=plugin_input,
                        )

                # update workflow element hash list with new hashes only
                new_param_hash_list = [
                    hash_key
                    for hash_key in param_storage.keys()
                    if hash_key not in prev_param_hash_list
                ]
                for hash_key in new_param_hash_list:
                    wf_element_value.hash_list[hash_key] = param_storage[
                        hash_key
                    ].dependencies
                # new_data_hash_list = [
                #     hash_key
                #     for hash_key in data_storage.keys()
                #     if hash_key not in prev_data_hash_list
                # ]
                # for hash_key in new_data_hash_list:
                #     wf_element_value.hash_list[hash_key] = data_storage[
                #         hash_key
                #     ].dependencies

        # TODO: if parameter/measurement not needed anymore => drop it

        ares_wf.save(output_dir=output_dir)

        logger.info("ARES pipeline successfully finished.")
    except Exception as e:
        logger.error(f"Error while executing ARES pipeline: {e}")
        raise
