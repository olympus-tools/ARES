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

import argparse
from src.ares_pipeline import ares_pipeline

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="ares.py starts a the ares pipeline")
    parser.add_argument("--workflow", type=str, help="Absolute path to the workflow *.json file.")
    args = parser.parse_args()

    ############## TODO: remove the next line ##############
    args.workflow = "/home/andrae/Dokumente/10_git/20_ARES/example/workflow_example2.json"
    
    if args.workflow is not None:
        ares_pipeline(wf_path = args.workflow)