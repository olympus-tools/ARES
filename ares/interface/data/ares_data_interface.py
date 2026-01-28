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

Copyright 2025 olympus-tools contributors. Contributors to this project
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

import re
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import ClassVar

import numpy as np

from ares.interface.data.ares_signal import AresSignal
from ares.pydantic_models.workflow_model import DataElement
from ares.utils.decorators import error_msg
from ares.utils.decorators import typechecked_dev as typechecked
from ares.utils.eval_output_path import eval_output_path
from ares.utils.hash import bin_based_hash, str_based_hash
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

    cache: ClassVar[dict[str, "AresDataInterface"]] = {}
    _handlers: ClassVar[dict[str, type["AresDataInterface"]]] = {}

    @typechecked
    def __new__(
        cls,
        file_path: Path | None = None,
        data: list[AresSignal] | None = None,
        **kwargs,
    ):
        """Implement flyweight pattern based on content hash.

        Creates a new instance only if the content hash doesn't exist yet.
        Otherwise returns the existing cached instance.

        Args:
            file_path (Path | None): Path to the data file to load
            data (list[AresSignal] | None): Optional list of AresSignal objects for initialization
            **kwargs (Any): Additional arguments for subclass initialization

        Returns:
            AresDataInterface: New or cached instance based on content hash
        """
        # neither file_path nor signals provided - create uncached instance
        if file_path is None and data is None:
            empty_instance = super().__new__(cls)
            object.__setattr__(empty_instance, "hash", "empty_instance_no_hash")
            cls.cache["empty_instance_no_hash"] = empty_instance
            return empty_instance
        # load data from file if file_path provided
        elif file_path is not None:
            temp_instance = object.__new__(cls)
            cls.__init__(temp_instance, file_path=file_path, **kwargs)
            content_hash = cls._calculate_hash(file_path=file_path, **kwargs)
        # calculate hash in case data are provided directly
        else:
            timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")[:-3]
            content_hash = cls._calculate_hash(input_string=timestamp_str, **kwargs)

        # return cached instance if hash already exists
        if content_hash in cls.cache:
            return cls.cache[content_hash]

        # create new instance and add to cache
        instance = super().__new__(cls)
        object.__setattr__(instance, "hash", content_hash)
        cls.cache[content_hash] = instance
        return instance

    @typechecked
    def __init__(
        self,
        file_path: Path | None = None,
        dependencies: list[str] | None = None,
        vstack_pattern: list[str] | None = None,
    ):
        """Initialize base attributes for all data handlers.

        This method should be called by all subclass __init__ methods using super().__init__().

        Args:
            file_path (Path | None): Path to the data file to load
            dependencies (list[str] | None): List of dependencies for this data handler
            vstack_pattern (list[str] | None): Pattern (regex) used to stack AresSignal's
            **kwargs (Any): Additional arguments passed to subclass
        """
        object.__setattr__(self, "_file_path", file_path)
        object.__setattr__(
            self, "dependencies", dependencies if dependencies is not None else []
        )
        object.__setattr__(self, "_vstack_pattern", vstack_pattern)

    @classmethod
    @typechecked
    def register(cls, extension: str, handler_class: type["AresDataInterface"]) -> None:
        """Register a handler for a specific file extension.

        Args:
            extension (str): File extension including dot (e.g., '.mf4')
            handler_class (type[AresDataInterface]): Handler class to use for this extension
        """
        cls._handlers[extension.lower()] = handler_class

    @classmethod
    @error_msg(
        exception_msg="Error while executing wf_element_handler in ares-data-interface.",
        log=logger,
        include_args=[
            "wf_element_name",
            "wf_element_value",
            "input_hash_list",
            "output_dir",
        ],
    )
    @typechecked
    def wf_element_handler(
        cls,
        wf_element_name: str,
        wf_element_value: DataElement,
        input_hash_list: list[list[str]] | None = None,
        output_dir: Path | None = None,
        **kwargs,
    ) -> None:
        """Central handler method for data operations.

        Decides between _load() and save() based on mode from DataElement.

        Args:
            wf_element_name (str): Name of the element being processed
            wf_element_value (DataElement): DataElement containing mode, file_path, and output_format
            input_hash_list (list[list[str]] | None): Nested list of data hashes for writing operations
            output_dir (Path | None): Output directory path for writing operations
            **kwargs (Any): Additional format-specific arguments
        """

        match wf_element_value.mode:
            case "read":
                for file_path in wf_element_value.file_path:
                    cls.create(
                        file_path=file_path,
                        vstack_pattern=wf_element_value.vstack_pattern,
                    )
                return None

            case "write":
                if not input_hash_list or not output_dir:
                    return None

                target_extension = f".{wf_element_value.output_format}"
                target_handler_class = cls._handlers.get(target_extension)

                stepsize = getattr(wf_element_value, "stepsize", None)

                for wf_element_hash_list in input_hash_list:
                    for output_hash in wf_element_hash_list:
                        if output_hash in cls.cache:
                            source_instance = cls.cache.get(output_hash)

                            data = source_instance.get(
                                label_filter=wf_element_value.label_filter,
                                stepsize=stepsize,
                                vstack_pattern=wf_element_value.vstack_pattern,
                                **kwargs,
                            )

                            target_instance = target_handler_class.__new__(
                                target_handler_class, file_path=None
                            )
                            target_handler_class.__init__(
                                target_instance, file_path=None
                            )

                            if data is not None:
                                target_instance.add(data, **kwargs)

                            output_path = eval_output_path(
                                output_hash=output_hash,
                                output_dir=output_dir,
                                output_format=wf_element_value.output_format,
                                wf_element_name=wf_element_name,
                            )

                            target_instance._save(output_path=output_path, **kwargs)

                return None

    @classmethod
    @typechecked
    def create(
        cls,
        file_path: Path | None = None,
        vstack_pattern: list[str] | None = None,
        **kwargs,
    ) -> "AresDataInterface":
        """Create data handler with automatic format detection.

        Uses file extension to select appropriate handler.
        All handlers share the same flyweight cache.

        Args:
            file_path (Path | None): Path to the data file to load. If None, defaults to MF4 handler.
            vstack_pattern (list[str] | None): Pattern (regex) used to stack AresSignal's
            **kwargs (Any): Additional format-specific arguments

        Returns:
            AresDataInterface: AresDataInterface handler instance (may be cached)
        """

        if file_path is None:
            ext = ".mf4"
        else:
            ext = file_path.suffix.lower()

        handler_class = cls._handlers[ext]
        return handler_class(
            file_path=file_path, vstack_pattern=vstack_pattern, **kwargs
        )

    @staticmethod
    @error_msg(
        exception_msg="Hash of ares-data-interface could not be calculated.",
        log=logger,
        include_args=["file_path", "input_string"],
    )
    @typechecked
    def _calculate_hash(
        file_path: Path | None = None,
        input_string: str | None = None,
        **kwargs,
    ) -> str:
        """Calculate hash from signal list.

        This method is used for cache lookup. It always calculates hash
        from a signal list for consistent hash generation.

        Converts data to a normalized dictionary format, then serializes
        to JSON with sorted keys to ensure consistent hash generation for
        identical signal content.

        Args:
            file_path (Path | None): Path to the data file to load. If None, defaults to MF4 handler.
            input_string (str | None): Input string to hash. Used if file_path is None.
            **kwargs (Any): Additional arguments (ignored, but accepted for compatibility)

        Returns:
            str: SHA256 hash string of the content
        """
        if file_path is not None:
            return_hash = bin_based_hash(file_path=file_path)
        elif input_string is not None:
            return_hash = str_based_hash(input_string=input_string)
        else:
            raise

        return return_hash

    @staticmethod
    @error_msg(
        exception_msg="Error in ares-data-interface resample function.",
        log=logger,
    )
    @typechecked
    def _resample(data: list[AresSignal], stepsize: int) -> list[AresSignal]:
        """Resample all signals to a common time vector using linear interpolation.

        Args:
            data (list[AresSignal]): List of AresSignal objects to resample
            stepsize (int): Resampling step size in milliseconds

        Returns:
            list[AresSignal]: List of resampled AresSignal objects with common time vector
        """
        latest_start_time = np.float32(0.0)
        earliest_end_time = np.float32(np.inf)

        # get timevector
        for signal in data:
            if len(signal.timestamps) > 0:
                latest_start_time = np.maximum(latest_start_time, signal.timestamps[0])
                earliest_end_time = np.minimum(earliest_end_time, signal.timestamps[-1])

        timestamps_resample = np.arange(
            0,
            (earliest_end_time - latest_start_time) + (stepsize / 1000.0),
            stepsize / 1000.0,
            dtype=np.float32,
        )

        # resampling of each element based on resample function of signal
        [signal.resample(timestamps_resample) for signal in data]
        return data

    @staticmethod
    @typechecked
    def _vstack(data: list[AresSignal], vstack_pattern: list[str]) -> list[AresSignal]:
        """Vertical stack ares-signals matching given regex.

        Args:
            data (list[AresSignal]): List of AresSignal objects
            vstack_pattern (list[str]): Pattern (regex) used to stack AresSignal's

        Returns:
            list[AresSignal]: List of AresSignal with vstacked signals.
        """
        for regex in vstack_pattern:
            pattern = re.compile(regex)
            matches = [signal for signal in data if pattern.search(signal.label)]

            if len(matches) == 0:
                continue

            if all([len(signal.value) == len(matches[0].value) for signal in matches]):
                sig_name = pattern.search(matches[0].label).group(1)
                logger.debug(
                    f"Vertical stacking applied, stacking: {sig_name} <-- {[signal.label for signal in matches]}"
                )
                data.append(
                    AresSignal(
                        label=sig_name,
                        timestamps=matches[0].timestamps,
                        value=np.vstack([signal.value for signal in matches]).T,
                    )
                )
        return data

    @abstractmethod
    def get(
        self,
        label_filter: list[str] | None = None,
        stepsize: int | None = None,
        vstack_pattern: list[str] | None = None,
        **kwargs,
    ) -> list[AresSignal] | None:
        """Get data from the interface.

        Args:
            label_filter (list[str] | None): List of signal names to retrieve from the interface.
            stepsize (int | None): Step size for resampling signals. If None, no resampling is performed. Defaults to None.
            vstack_pattern (list[str] | None): Pattern (regex) used to stack AresSignal's
            **kwargs (Any): Additional format-specific arguments

        Returns:
            list[AresSignal] | None: List of all AresSignal objects stored in the interface, or None if no signals are found
        """
        pass

    @abstractmethod
    def add(self, data: list[AresSignal], **kwargs) -> None:
        """Add signals to the interface.

        Args:
            data (list[AresSignal]): List of AresSignal objects to add
            **kwargs (Any): Additional format-specific arguments
        """
        pass

    @abstractmethod
    def _save(self, output_path: Path, **kwargs) -> None:
        """Write signals to file.

        Args:
            output_path (Path): Absolute path where the data file should be written
            **kwargs (Any): Additional format-specific arguments
        """
        pass
