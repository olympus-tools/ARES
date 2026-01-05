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

For details, see: https://github.com/AndraeCarotta/ares#7-license
"""

import json
import os
from abc import ABC, abstractmethod
from typing import ClassVar

import numpy as np

from ares.interface.data.ares_signal import AresSignal
from ares.pydantic_models.workflow_model import DataElement
from ares.utils.decorators import typechecked_dev as typechecked
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

    cache: ClassVar[dict[str, "AresDataInterface"]] = {}
    _handlers: ClassVar[dict[str, type["AresDataInterface"]]] = {}

    @typechecked
    def __new__(
        cls,
        file_path: str | None = None,
        signals: list[AresSignal] | None = None,
        **kwargs,
    ):
        """Implement flyweight pattern based on content hash.

        Creates a new instance only if the content hash doesn't exist yet.
        Otherwise returns the existing cached instance.

        Args:
            file_path (str | None): Path to the signals file to load
            signals (list[AresSignal] | None): Optional list of AresSignal objects for initialization
            **kwargs (Any): Additional arguments for subclass initialization

        Returns:
            AresDataInterface: New or cached instance based on content hash
        """
        # neither file_path nor signals provided - create uncached instance
        if file_path is None and signals is None:
            return super().__new__(cls)

        # load signals from file if file_path provided
        if file_path is not None:
            temp_instance = object.__new__(cls)
            cls.__init__(temp_instance, file_path=file_path, **kwargs)
            signals = temp_instance.get(**kwargs)

        # calculate hash from signals
        content_hash = cls._calculate_hash(signals=signals, **kwargs)

        # return cached instance if hash already exists
        if content_hash in cls.cache:
            return cls.cache[content_hash]

        # create new instance and add to cache
        instance = super().__new__(cls)
        object.__setattr__(instance, "hash", content_hash)
        cls.cache[content_hash] = instance
        return instance

    @typechecked
    def __init__(self, file_path: str | None, **kwargs):
        """Initialize base attributes for all data handlers.

        This method should be called by all subclass __init__ methods using super().__init__().

        Args:
            file_path (str | None): Path to the data file to load
            **kwargs (Any): Additional arguments passed to subclass
        """
        object.__setattr__(self, "_file_path", file_path)
        object.__setattr__(self, "dependencies", kwargs.get("dependencies", []))

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
    @typechecked
    # TODO: safely_run function candidate?
    def wf_element_handler(
        cls,
        element_name: str,
        element_value: DataElement,
        input_hash_list: list[list[str]] | None = None,
        output_dir: str | None = None,
        **kwargs,
    ) -> None:
        """Central handler method for data operations.

        Decides between _load() and save() based on mode from DataElement.

        Args:
            element_name (str): Name of the element being processed
            element_value (DataElement): DataElement containing mode, file_path, and output_format
            input_hash_list (list[list[str]] | None): Nested list of data hashes for writing operations
            output_dir (str | None): Output directory path for writing operations
            **kwargs (Any): Additional format-specific arguments
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
                        if output_hash in cls.cache:
                            source_instance = cls.cache.get(output_hash)

                            signals = source_instance.get(
                                label_filter=element_value.label_filter,
                                stepsize=element_value.stepsize,
                                **kwargs,
                            )

                            target_instance = target_handler_class.__new__(
                                target_handler_class, file_path=None
                            )
                            target_handler_class.__init__(
                                target_instance, file_path=None
                            )

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
            file_path (str | None): Path to the data file to load. If None, defaults to MF4 handler.
            **kwargs (Any): Additional format-specific arguments

        Returns:
            AresDataInterface: AresDataInterface handler instance (may be cached)
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
    @staticmethod
    @typechecked
    def _calculate_hash(
        signals: list[AresSignal],
        **kwargs,
    ) -> str | None:
        """Calculate hash from signal list.

        This method is used for cache lookup. It always calculates hash
        from a signal list for consistent hash generation.

        Converts signals to a normalized dictionary format, then serializes
        to JSON with sorted keys to ensure consistent hash generation for
        identical signal content.

        Args:
            signals (list[AresSignal]): List of AresSignal objects
            **kwargs (Any): Additional format-specific arguments (unused)

        Returns:
            str | None: SHA256 hash string of the content, or None on error
        """
        temp_signal_dict = {}
        temp_signal_dict["metadata"] = {"type": "AresDataInterface"}
        for signal in signals:
            temp_signal_dict[signal.label] = {
                "description": signal.description
                if signal.description is not None
                else "",
                "unit": signal.unit if signal.unit is not None else "",
                "dtype": str(signal.dtype),
                "shape": signal.shape,
            }
        signal_json = json.dumps(temp_signal_dict, sort_keys=True)
        return sha256_string(signal_json)

    @staticmethod
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

    @abstractmethod
    def get(self, label_filter: list[str] | None = None, **kwargs) -> list[AresSignal]:
        """Get signals from the interface.

        Args:
            label_filter (list[str] | None): List of signal names to retrieve from the interface.
            **kwargs (Any): Additional format-specific arguments

        Returns:
            list[AresSignal]: List of all AresSignal objects stored in the interface
        """
        pass

    @abstractmethod
    def add(self, signals: list[AresSignal], **kwargs) -> None:
        """Add signals to the interface.

        Args:
            signals (list[AresSignal]): List of AresSignal objects to add
            **kwargs (Any): Additional format-specific arguments
        """
        pass

    @abstractmethod
    def _save(self, output_path: str, **kwargs) -> None:
        """Write signals to file.

        Args:
            output_path (str): Absolute path where the data file should be written
            **kwargs (Any): Additional format-specific arguments
        """
        pass
