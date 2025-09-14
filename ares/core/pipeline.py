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

from ares.core.data import Data
from ares.core.parameter import Parameter
from ares.core.simunit import SimUnit
from ares.core.workflow import Workflow
from ares.utils.logger import create_logger

logger = create_logger("pipeline")


# TODO: use meta_data from files like e.g. mf4,mat,???
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
    try:
        logger.info("ARES pipeline is starting...")

        ares_wf = Workflow(file_path=wf_path)

        data_objects = {}
        parameter_objects = {}
        simunit_objects = {}
        custom_objects = {}

        if output_path is None:
            output_path = os.path.dirname(wf_path)

        for wf_element_name, wf_element_value in ares_wf.workflow.items():
            # handle "data" workflow elements
            if wf_element_value.type == "data":
                if "source" not in wf_element_value:
                    wf_element_value.source = ["all"]
                if "cycle_time" not in wf_element_value:
                    wf_element_value.cycle_time = 10

                # read mode: create data objectsfor each path in the workflow element
                if wf_element_value.mode == "read":
                    data_objects[wf_element_name] = []
                    for data_path in wf_element_value.path:
                        data_objects[wf_element_name].append(
                            Data(
                                file_path=data_path,
                                base_wf_element_name=wf_element_name,
                                source=wf_element_value.source,
                                step_size_init_ms=wf_element_value.cycle_time,
                            )
                        )
                # write mode: export data from data objects
                elif wf_element_value.mode == "write":
                    ares_wf.workflow[wf_element_name].path = []
                    for data_value in data_objects[
                        wf_element_value.element_input_workflow[0]
                    ]:
                        output_file_path = data_value.write_out(
                            dir_path=output_path,
                            output_format=wf_element_value.output_format,
                            meta_data=meta_data,
                            element_input_workflow=wf_element_value.element_input_workflow,
                            source=wf_element_value.source,
                        )
                        ares_wf.workflow[wf_element_name].path.append(output_file_path)

            # handle "parameter" workflow elements
            if wf_element_value.type == "parameter":
                if "source" not in wf_element_value:
                    wf_element_value.source = ["all"]

                # read mode: create parameter object for each path in the workflow element
                if wf_element_value.mode == "read":
                    parameter_objects[wf_element_name] = []
                    for parameter_path in wf_element_value.path:
                        parameter_objects[wf_element_name].append(
                            Parameter(
                                file_path=parameter_path,
                                base_wf_element_name=wf_element_name,
                            )
                        )

                # write mode: export parameter from parameter objects
                elif wf_element_value.mode == "write":
                    ares_wf.workflow[wf_element_name].path = []
                    for parameter_value in parameter_objects[
                        wf_element_value.element_parameter_workflow[0]
                    ]:
                        output_file_path = parameter_value.write_out(
                            dir_path=output_path,
                            output_format=wf_element_value.output_format,
                            meta_data=meta_data,
                            element_parameter_workflow=wf_element_value.element_parameter_workflow,
                            source=wf_element_value.source,
                        )
                        ares_wf.workflow[wf_element_name].path.append(output_file_path)

            # Handle "sim_unit" workflow elements
            if wf_element_value.type == "sim_unit":
                simunit_objects[wf_element_name] = SimUnit(
                    file_path=wf_element_value.path,
                    dd_path=wf_element_value.data_dictionary,
                )

                # Run simulation for each original data source- and parameter variant
                for data_value in data_objects[
                    wf_element_value.element_input_workflow[0]
                ]:
                    sim_input = data_value.get(step_size_ms=wf_element_value.cycle_time)

                    for parameter_value in parameter_objects[
                        wf_element_value.element_parameter_workflow[0]
                    ]:
                        sim_parameter = parameter_value.get()

                        simulation_result = simunit_objects[
                            wf_element_name
                        ].run_simulation(
                            data=sim_input,
                            parameter=sim_parameter,
                        )
                        data_value.data[wf_element_name] = simulation_result

            # handle "custom" workflow elements
            if wf_element_value.type == "custom":
                custom_objects[wf_element_name] = {}

            # TODO: if object not needed anymore
            # drop it

        ares_wf.write_out(output_path=output_path)

        logger.info("ARES pipeline successfully finished.")

    except Exception as e:
        logger.error(f"Error while executing ARES pipeline: {e}")
