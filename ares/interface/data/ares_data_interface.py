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
from typing import ClassVar, Dict, List, Optional

import numpy as np
from typeguard import typechecked

from ares.interface.data.ares_signal import AresSignal
from ares.pydantic_models.workflow_model import DataElement
from ares.utils.eval_output_path import eval_output_path
from ares.utils.hash import sha256_string
from ares.utils.logger import create_logger

logger = create_logger(__name__)


class AresDataInterface(ABC):
    """Abstract base class for data interfaces in ARES.

    This interface defines the contract for all data handlers in ARES.
    Implements flyweight pattern based on content hash (sha256) to ensure
    that identical data objects share the same instance.

    The flyweight pattern is implemented via __new__ - identical file contents
    will automatically return the same cached instance.
    """

    cache: ClassVar[Dict[str, "AresDataInterface"]] = {}
    _handlers: ClassVar[Dict[str, type["AresDataInterface"]]] = {}

    @typechecked
    def __new__(
        cls,
        file_path: str | None = None,
        **kwargs,
    ):
        """Implement flyweight pattern based on content hash.

        Creates a new instance only if the content hash doesn't exist yet.
        Otherwise returns the existing cached instance.

        Args:
            file_path ( str ): Path to the signals file to load
            **kwargs: Additional arguments for subclass initialization

        Returns:
            New or cached instance based on content hash
        """
        # Neither file_path nor signals provided - create uncached instance
        if file_path is None:
            return super().__new__(cls)

        # Load signals from file if file_path provided
        temp_instance = object.__new__(cls)
        cls.__init__(temp_instance, file_path=file_path, **kwargs)

        # Calculate  from signals
        content_hash = cls._calculate_hash(file_path, **kwargs)

        # Return cached instance if hash already exists
        if content_hash in cls.cache:
            return cls.cache[content_hash]

        # Create new instance and add to cache
        cls.cache[content_hash] = temp_instance
        return temp_instance

    @typechecked
    def __init__(self, file_path: str | None, **kwargs):
        """Initialize base attributes for all data handlers.
        This method should be called by all subclass __init__ methods using super().__init__().

        Args:
            file_path ( str ): Path to the signals file to load
            **kwargs: Additional arguments passed to subclass
        """
        self._file_path = file_path if file_path is not None else ""
        self.dependencies: List[str] = kwargs.get("dependencies", [])

    @property
    def file_path(self) -> str | None:
        """File path to element to read/write. File can NOT exist."""
        return self._file_path

    @classmethod
    @typechecked
    def register(cls, extension: str, handler_class: type["AresDataInterface"]) -> None:
        """Register a handler for a specific file extension.

        Args:
            extension: File extension including dot (e.g., '.dcm', '.json')
            handler_class: Handler class to use for this extension
        """
        cls._handlers[extension.lower()] = handler_class

    @classmethod
    @typechecked
    # TODO: safely_run function candidate?
    def wf_element_handler(
        cls,
        element_name: str,
        element_value: DataElement,
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
                    cls.create(fp, **kwargs)
                return None

            case "write":
                if not input_hash_list or not output_dir:
                    return None

                target_extension = f".{element_value.output_format}"
                target_handler_class = cls._handlers.get(target_extension)

                for wf_element_hash_list in input_hash_list:
                    for output_hash in wf_element_hash_list:
                        source_instance = cls.cache.get(output_hash)

                        signals = source_instance.get(**kwargs)

                        target_instance = target_handler_class.__new__(
                            target_handler_class, file_path=None
                        )
                        target_handler_class.__init__(target_instance, file_path=None)

                        target_instance.add(signals, **kwargs)

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
    def create(cls, file_path: str | None = None, **kwargs) -> "AresDataInterface":
        """Create data handler with automatic format detection.

        Uses file extension to select appropriate handler.
        All handlers share the same flyweight cache.

        Args:
            file_path ( str ): Path to the measurement file to load. If None, defaults to MF4 handler.
            **kwargs: Additional format-specific arguments

        Returns:
            AresDataInterface handler instance (may be cached)
        """

        if file_path is None:
            ext = ".mf4"
        else:
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()

        handler_class = cls._handlers[ext]
        return handler_class(file_path=file_path, **kwargs)

    # XXX: Idea for later, should the hash function be abstact and calculated based on infromations provided by the intherited class after init?
    # + uniqueness of hash is easier applicable since attributes of the obj itself can be used, avaialable signals, lenght, timestamps
    # - for each new element type an implementation is necessary
    @typechecked
    @staticmethod
    def _calculate_hash(
        file_path: str,
        **kwargs,
    ) -> str | None:
        """Calculate hash from signal list.

        This method is used for cache lookup. It always calculates hash
        from a signal list for consistent hash generation.

        Converts signals to a normalized dictionary format, then serializes
        to JSON with sorted keys to ensure consistent hash generation for
        identical signal content.

        Args:
            file_path ( str ) : Path to the measurement file to load. If None, defaults to MF4 handler.
            **kwargs: Additional format-specific arguments (unused)

        Returns:
            SHA256 hash string of the content
        """
        return sha256_string(file_path)

    @staticmethod
    @typechecked
    def _resample(data: list[AresSignal], stepsize_ms: int) -> list[AresSignal]:
        """Resample all signals to a common time vector using linear interpolation.

        Args:
            data (list[AresSignal]): List of AresSignal objects to resample.
            stepsize_ms (int): Resampling step size in milliseconds.

        Returns:
            list[AresSignal]: List of resampled AresSignal objects with common time vector.
        """
        latest_start_time = float(0.0)
        earliest_end_time = np.inf

        # get timevector
        for sig in data:
            if len(sig.timestamps) > 0:
                latest_start_time = max(latest_start_time, sig.timestamps[0])
                earliest_end_time = min(earliest_end_time, sig.timestamps[-1])

        timestamps_resample = np.arange(
            0,
            (earliest_end_time - latest_start_time) + (stepsize_ms / 1000.0),
            stepsize_ms / 1000.0,
        )

        # resampling of each element based on resample function of signal
        [sig.resample(timestamps_resample) for sig in data]
        return data

    @abstractmethod
    def get(self, **kwargs) -> List[AresSignal]:
        """Get signals from the interface.

        Args:
            **kwargs: Additional format-specific arguments (e.g., filter criteria)

        Returns:
            List[AresSignal]: List of all AresSignal objects stored in the interface
        """
        pass

    @abstractmethod
    def add(self, signals: List[AresSignal], **kwargs) -> None:
        """Add signals to the interface.

        Args:
            signals: List of AresSignal objects to add
            **kwargs: Additional format-specific arguments
        """
        pass

    # XXX: do we want to define the output_path during calling the write function
    # or is it already defined during creation?
    @abstractmethod
    def write(self, output_path: str, **kwargs) -> None:
        """Write signals to file.

        Args:
            output_path: Absolute path where the signal file should be written
            **kwargs: Additional format-specific arguments
        """
        pass
