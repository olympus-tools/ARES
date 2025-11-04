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

from typeguard import typechecked

from ares.models.workflow_model import DataElement
from ares.utils.data.ares_interface import AresDataInterface
from ares.utils.data.mf4_interface import mf4_handler
from ares.utils.decorators import safely_run
from ares.utils.logger import create_logger

logger = create_logger("data")


@typechecked
@safely_run(
    default_return=[],
    message="Oops, something went terribly wrong. Check your workflow json.",
    log=logger,
)
def get_data_handler(
    name: str,
    data_element: DataElement,
    data_object_list: list[AresDataInterface],
) -> list[AresDataInterface] | None:
    """Function initializes "ares_interface" depending on the  file-type requested.
    FACTORY!
    """
    dh_out = []

    # XXX: to get_data_handler does what the example wants, think about:
    #     - considering "data_object_list" -> DataElement -> function/object
    #     - make this a generic function for all data_handlers -> doesn't need to be file dependent?
    for file_path in data_element.path:
        if file_path.endswith(".mf4"):
            if data_element.mode == "read":
                dh_out.append(
                    mf4_handler(name=name, file_path=file_path, mode=data_element.mode)
                )
            elif data_element.mode == "write":
                for dh_in in data_element.input:
                    data_in = [data for data in data_object_list if data.name == dh_in]
                    for d_in in data_in:
                        new_file_path = (
                            file_path.replace(".mf4", "_") + d_in.hash + ".mf4"
                        )
                        dh_out.append(
                            mf4_handler(
                                name=name,
                                file_path=new_file_path,
                                mode=data_element.mode,
                            )
                        )
                        dh_out[-1].write(d_in.get())

                        # TODO: can i move this in the destructor?
                        # in my concept this would be executed by the "plugin" -> now this MUST BE done by the dh function
                        dh_out[-1].save_file()

        elif file_path.endswith(".parquet"):
            logger.error("Evaluation of .parquet input/output is not implemented yet.")
            raise ValueError("Not implemented yet.")
        elif file_path.endswith(".mat"):
            logger.error("Evaluation of .mat input/output is not implemented yet.")
            raise ValueError("Not implemented yet.")
        else:
            logger.error(
                f"Unknown file format for file: {file_path} or {output_format}"
            )
            raise ValueError("Unknown file format.")

    return dh_out
