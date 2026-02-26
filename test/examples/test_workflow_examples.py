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

Copyright 2025 olympus-tools contributors. Dependencies and licenses
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

import pytest


@pytest.mark.parametrize(
    "workflow_file",
    [
        "workflow/data_interface/data_caching.wf.json",
        "workflow/data_interface/data_labelfilter.wf.json",
        # "workflow/data_interface/data_convertion.wf.json", TODO: implement data convertion example
        "workflow/data_interface/data_resampling.wf.json",
        "workflow/data_interface/data_merge.wf.json",
        "workflow/data_interface/data_vstack.wf.json",
        "workflow/parameter_interface/param_caching.wf.json",
        "workflow/parameter_interface/param_convertion.wf.json",
        "workflow/parameter_interface/param_merge.wf.json",
        "workflow/parameter_interface/param_labelfilter.wf.json",
        "workflow/plugin/plugin_manipulation.wf.json",
        "workflow/sim_unit/simunit_dependencies.wf.json",
        "workflow/sim_unit/simunit_interface_alt.wf.json",
        "workflow/sim_unit/simunit_interface_alt_default.wf.json",
        "workflow/sim_unit/simunit_interface_alt_value.wf.json",
        "workflow/sim_unit/simunit_interface_std.wf.json",
        "workflow/sim_unit/simunit_vstack.wf.json",
    ],
)
def test_workflow_example(workflow_file: str, tmp_path):
    """Test all workflow examples from the examples Makefile.

    This test executes each workflow and asserts its successful completion
    and the absence of errors.

    Args:
        workflow_file (str): Relative path to the workflow file from examples directory.
        tmp_path (Path): pytest fixture providing temporary directory.
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    python_executable = (
        project_root / ".venv" / ("Scripts" if os.name == "nt" else "bin") / "python"
    )
    workflow_path = project_root / "examples" / workflow_file

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    command = [
        str(python_executable),
        "-m",
        "ares",
        "pipeline",
        "--workflow",
        str(workflow_path),
        "--output",
        str(output_dir),
        "--log-level",
        "10",
    ]

    env = dict(**os.environ)
    env["PYTHONPATH"] = str(project_root)

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=120,
        cwd=project_root,
        env=env,
    )

    clean_stdout = re.sub(r"\x1b\[[0-9;]*m", "", result.stdout)
    clean_stderr = re.sub(r"\x1b\[[0-9;]*m", "", result.stderr)

    assert result.returncode == 0, (
        f"Pipeline failed with return code {result.returncode}:\n"
        f"STDOUT:\n{clean_stdout}\n"
        f"STDERR:\n{clean_stderr}"
    )

    assert "ERROR" not in clean_stdout, f"Pipeline reported ERRORs:\n{clean_stdout}"

    success_string = "ARES pipeline successfully finished."
    assert success_string in clean_stdout, (
        f"Success string '{success_string}' not found in output.\n"
        f"STDOUT:\n{clean_stdout}"
    )
