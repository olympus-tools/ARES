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

Copyright 2025 olympus-tools contributors. Contributors to this project
are listed in the NOTICE file:

    https://github.com/olympus-tools/ARES/blob/master/NOTICE

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License:

    https://github.com/olympus-tools/ARES/blob/master/LICENSE
"""

import os
import re
import subprocess
from pathlib import Path


def test_ares_pipeline_example_2(tmp_path, caplog):
    """
    Executes an ARES pipeline example and asserts its successful completion
    and the absence of errors.
    """

    project_root = Path(__file__).resolve().parent.parent.parent
    python_executable = (
        project_root / ".venv" / ("Scripts" if os.name == "nt" else "bin") / "python"
    )
    workflow_file = project_root / "examples/workflow/workflow_example_2.json"

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    command = [
        str(python_executable),
        "-m",
        "ares",
        "pipeline",
        "--workflow",
        str(workflow_file),
        "--output",
        str(output_dir),
        "--log-level",
        "10",
    ]

    env = dict(**os.environ)
    env["PYTHONPATH"] = str(project_root)

    with caplog.at_level("DEBUG"):
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=project_root,
            env=env,
            check=True,
        )

    clean_stdout = re.sub(r"\x1b\[[0-9;]*m", "", result.stdout)

    assert "ERROR" not in clean_stdout, f"Pipeline reported ERRORs:\n{clean_stdout}"

    success_string = "ARES pipeline successfully finished."
    assert success_string in clean_stdout, (
        f"Success string '{success_string}' not found in output.\n{clean_stdout}"
    )
