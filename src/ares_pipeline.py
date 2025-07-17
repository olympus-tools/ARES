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
# Licensed under the GNU LGPLv3 License. You may obtain a copy of the 
# License at
#
#     https://github.com/AndraeCarotta/ARES/blob/master/LICENSE
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""

import os
from datetime import datetime
from . import ares_globals
from .utilities.class_datasource import DataSource
from .utilities.class_workflow import Workflow
from .utilities.class_simunit import SimUnit
#from utilities.class_dataset import Parameters

def ares_pipeline(file_path: str):

    ############## TODO: tmp ##############
    file_path = "/home/andrae/Dokumente/10_git/20_ARES/example/workflow.json"
    #datasource_read_path = "/home/andrae/Dokumente/10_git/20_ARES/example/datasource_1.mf4"
    #datasource_write_path = "/home/andrae/Dokumente/10_git/20_ARES/example/Testoutput.mf4"
    function1_lib_path = "/home/andrae/Dokumente/10_git/20_ARES/example/function1/wrapper1.so"
    function1_dd_path =  "/home/andrae/Dokumente/10_git/20_ARES/example/function1/function1_dd.json"

    ares_globals.logfile.write("ARES pipeline is starting...")

    ares_wf = Workflow(file_path = file_path)

    data_source_objects = {}
    param_objects = {}
    simunit_objects = {}
    custom_objects = {}

    for wf_name, wf_value in ares_wf.workflow.items():

        #TODO: if object not needed anymore
            #drop opject

        if wf_value["type"] == "data_source":
            if wf_value["mode"] == "read":
                for data_source_file in wf_value["path"]:
                    data_source_objects[wf_name] = DataSource(file_path = data_source_file)
            elif wf_value["mode"] == "write":
                for input in wf_value["input"]:
                    data_source_objects[wf_name].write_out(file_path = wf_value["path"], sources = input)

        if wf_value[type] == "parameters":
            pass

        if wf_value[type] == "sim_unit":
            pass

        if wf_value[type] == "custom":
            pass

    # writing out modified workflow json file at the end of the pipeline
    directory, filename = os.path.split(file_path)
    name, extension = os.path.splitext(filename)
    new_filename = f"{name}_out_{datetime.now().strftime("%Y%m%d%H%M%S")}{extension}"
    file_path_out = os.path.join(directory, new_filename)
    ares_wf.write_out(file_path = file_path_out)
      
    ares_globals.logfile.write("ARES pipeline successfully finished.")

    #TODO: remove this stuff
    #ares_wf.write_out(file_path = workflow_write_path)
    #Test_meas = DataSource(file_path = datasource_read_path, sources = ['CAN-Monitoring:3', 'FETK:1', 'FETK:2'])
    #Test_meas.write_out(file_path = datasource_write_path, sources = ['base'])
    #Test_simunit = SimUnit(file_path = function1_lib_path, dd_path = function1_dd_path)
    #tmp_measure = {"timestamps":[0,1,2,3,4,5]}
    #SimResult = Test_simunit.run_simulation(simulation_input = tmp_measure)