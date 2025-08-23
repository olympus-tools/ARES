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

from ares.core.data import Data
from ares.core.workflow import Workflow
from ares.core.simunit import SimUnit
from ares.core.logfile import Logfile
from ares.core.parameter import Parameter

import os

def pipeline(wf_path: str, output_path: str, logfile: Logfile):
    """Executes the ARES simulation pipeline based on a defined workflow.

    This function orchestrates the entire simulation process, from data acquisition and
    processing to running simulation units and exporting the final results. It
    iterates through a workflow defined in a JSON file and dynamically manages
    the necessary objects (Data, SimUnit, Parameter, etc.).

    Args:
        wf_path: The absolute path to the workflow's JSON file.
        output_path: The absolute path to the output directory. If `None`, results
            are written to the same directory as the workflow file.
        logfile: An instance of the `Logfile` class used for logging the process.

    Raises:
        Exception: If any error occurs during the pipeline execution, it is caught,
            logged, and the process is terminated. This ensures robust error
            handling.
    """
    try:
        logfile.write("ARES pipeline is starting...", level="INFO")

        ares_wf = Workflow(file_path=wf_path, logfile=logfile)

        data_source_objects = {}
        param_objects = {}
        simunit_objects = {}
        custom_objects = {}

        if output_path is None:
            output_path = os.path.dirname(wf_path)

        for wf_element_name, wf_element_value in ares_wf.workflow.root.items():

            # Handle "data" workflow elements
            if wf_element_value.type == "data":

                if "source" not in wf_element_value:
                    wf_element_value.source = ["all"]
                if "cycle_time" not in wf_element_value:
                    wf_element_value.cycle_time = 10

                # Read mode: create Data objects for each path in the workflow element
                if wf_element_value.mode == "read":
                    data_source_objects[wf_element_name] = {}
                    for data_source_idx, data_source_path in enumerate(wf_element_value.path):
                        data_source_objects[wf_element_name][data_source_idx] = Data(
                            file_path=data_source_path,
                            source=wf_element_value.source,
                            step_size_init_ms=wf_element_value.cycle_time,
                            logfile=logfile,
                        )
                # Write mode: export data from Data objects
                elif wf_element_value.mode == "write":
                    ares_wf.workflow.root[wf_element_name].path = []
                    for data_source_value in data_source_objects[wf_element_value.element_workflow[0]].values():
                        output_file_path = data_source_value.write_out(
                            dir_path=output_path,
                            output_format=wf_element_value.output_format,
                            element_workflow=wf_element_value.element_workflow,
                            source=wf_element_value.source,
                        )
                        ares_wf.workflow.root[wf_element_name].path.append(output_file_path)

            # Handle "parameter" workflow elements
            if wf_element_value.type == "parameter":
                param_objects[wf_element_name] = {}

            # Handle "sim_unit" workflow elements
            if wf_element_value.type == "sim_unit":

                simunit_objects[wf_element_name] = SimUnit(
                    file_path=wf_element_value.path,
                    dd_path=wf_element_value.data_dictionary,
                    logfile=logfile,
                )

                # Run simulation for each original data source- and parameter variant
                for data_source_value in data_source_objects[wf_element_value.element_workflow[0]].values():
                    sim_input = data_source_value.get(step_size_ms=wf_element_value.cycle_time)

                    for parameter_name in wf_element_value.parameter:
                        simulation_result = simunit_objects[wf_element_name].run_simulation(
                            data=sim_input,
                            parameter=param_objects[parameter_name],
                        )
                        data_source_value.data[wf_element_name] = simulation_result

            # Handle "custom" workflow elements
            if wf_element_value.type == "custom":
                custom_objects[wf_element_name] = {}

            # TODO: if object not needed anymore
            # drop object

        ares_wf.write_out(output_path=output_path)

        logfile.write("ARES pipeline successfully finished.", level="INFO")

    except Exception as e:
        logfile.write(f"Error while executing ARES pipeline: {e}", level="ERROR")
