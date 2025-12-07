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

import datetime
import os


def eval_output_path(
    output_hash: str,
    output_dir: str,
    output_format: str,
    element_name: str,
) -> str:
    """Generate output file path with timestamp to prevent overwriting.

    Creates a timestamped filename in the format: {element_name}_{hash}_{YYYYMMDDHHMMSS}.{format}
    and ensures the output directory exists.

    Args:
        hash: Content hash to include in filename
        output_dir: Output directory path (will be created if not exists)
        output_format: File format/extension (without dot, e.g., 'dcm', 'json')
        element_name: Element name to include in filename

    Returns:
        str: Complete absolute file path
    """
    os.makedirs(
        output_dir, exist_ok=True
    )  # TODO: should it be somewheere else? => Jonas says yes
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    new_file_name = f"{element_name}_{output_hash[:8]}_{timestamp}.{output_format}"
    output_path = os.path.join(output_dir, new_file_name)

    return output_path
