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

from typing import Any

from typeguard import typechecked

from ares.core.data.mf4_interface import mf4_handler
from ares.core.storage_handler import StorageHandler
from ares.pydantic_models.workflow_model import DataElement
from ares.utils.decorators import safely_run
from ares.utils.logger import create_logger

logger = create_logger(__name__)


class DataHandler(StorageHandler[DataElement, Any]):
    """DataHandler implementation based on StorageHandler.

    This class serves as a placeholder/template for future data handling implementation,
    following the pattern established by ParameterHandler.
    """

    def __init__(self):
        super().__init__()

    @safely_run(
        default_return=None,
        message="Oops, something went terribly wrong. Check your workflow json.",
        log=logger,
    )
    @typechecked
    def handler(
        self,
        element_name: str,
        element_value: DataElement,
        input_hash_list: list[list[str]] | None = None,
        output_dir: str | None = None,
        **kwargs,
    ) -> list[str]:
        """Perform a data interface and return a list of hashes for affected data objects.

        Args:
            element_name: Name of the element being processed
            element_value: DataElement containing mode and configuration
            input_hash_list: List of data hashes for writing operations
            output_dir: Output directory for writing operations

        Returns:
            list[str]: List of hashes for affected data objects.
        """
        output_hash_list: list[str] = []

        for file_path in element_value.path:
            if file_path.endswith(".mf4"):
                match element_value.mode:
                    case "read":
                        tmp_handler = mf4_handler(
                            name=element_name,
                            file_path=file_path,
                            mode=element_value.mode,
                        )
                        self.data.update({tmp_handler.hash: tmp_handler})

                    case "write":
                        for element_input_hash in input_hash_list:
                            handler_inputs = self.data.get(element_input_hash)

                            for data_handler in handler_inputs:
                                file_path_out: str = (
                                    file_path.replace(".mf4", "_")
                                    + data_handler.hash
                                    + ".mf4"
                                )

                                tmp_handler = mf4_handler(
                                    name=element_name,
                                    file_path=file_path_out,
                                    mode=element_name.mode,
                                )
                                tmp_handler.write(handler_inputs.get())
                                tmp_handler.save_file(overwrite=True)

            elif file_path.endswith(".parquet"):
                logger.error(
                    "Evaluation of .parquet input/output is not implemented yet."
                )
                raise ValueError("Not implemented yet.")
            elif file_path.endswith(".mat"):
                logger.error("Evaluation of .mat input/output is not implemented yet.")
                raise ValueError("Not implemented yet.")
            else:
                logger.error(f"Unknown file format for file: {file_path}")
                raise ValueError("Unknown file format.")
