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

from typing import Any, Dict, List, Optional

from ares.pydantic_models.workflow_model import DataElement
from typeguard import typechecked

from ares.core.storage_handler import StorageHandler
from ares.utils.logger import create_logger

logger = create_logger(__name__)


class DataHandler(StorageHandler[DataElement, Any]):
    """Dummy DataHandler implementation based on StorageHandler.

    This class serves as a placeholder/template for future data handling implementation,
    following the pattern established by ParameterHandler.
    """

    @typechecked
    def __init__(self):
        super().__init__()
        self.data_dict: Dict[str, Any] = self.data
        self._element_name: Optional[str] = None

    @typechecked
    def interface(
        self,
        element_name: str,
        element_value: DataElement,
        input_hash_list: Optional[List[List[str]]] = None,
        output_dir: Optional[str] = None,
        **kwargs,
    ) -> List[str]:
        """Perform a data interface and return a list of hashes for affected data objects.

        Args:
            element_name: Name of the element being processed
            element_value: DataElement containing mode and configuration
            input_hash_list: List of data hashes for writing operations
            output_dir: Output directory for writing operations

        Returns:
            List[str]: List of hashes for affected data objects.
        """
        self._element_name = element_name
        output_hash_list: List[str] = []

        try:
            match element_value.mode:
                case "read":
                    logger.info(
                        f"{self._element_name}: Dummy read operation for {element_value.file_path}"
                    )
                    output_hash_list = self._load(file_path=element_value.file_path)
                case "write":
                    if input_hash_list:
                        logger.info(f"{self._element_name}: Dummy write operation")
                        self._write(
                            hash_list=input_hash_list,
                            output_format=element_value.output_format,
                            output_dir=output_dir,
                        )

            return output_hash_list

        except Exception as e:
            logger.warning(
                f"{self._element_name}: Data interface operation failed: {e}"
            )
            return []

    @typechecked
    def _load(self, file_path: List[str], **kwargs) -> Optional[List[str]]:
        """Dummy load implementation.

        Args:
            file_path: List of file paths to load from

        Returns:
            Optional[List[str]]: List of content hashes
        """
        return []

    @typechecked
    def _write(
        self,
        hash_list: List[List[str]],
        output_format: str,
        output_dir: str,
        **kwargs,
    ) -> None:
        """Dummy write implementation.

        Args:
            hash_list: Nested list of content hashes to write
            output_format: Target output format
            output_dir: Output directory path
        """
        pass
