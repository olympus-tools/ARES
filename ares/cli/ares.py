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

import getpass

import click

from ares.core.pipeline import pipeline
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
def pipeline_command(workflow, output):
    pipeline(wf_path=workflow, output_path=output, meta_data=meta_data)


if __name__ == "__main__":
    cli()
