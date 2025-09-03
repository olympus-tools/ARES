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
from datetime import datetime
from typeguard import typechecked

debugging = False


class Logfile:
    @typechecked
    def __init__(self, file_path: str):
        """
        Creates a new logfile.

        Args:
            file_path (str): The path to the logfile.
        """
        self.file_path = file_path
        if not os.path.exists(self.file_path):
            self.create_logfile()

    @typechecked
    def create_logfile(self):
        """
        Creates a new logfile.
        """
        directory = os.path.dirname(self.file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)

        with open(self.file_path, "w", encoding="utf-8") as file:
            file.write(
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Logfile created.\n"
            )
        self.write(f"Created new logfile: {self.file_path}")

    @typechecked
    def write(self, message: str, level: str = "INFO"):
        """
        Writes a message to the logfile and prints it to the command line, with level-based formatting.

        Args:
            message (str): Text to be written to the logfile and console.
            level (str): Logging level: 'INFO', 'WARNING', or 'ERROR'.

        Raises:
            RuntimeError: If the logging level is 'ERROR', a `RuntimeError` is raised with the provided message.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prefix = ""
        color_code = ""

        # Determine prefix and color based on level
        if level.upper() == "WARNING":
            prefix = "[WARNING] "
            color_code = "\033[93m"  # Yellow
        elif level.upper() == "ERROR":
            prefix = "[ERROR] "
            color_code = "\033[91m"  # Red
        else:
            color_code = "\033[0m"  # Default

        if level.upper() in ["INFO", "WARNING", "ERROR"] or (
            debugging and level.upper() in ["DEBUG"]
        ):
            log_message = f"[{timestamp}] {prefix}{message}\n"

            # Write to log file
            with open(self.file_path, "a", encoding="utf-8") as file:
                file.write(log_message)

            # Print to console with color
            print(f"{color_code}[{timestamp}] {prefix}{message}\033[0m")

            # Raise exception on error
            if level.upper() == "ERROR":
                raise RuntimeError(message)
