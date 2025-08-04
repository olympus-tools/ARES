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

from .utilities.class_datasource import DataSource
from .utilities.class_workflow import Workflow
from .utilities.class_simunit import SimUnit
from .utilities.class_logfile import Logfile
from .utilities.class_parameter import Parameter


def ares_pipeline(wf_path: str, logfile: Logfile = None):

    try:
        logfile.write("ARES pipeline is starting...", level="INFO")

        ares_wf = Workflow(file_path=wf_path, logfile=logfile)

        data_source_objects = {}
        param_objects = {}
        simunit_objects = {}
        custom_objects = {}

        for wf_element_name, wf_element_value in ares_wf.workflow.items():

            # TODO: if object not needed anymore
            # drop opject

            # Handle "data_source" workflow elements
            if wf_element_value["type"] == "data_source":

                if "source" not in wf_element_value:
                    wf_element_value["source"] = ["all"]
                if "cycle_time" not in wf_element_value:
                    wf_element_value["cycle_time"] = 10

                # Read mode: create DataSource objects for each path in the workflow element
                if wf_element_value["mode"] == "read":
                    data_source_objects[wf_element_name] = {}
                    for data_source_idx, data_source_path in enumerate(
                        wf_element_value["path"]
                    ):
                        data_source_objects[wf_element_name][data_source_idx] = (
                            DataSource(
                                file_path=data_source_path,
                                source=wf_element_value["source"],
                                step_size_init_ms=wf_element_value["cycle_time"],
                                logfile=logfile,
                            )
                        )
                # Write mode: export data from DataSource objects
                elif wf_element_value["mode"] == "write":
                    for data_source_name in wf_element_value["original_data_source"]:
                        for data_source_par_var in data_source_objects[data_source_name].values():
                            data_source_par_var.write_out(
                                file_path=wf_element_value["output"],
                                #TODO: element_workflow=wf_element_value['element_workflow'],
                                source=wf_element_value["source"],
                            )

            # Handle "parameter" workflow elements
            if wf_element_value["type"] == "parameter":
                param_objects[wf_element_name] = {}

            # Handle "sim_unit" workflow elements
            if wf_element_value["type"] == "sim_unit":

                simunit_objects[wf_element_name] = SimUnit(
                    file_path=wf_element_value["path"],
                    dd_path=wf_element_value["data_dictionary"],
                    logfile=logfile,
                )

                # Run simulation for each original data source- and parameter variant
                for original_source in wf_element_value["original_data_source"]:
                    source_objects = data_source_objects[original_source]

                    for data_source_value in source_objects.values():
                        sim_input = data_source_value.get(
                            step_size_ms=wf_element_value["cycle_time"]
                        )
                        for parameter_name in wf_element_value["dataset"]:
                            simulation_result = simunit_objects[
                                wf_element_name
                            ].run_simulation(
                                data=sim_input,
                                parameter=param_objects[parameter_name],
                            )
                            data_source_value.data[wf_element_name] = simulation_result

            # Handle "custom" workflow elements
            if wf_element_value["type"] == "custom":
                custom_objects[wf_element_name] = {}

        # Write out workflow evaluated workflow
        ares_wf.write_out(file_path=wf_path)

        logfile.write("ARES pipeline successfully finished.", level="INFO")

    except Exception as e:
        logfile.write(f"Error while executing ARES pipeline: {e}", level="ERROR")
