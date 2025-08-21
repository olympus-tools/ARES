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
import argparse
from ares.models.pipeline import pipeline
from ares.models.logfile import Logfile

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="ares.py starts a the ares pipeline")
    parser.add_argument("--workflow", type=str, help="Absolute path to the workflow *.json file.")
    parser.add_argument("--output_path", type=str, help="Absolute path to the output directory.", default=None)
    args = parser.parse_args()

    logfile_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "log", "simulation.log"
    )
    logfile = Logfile(logfile_path)

    if args.workflow is not None:
        pipeline(wf_path=args.workflow, output_path=args.output_path, logfile=logfile)
