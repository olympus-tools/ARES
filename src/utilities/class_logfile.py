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

debugging = True

class Logfile:
    def __init__(self, file_path: str):
        """
        Creates a new logfile
        
        :parameter file_path: The path to the logfile."""
        self.file_path = file_path
        if not os.path.exists(self.file_path):
            self.create_logfile()

    def create_logfile(self):
        """Creates a new logfile"""

        directory = os.path.dirname(self.file_path)
        if not os.path.exists(directory):
            os.makedirs(directory) 
            
        with open(self.file_path, 'w', encoding='utf-8') as file:
            file.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Logfile created.\n")
        self.write(f"Created new logfile: {self.file_path}")

    def write(self, message: str, level: str = "INFO"):
        """Writes a message to the logfile and prints it to command line, with level-based formatting.

        :parameter message: Text to be written to the logfile and console.
        :parameter level: Logging level: 'INFO', 'WARNING', or 'ERROR'."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        prefix = ""
        color_code = ""

        # Determine prefix and color based on level
        if level.upper() == "WARNING":
            prefix = "Warning: "
            color_code = "\033[93m"  # Yellow
        elif level.upper() == "ERROR":
            prefix = "Error: "
            color_code = "\033[91m"  # Red
        else:
            color_code = "\033[0m"   # Default
            
        if level.upper() in ["INFO", "WARNING", "ERROR"] or (debugging and level.upper() in ["DEBUG"]):
            log_message = f"[{timestamp}] {prefix}{message}\n"

            # Write to file
            with open(self.file_path, 'a', encoding='utf-8') as file:
                file.write(log_message)

            # Print with color
            print(f"{color_code}[{timestamp}] {prefix}{message}\033[0m")

            # Raise exception on error
            if level.upper() == "ERROR":
                raise RuntimeError(message)
