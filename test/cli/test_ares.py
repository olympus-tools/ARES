r"""
________________________________________________________________________
|                                                                      |
|               $$$$$$\  $$$$$$$\  $$$$$$$$\  $$$$$$\                  |
|              $$  __$$\ $$  __$$\ $$  _____|$$  __$$\                 |
|              $$ /  $$ |$$ |  $$ |$$ |      $$ /  \__|                |
|              $$$$$$$$ |$$$$$$$  |$$$$$\    \$$$$$$\                 |
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

import logging
from unittest.mock import patch

from click.testing import CliRunner

from ares.cli.ares import __version__, cli


# TEST: CLI version option
def test_cli_version_option():
    """Tests that the version option prints the installed ARES version."""
    result = CliRunner().invoke(cli, ["--version"])

    assert result.exit_code == 0
    assert result.output == f"ARES version {__version__}\n"


# TEST: pipeline command
def test_pipeline_command_delegates_to_logger_and_pipeline(tmp_path):
    """
    Tests that the pipeline command configures logging and forwards its options.

    Args:
        tmp_path (Path): Temporary directory used for CLI path arguments.
    """
    workflow = tmp_path / "workflow.json"
    output = tmp_path / "output"
    log_dir = tmp_path / "logs"
    workflow.touch()

    with (
        patch("ares.cli.ares.create_logger") as create_logger,
        patch("ares.cli.ares.pipeline") as pipeline,
        patch("ares.cli.ares.logging.getLogger") as get_logger,
    ):
        result = CliRunner().invoke(
            cli,
            [
                "pipeline",
                "--workflow",
                str(workflow),
                "--output",
                str(output),
                "--log-dir",
                str(log_dir),
                "--log-level",
                "10",
            ],
        )

    assert result.exit_code == 0
    create_logger.assert_called_once_with(log_dir=log_dir, level=logging.DEBUG)
    get_logger.return_value.setLevel.assert_called_once_with(logging.DEBUG)
    pipeline.assert_called_once_with(
        wf_path=workflow,
        output_dir=output,
        meta_data={
            "username": pipeline.call_args.kwargs["meta_data"]["username"],
            "version": __version__,
        },
    )


# TEST: pipeline command validation
def test_pipeline_command_requires_existing_workflow():
    """Tests that the pipeline command rejects a missing workflow file."""
    result = CliRunner().invoke(cli, ["pipeline", "--workflow", "missing.json"])

    assert result.exit_code != 0
    assert "does not exist" in result.output
