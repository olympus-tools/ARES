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

import json
import os
from abc import ABC, abstractmethod
from typing import ClassVar, Dict, List, Optional

from typeguard import typechecked

from ares.interface.parameter.ares_parameter import AresParameter
from ares.pydantic_models.workflow_model import ParameterElement
from ares.utils.eval_output_path import eval_output_path
from ares.utils.hash import sha256_string
from ares.utils.logger import create_logger

logger = create_logger(__name__)


class AresParamInterface(ABC):
    """Abstract base class for parameter interfaces in ARES.

    This interface defines the contract for all parameter handlers in ARES.
    Implements flyweight pattern based on content hash (sha256) to ensure
    that identical parameter sets share the same instance.

    The flyweight pattern is implemented via __new__ - identical file contents
    will automatically return the same cached instance.
    """

    cache: ClassVar[Dict[str, "AresParamInterface"]] = {}
    _handlers: ClassVar[Dict[str, type["AresParamInterface"]]] = {}

    @typechecked
    def __new__(
        cls,
        file_path: Optional[str] = None,
        parameters: Optional[List[AresParameter]] = None,
        **kwargs,
    ):
        """Implement flyweight pattern based on content hash.

        Creates a new instance only if the content hash doesn't exist yet.
        Otherwise returns the existing cached instance.

        Args:
            file_path: Path to the parameter file to load
            parameters: Optional list of AresParameter objects for initialization
            **kwargs: Additional arguments for subclass initialization

        Returns:
            New or cached instance based on content hash
        """
        # neither file_path nor parameters provided - create uncached instance
        if file_path is None and parameters is None:
            return super().__new__(cls)

        # Load parameters from file if file_path provided
        if file_path is not None:
            temp_instance = object.__new__(cls)
            cls.__init__(temp_instance, file_path=file_path, **kwargs)
            parameters = temp_instance.get(**kwargs)

        # calculate hash from parameters
        content_hash = cls._calculate_hash(parameters=parameters, **kwargs)

        # return cached instance if hash already exists
        if content_hash in cls.cache:
            return cls.cache[content_hash]

        # create new instance and add to cache
        instance = super().__new__(cls)
        object.__setattr__(instance, "hash", content_hash)
        cls.cache[content_hash] = instance
        return instance

    @typechecked
    def __init__(self, file_path: Optional[str], **kwargs):
        """Initialize base attributes for all parameter handlers.

        This method should be called by all subclass __init__ methods using super().__init__().

        Args:
            file_path: Path to the parameter file to load
            **kwargs: Additional arguments passed to subclass
        """
        object.__setattr__(self, "_file_path", file_path)
        object.__setattr__(self, "dependencies", kwargs.get("dependencies", []))

    @classmethod
    @typechecked
    def register(
        cls, extension: str, handler_class: type["AresParamInterface"]
    ) -> None:
        """Register a handler for a specific file extension.

        Args:
            extension: File extension including dot (e.g., '.dcm', '.json')
            handler_class: Handler class to use for this extension
        """
        cls._handlers[extension.lower()] = handler_class

    @classmethod
    @typechecked
    def wf_element_handler(
        cls,
        element_name: str,
        element_value: ParameterElement,
        input_hash_list: Optional[List[List[str]]] = None,
        output_dir: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Central handler method for parameter operations.

        Decides between _load() and save() based on mode from ParameterElement.

        Args:
            element_name: Name of the element being processed
            element_value: ParameterElement containing mode, file_path, and output_format
            input_hash_list: Nested list of parameter hashes for writing operations
            output_dir: Output directory path for writing operations
            **kwargs: Additional format-specific arguments
        """

        match element_value.mode:
            case "read":
                for fp in element_value.file_path:
                    cls.create(file_path=fp, **kwargs)
                return None

            case "write":
                if not input_hash_list or not output_dir:
                    return None

                target_extension = f".{element_value.output_format}"
                target_handler_class = cls._handlers.get(target_extension)

                for wf_element_hash_list in input_hash_list:
                    for output_hash in wf_element_hash_list:
                        if output_hash in cls.cache:
                            source_instance = cls.cache.get(output_hash)

                            parameters = source_instance.get(
                                label_filter=element_value.label_filter, **kwargs
                            )

                            target_instance = target_handler_class.__new__(
                                target_handler_class, file_path=None
                            )
                            target_handler_class.__init__(
                                target_instance, file_path=None
                            )

                            target_instance.add(parameters=parameters, **kwargs)

                            output_path = eval_output_path(
                                output_hash=output_hash,
                                output_dir=output_dir,
                                output_format=element_value.output_format,
                                element_name=element_name,
                            )

                            target_instance._save(output_path=output_path, **kwargs)

                return None

    @classmethod
    @typechecked
    def create(cls, file_path: Optional[str] = None, **kwargs) -> "AresParamInterface":
        """Create parameter handler with automatic format detection.

        Uses file extension to select appropriate handler.
        All handlers share the same flyweight cache.

        Args:
            file_path: Path to the parameter file to load. If None, defaults to JSON handler.
            **kwargs: Additional format-specific arguments

        Returns:
            AresParameter handler instance (may be cached)
        """

        if file_path is None:
            ext = ".json"
        else:
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()

        handler_class = cls._handlers[ext]
        return handler_class(file_path=file_path, **kwargs)

    @staticmethod
    @typechecked
    def _calculate_hash(
        parameters: List[AresParameter],
        **kwargs,
    ) -> Optional[str]:
        """Calculate hash from parameter list.

        This method is used for cache lookup. It always calculates hash
        from a parameter list for consistent hash generation.

        Converts parameters to a normalized dictionary format, then serializes
        to JSON with sorted keys to ensure consistent hash generation for
        identical parameter content.

        Args:
            parameters: List of AresParameter objects
            **kwargs: Additional format-specific arguments (unused)

        Returns:
            SHA256 hash string of the content, or None on error
        """
        temp_param_dict = {}
        temp_param_dict["metadata"] = {"type": "AresParamInterface"}
        for param in parameters:
            temp_param_dict[param.label] = {
                "description": param.description
                if param.description is not None
                else "",
                "unit": param.unit if param.unit is not None else "",
                "value": param.value.tolist(),
            }
        param_json = json.dumps(temp_param_dict, sort_keys=True)
        return sha256_string(param_json)

    @abstractmethod
    def get(
        self, label_filter: list[str] | None = None, **kwargs
    ) -> List[AresParameter]:
        """Get parameters from the interface.

        Args:
            label_filter (list[str] | None): List of parameter names to retrieve from the interface.
            **kwargs: Additional format-specific arguments

        Returns:
            List[AresParameter]: List of all AresParameter objects stored in the interface
        """
        pass

    @abstractmethod
    def add(self, parameters: List[AresParameter], **kwargs) -> None:
        """Add parameters to the interface.

        Args:
            parameters: List of AresParameter objects to add
            **kwargs: Additional format-specific arguments
        """
        pass

    @abstractmethod
    def _save(self, output_path: str, **kwargs) -> None:
        """Write parameters to file.

        Args:
            output_path: Absolute path where the parameter file should be written
            **kwargs: Additional format-specific arguments
        """
        pass
