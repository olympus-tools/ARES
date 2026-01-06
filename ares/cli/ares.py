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

Copyright 2025 Andrä Carotta

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

For details, see: https://github.com/olympus-tools/ARES#7-license
"""

import getpass
import logging

import click

from ares.core.pipeline import pipeline
from ares.utils.logger import create_logger
from ares.version import __version__

meta_data = {"username": getpass.getuser(), "version": __version__}


@click.group()
@click.option(
    "-v",
    "--version",
    is_flag=True,
    is_eager=True,
    expose_value=False,
    callback=lambda ctx, param, value: (
        click.echo(f"ARES version {__version__}") or ctx.exit()
    )
    if value
    else None,
    help="Show the installed ARES version.",
)
def cli():
    """Automated Rapid Embedded Simulation (ARES) CLI"""
    pass


@cli.command(name="pipeline", help="Starts the ARES simulation pipeline.")
@click.option(
    "-wf",
    "--workflow",
    required=True,
    type=click.Path(exists=True, dir_okay=False),
    help="Absolute file path of to the workflow *.json file.",
)
@click.option(
    "-o",
    "--output",
    default=None,
    type=click.Path(file_okay=False),
    help="Absolute path to the output directory.",
)
@click.option(
    "--log-level",
    default=logging.WARNING,
    help="""\b
    Setting log level for root logger via integer value:
    10 = DEBUG
    20 = INFO
    30 = WARNING (default)
    40 = ERROR
    50 = CRITICAL
    """,
)
def pipeline_command(workflow, output, log_level):
    ares_logger = create_logger(level=log_level)

    pipeline(wf_path=workflow, output_dir=output, meta_data=meta_data)
