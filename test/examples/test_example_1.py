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

import subprocess
from pathlib import Path

import pytest


def test_ares_pipeline_example_1(tmp_path):
    """
    Executes an ARES pipeline example and asserts its successful completion
    and the absence of errors.
    """

    # Define paths based on project structure
    ares_executable = Path(".venv/bin/ares").resolve()
    workflow_file = Path("examples/workflow/workflow_example_1.json").resolve()

    # Create a temporary output directory for the test
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    # Command to execute, matching the VS Code configuration
    command = [
        str(ares_executable),
        "pipeline",
        "--workflow",
        str(workflow_file),
        "--output",
        str(output_dir),
        "--log-level",
        "10",
    ]

    # Execute the command without checking the return code
    result = subprocess.run(command, capture_output=True, text=True, timeout=120)

    # Assert that no errors were printed to stderr
    # An empty stderr is a strong indicator of a clean run.
    assert not result.stderr, (
        f"ARES reported errors on stderr. "
        f"Return code was {result.returncode}.\n"
        f"Stderr:\n---\n{result.stderr}\n---\n"
        f"Stdout:\n---\n{result.stdout}\n---\n"
    )

    # Assert successful completion based on a specific output string
    # Adjust this string to match the actual success message from ARES.
    success_string = "ARES pipeline successfully finished."

    assert success_string in result.stdout, (
        f"Success string '{success_string}' not found in output. "
        f"Return code was {result.returncode}.\n"
        f"Full stdout:\n---\n{result.stdout}\n---\n"
        f"Stderr:\n---\n{result.stderr}\n---\n"
    )
