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

import copy
import os

from ares.core.data import Data
from ares.core.parameter import Parameter
from ares.core.simunit import SimUnit
from ares.core.workflow import Workflow
from ares.utils.logger import create_logger

logger = create_logger("pipeline")


# TODO: use meta_data from files like e.g. mf4,mat,????
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

        if output_path is None:
            output_path = os.path.dirname(wf_path)

        # evaluation of all sinks, that were found in workflow json files
        wf_objects = {}
        for wf_sink in ares_wf.workflow_sinks:
            wf_element_workflow = list(
                ares_wf.workflow.get(wf_sink).element_workflow
            ) + [wf_sink]

            for wf_element_name in wf_element_workflow:
                wf_objects[wf_element_name] = {}
                wf_element_value = ares_wf.workflow.get(wf_element_name)

                # handle "data" workflow elements
                if wf_element_value.type == "data":
                    if "source" not in wf_element_value:
                        wf_element_value.source = ["all"]
                    if "cycle_time" not in wf_element_value:
                        wf_element_value.cycle_time = 10

                    # read mode: create data objects for each path in the workflow element
                    if wf_element_value.mode == "read":
                        for idx, data_path in enumerate(wf_element_value.path):
                            wf_objects[wf_element_name][f"variant_{idx}"] = Data(
                                file_path=data_path,
                                base_wf_element_name=wf_element_name,
                                source=wf_element_value.source,
                                step_size_init_ms=wf_element_value.cycle_time,
                            )
                    # write mode: export data from data objects
                    elif wf_element_value.mode == "write":
                        pass  # TODO: implement write mode here

                # handle "parameter" workflow objects
                elif wf_element_value.type == "parameter":
                    if "source" not in wf_element_value:
                        wf_element_value.source = ["all"]

                    # read mode: create parameter object for each path in the workflow element
                    if wf_element_value.mode == "read":
                        for idx, parameter_path in enumerate(wf_element_value.path):
                            wf_objects[wf_element_name][f"variant_{idx}"] = Parameter(
                                file_path=parameter_path,
                                base_wf_element_name=wf_element_name,
                            )

                    # write mode: export parameter from parameter objects
                    elif wf_element_value.mode == "write":
                        pass  # TODO: implement write mode here

                # handle "sim_unit" workflow elements
                elif wf_element_value.type == "sim_unit":
                    wf_objects[wf_element_name] = SimUnit(
                        type=wf_element_value.type,
                        input=wf_element_value.input,
                        parameter=wf_element_value.parameter,
                        cancel_condition=wf_element_value.cancel_condition,
                        init=wf_element_value.init,
                        cycle_time=wf_element_value.cycle_time,
                        element_workflow=wf_element_value.element_workflow,
                        file_path=wf_element_value.path,
                        dd_path=wf_element_value.data_dictionary,
                    )

                    for input_name in wf_objects[wf_element_name].input:
                        pass

                        for parameter_name in wf_objects[wf_element_name].parameter:
                            pass

                        #     sim_result = simunit_objects[wf_element_name].run_simulation(
                        #             data=sim_input, parameter=sim_parameter
                        #         )

                # TODO: elif wf_element_value.type == "custom":
                #     wf_objects[wf_element_name] = {}

        # # TODO: if object not needed anymore
        # # drop it

        # # evaluation of the objects in the workflow
        # for wf_element_name, wf_element_value in ares_wf.workflow.items():
        # # handle "data" workflow elements
        # if wf_element_value.type == "data":
        #     # read mode: create data objects for each path in the workflow element
        #     if wf_element_value.mode == "read":
        #         wf_objects[wf_element_name] = {}

        #         for data_path in wf_element_value.path:
        #             wf_objects[wf_element_name][data_path] = Data(
        #                 file_path=data_path,
        #                 base_wf_element_name=wf_element_name,
        #                 source=wf_element_value.source,
        #                 step_size_init_ms=wf_element_value.cycle_time,
        #             )

        #     # write mode: export data from data objects
        #     elif wf_element_value.mode == "write":
        #         ares_wf.workflow[wf_element_name].path = []
        #         for data_value in data_objects[
        #             wf_element_value.element_input_workflow[0]
        #         ]:
        #             output_file_path = data_value.write_out(
        #                 dir_path=output_path,
        #                 output_format=wf_element_value.output_format,
        #                 meta_data=meta_data,
        #                 element_input_workflow=wf_element_value.element_input_workflow,
        #                 source=wf_element_value.source,
        #             )
        # ares_wf.workflow[wf_element_name].path.append(output_file_path)

        # # handle "parameter" workflow elements
        # if wf_element_value.type == "parameter":
        #     if "source" not in wf_element_value:
        #         wf_element_value.source = ["all"]

        #     # read mode: create parameter object for each path in the workflow element
        #     if wf_element_value.mode == "read":
        #         parameter_objects[wf_element_name] = []
        #         for parameter_path in wf_element_value.path:
        #             parameter_objects[wf_element_name].append(
        #                 Parameter(
        #                     file_path=parameter_path,
        #                     base_wf_element_name=wf_element_name,
        #                 )
        #             )

        #     # write mode: export parameter from parameter objects
        #     elif wf_element_value.mode == "write":
        #         ares_wf.workflow[wf_element_name].path = []
        #         for parameter_value in parameter_objects[
        #             wf_element_value.element_parameter_workflow[0]
        #         ]:
        #             output_file_path = parameter_value.write_out(
        #                 dir_path=output_path,
        #                 output_format=wf_element_value.output_format,
        #                 meta_data=meta_data,
        #                 element_parameter_workflow=wf_element_value.element_parameter_workflow,
        #                 source=wf_element_value.source,
        #             )
        #             ares_wf.workflow[wf_element_name].path.append(output_file_path)

        # # handle "sim_unit" workflow elements
        # if wf_element_value.type == "sim_unit":
        #     simunit_objects[wf_element_name] = SimUnit(
        #         file_path=wf_element_value.path,
        #         dd_path=wf_element_value.data_dictionary,
        #     )

        #     # finding all relevant input and parameter objects that should be evaluated
        #     data_objects[wf_element_name] = {}
        #     for input in wf_element_value.input:
        #         data_objects[wf_element_name][input] = copy.deepcopy(
        #             data_objects[input]
        #         )
        #     data_references = find_objects_and_get_references(
        #         data_objects[wf_element_name], Data
        #     )

        #     parameter_objects[wf_element_name] = {}
        #     for parameter in wf_element_value.parameter:
        #         parameter_objects[wf_element_name][parameter] = copy.deepcopy(
        #             parameter_objects[parameter]
        #         )
        #     parameter_references = find_objects_and_get_references(
        #         parameter_objects[wf_element_name], Parameter
        #     )

        #     # run simulation for each original data source- and parameter variant
        #     for data_reference in data_references:
        #         data_value, data_container, _, data_idx = data_reference
        #         sim_input = data_value.get(step_size_ms=wf_element_value.cycle_time)
        #         data_container[data_idx] = {}

        #         for parameter_reference in parameter_references:
        #             parameter_value, _, parameter_key, _ = parameter_reference
        #             sim_parameter = parameter_value.get()

        #             if parameter_key not in data_container[data_idx]:
        #                 data_container[data_idx][parameter_key] = []

        #             data_container[data_idx][parameter_key].append(
        #                 simunit_objects[wf_element_name].run_simulation(
        #                     data=sim_input, parameter=sim_parameter
        #                 )
        #             )

        # # handle "custom" workflow elements
        # if wf_element_value.type == "custom":
        #     custom_objects[wf_element_name] = {}

        ares_wf.write_out(output_path=output_path)

        logger.info("ARES pipeline successfully finished.")

    except Exception as e:
        logger.error(f"Error while executing ARES pipeline: {e}")


def find_objects_and_get_references(structure, target_type, key=None, results=None):
    """
    Recursively searches through nested structures and returns a list of tuples.
    Each tuple contains (found_object, parent_container, key_or_index).

    Args:
        structure: The current dict, list, or object being searched.
        target_type: The type of object to find.
        results: A list to store the found object and its context.

    Returns:
        A list of (object, parent_container, key_or_index) tuples.
    """
    if results is None:
        results = []

    if isinstance(structure, dict):
        for key, value in structure.items():
            find_objects_and_get_references(value, target_type, key, results)

    elif isinstance(structure, list):
        for i in range(len(structure)):
            element = structure[i]

            if isinstance(element, target_type):
                results.append((element, structure, key, i))

            find_objects_and_get_references(element, target_type, key, results)

    return results
