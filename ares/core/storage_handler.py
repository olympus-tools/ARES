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

import os
from abc import ABC, abstractmethod
from collections import UserDict
from datetime import datetime
from typing import Generic, List, Optional, TypeVar

from typeguard import typechecked

WfElementType = TypeVar("WfElementType")
InterfaceType = TypeVar("InterfaceType")


class StorageHandler(UserDict, ABC, Generic[WfElementType, InterfaceType]):
    """Abstract base class for storage handlers that manage collections of objects.

    This class defines the common interface and shared functionality for handlers
    that store, retrieve, and manage collections of data objects using hash-based
    caching and dictionary-like access patterns.

    All concrete implementations must provide their own loading, writing, and
    interface logic while inheriting the common dictionary operations.
    """

    @typechecked
    def __init__(self):
        """Initialize the storage handler with an empty dictionary for storing objects.

        UserDict provides self.data as the internal dictionary.
        """
        super().__init__()

    @abstractmethod
    @typechecked
    def handler(  # TODO: should it be called inferface?? => handler,...?
        self,
        element_name: str,
        element_value: WfElementType,
        input_hash_list: Optional[List[List[str]]] = None,
        output_dir: Optional[str] = None,
        **kwargs,
    ) -> List[str]:
        """Abstract method for performing interface operations.

        This method should handle the main interaction logic for the storage handler,
        such as coordinating load/write operations based on input parameters.

        Args:
            element_name: Name of the element being processed
            element_value: Configuration element (type varies by
                handler: ares/pydantic_models/workflow_model.py)
            input_hash_list: Optional list of hashes for write operations
            output_dir: Optional output directory for write operations
            **kwargs: Additional parameters specific to the handler type

        Returns:
            List[str]: List of hashes for affected objects.
        """
        pass

    @typechecked
    def _eval_output_path(
        self,
        hash: str,
        output_dir: str,
        output_format: str,
        element_name: str,
    ) -> str:
        """Generate output file path with timestamp to prevent overwriting.

        Creates a timestamped filename in the format: {hash}_{YYYYMMDDHHMMSS}.{format}
        and ensures the output directory exists.

        Args:
            hash: Content hash to use as base filename
            output_dir: Output directory path
            output_format: File format/extension (without dot)
            element_name: Optional element name for error logging

        Returns:
            Complete absolute file path, or None if an error occurs
        """
        # TODO: do we want to move this elsewhere?
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        new_file_name = f"{element_name}_{hash}_{timestamp}.{output_format}"
        output_path = os.path.join(output_dir, new_file_name)

        return output_path
