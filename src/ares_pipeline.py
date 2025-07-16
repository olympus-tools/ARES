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
from . import ares_globals
from .utilities.class_measurement import Measurement
from .utilities.class_workflow import Workflow
from .utilities.class_simunit import SimUnit
#from utilities.class_dataset import Dataset

def ares_pipeline(file_path: str):

    ############## tmp ##############
    file_path = "/home/andrae/Dokumente/10_git/20_ARES/example/workflow.json"
    workflow_write_path = "/home/andrae/Dokumente/10_git/20_ARES/example/workflow_output.json"
    #measurement_read_path = "/home/andrae/Dokumente/10_git/20_ARES/example/PO983_PT1104_Mue_2024-01-31 17_23_41.mf4"
    #measurement_write_path = "/home/andrae/Dokumente/10_git/20_ARES/example/Testoutput.mf4"
    function1_lib_path = "/home/andrae/Dokumente/10_git/20_ARES/example/function1/wrapper1.so"
    function1_dd_path =  "/home/andrae/Dokumente/10_git/20_ARES/example/function1/function1_dd.json"
    ############## tmp ##############

    ares_globals.logfile.write("ARES pipeline is starting.")

    Test_wf = Workflow(file_path = file_path)
    Test_wf.write_out(file_path = workflow_write_path)
    #Test_meas = Measurement(file_path = measurement_read_path, sources = ['CAN-Monitoring:3', 'FETK:1', 'FETK:2'])
    #Test_meas.write_out(file_path = measurement_write_path, sources = ['base'])
    Test_simunit = SimUnit(file_path = function1_lib_path, dd_path = function1_dd_path)
    tmp_measure = {"timestamps":[0,1,2,3,4,5]}
    SimResult = Test_simunit.run_simulation(simulation_input = tmp_measure)
    
    ares_globals.logfile.write("ARES pipeline successfully finished.")