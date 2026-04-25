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

Copyright 2025 olympus-tools contributors. Dependencies and licenses
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

import copy
import re
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import ClassVar

import numpy as np
from ares.interface.data.ares_signal import AresSignal
from ares.pydantic_models.workflow_model import DataElement, VStackPatternElement
from ares.utils.decorators import error_msg
from ares.utils.decorators import typechecked_dev as typechecked
from ares.utils.eval_output_path import eval_output_path
from ares.utils.hash import bin_based_hash, str_based_hash
from ares.utils.logger import create_logger

logger = create_logger(name=__name__)


class AresDataInterface(ABC):
    """Abstract base class for data interfaces in ARES.

    This interface defines the contract for all data handlers in ARES.
    Implements flyweight pattern based on content hash (sha256) to ensure
    that identical data objects share the same instance.

    The flyweight pattern is implemented via __new__ - identical file contents
    will automatically return the same cached instance.
    """

    cache: ClassVar[dict[str, "AresDataInterface"]] = {}
    tmp_hash_list: ClassVar[list[str]] = []
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

        cls.tmp_hash_list.append(content_hash)

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
        vstack_pattern: list[VStackPatternElement] | None = None,
        stepsize: int | None = None,
        label_filter: list[str] | None = None,
    ):
        """Initialize base attributes for all data handlers.

        This method should be called by all subclass __init__ methods using super().__init__().

        Args:
            file_path (Path | None): Path to the data file to load
            dependencies (list[str] | None): List of dependencies for this data handler
            vstack_pattern (list[VStackPatternElement]| None): Pattern (regex) used to stack AresSignal's
            stepsize (int | None): Step size for resampling signals. If None, no resampling is performed. Defaults to None.
            label_filter (list[str] | None): List of signal names to filter when retrieving data
            **kwargs (Any): Additional arguments passed to subclass
        """
        object.__setattr__(self, "_file_path", file_path)
        object.__setattr__(
            self, "dependencies", dependencies if dependencies is not None else []
        )
        object.__setattr__(self, "stepsize", stepsize)
        object.__setattr__(self, "_label_filter", label_filter)
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
            "wf_element_value",
            "input_hash_list",
            "output_dir",
        ],
    )
    @typechecked
    def wf_element_handler(
        cls,
        wf_element_value: DataElement,
        input_hash_list: list[list[str]] | None = None,
        output_dir: Path | None = None,
        **kwargs,
    ):
        """Central handler method for data operations.

        Decides between _load() and save() based on mode from DataElement.

        Args:
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
                        label_filter=wf_element_value.label_filter,
                        stepsize=wf_element_value.stepsize,
                        vstack_pattern=wf_element_value.vstack_pattern,
                    )

            case "write":
                if not input_hash_list or not output_dir:
                    return

                target_extension = f".{wf_element_value.output_format}"
                target_handler_class = cls._handlers.get(target_extension)

                for wf_element_hash_list in input_hash_list:
                    for output_hash in wf_element_hash_list:
                        if output_hash in cls.cache:
                            source_instance = cls.cache.get(output_hash)

                            data = source_instance.get(
                                label_filter=wf_element_value.label_filter,
                                stepsize=wf_element_value.stepsize,
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
                                wf_element_name=wf_element_value.name,
                            )

                            target_instance._save(output_path=output_path, **kwargs)

    @classmethod
    @typechecked
    def create(
        cls,
        file_path: Path | None = None,
        vstack_pattern: list[VStackPatternElement] | None = None,
        **kwargs,
    ) -> "AresDataInterface":
        """Create data handler with automatic format detection.

        Uses file extension to select appropriate handler.
        All handlers share the same flyweight cache.

        Args:
            file_path (Path | None): Path to the data file to load. If None, defaults to MF4 handler.
            vstack_pattern (list[VStackPatternElement] | None): Pattern (regex) used to stack AresSignal's
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
    @typechecked
    def _filter_deduplicates(data: list[AresSignal]) -> list[AresSignal]:
        """Remove duplicate signals by label, keeping the last occurrence.

        When multiple signals with the same label exist in the input list,
        only the last occurrence is retained. This ensures that later signals
        override earlier ones when merging data from multiple sources.

        Args:
            data (list[AresSignal]): List of AresSignal objects that may contain duplicates.

        Returns:
            list[AresSignal]: Deduplicated list with unique labels, preserving insertion order.
        """
        data_filtered: dict[str, AresSignal] = {}
        for signal in data:
            if signal.label in data_filtered:
                logger.debug(
                    f"Duplicate signal label '{signal.label}' found. Using later occurrence."
                )
            data_filtered[signal.label] = signal
        return list(data_filtered.values())

    @staticmethod
    @typechecked
    def _resample_accuracy(
        data_original: list[AresSignal],
        data_resampled: list[AresSignal],
        stepsize: int,
    ) -> None:
        """Log hub-normalised resampling accuracy for all signals.

        For each signal pair (original / resampled), the resampled signal is
        back-interpolated onto the original timestamps. Absolute deviations are
        normalised by the signal hub (``max - min``) to yield a dimensionless
        percentage. Per-signal mean and max errors, as well as an overall summary,
        are emitted at DEBUG log level.

        Args:
            data_original (list[AresSignal]): Signals before resampling.
            data_resampled (list[AresSignal]): Corresponding signals after resampling.
            stepsize (int): Resampling step size in milliseconds (used for log output only).
        """
        value_accuracy: list[tuple[str, float, float]] = []
        for signal in data_original:
            signal_resampled = next(
                s for s in data_resampled if s.label == signal.label
            )

            mask = (signal.timestamps >= signal_resampled.timestamps[0]) & (
                signal.timestamps <= signal_resampled.timestamps[-1]
            )
            timestamps_original_masked = signal.timestamps[mask]
            values_original = signal.value[mask].astype(np.float32)

            signal_resampled_copy = copy.deepcopy(signal_resampled)
            signal_resampled_copy.resample(
                timestamps_resampled=timestamps_original_masked
            )
            if signal_resampled_copy.value is None:
                continue
            values_back_resampled = signal_resampled_copy.value.astype(np.float32)
            abs_errors = np.abs(values_original - values_back_resampled)

            hub = float(np.max(values_original) - np.min(values_original))
            if hub == 0.0:
                value_accuracy.append((signal.label, 0.0, 0.0))
                continue

            mean_err_pct = float(np.mean(abs_errors) / hub * 100.0)
            max_err_pct = float(np.max(abs_errors) / hub * 100.0)
            value_accuracy.append((signal.label, mean_err_pct, max_err_pct))

        label_worst, mean_worst, max_worst = max(value_accuracy, key=lambda x: x[1])

        col_label = 70
        col_num = 6

        rows = "\n".join(
            f"  {label:<{col_label}}  mean error: {mean:>{col_num}.2f} %  max. error: {max_e:>{col_num}.2f} %"
            for label, mean, max_e in value_accuracy
        )
        if mean_worst == 0.0:
            overall_line = f"  {'overall error':<{col_label}}  no deviation detected"
        else:
            overall_line = (
                f"  {'overall error':<{col_label}}  max. mean error: {mean_worst:>{col_num}.2f} %"
                f"  max. error: {max_worst:>{col_num}.2f} % (signal='{label_worst}')"
            )
        logger.debug(
            f"Resampling accuracy (stepsize={stepsize} ms, n={len(value_accuracy)} signals, method: hub-normalised):\n"
            f"{overall_line}\n"
            f"  {'-' * (col_label + col_num * 2 + 50)}\n" + rows
        )

    @staticmethod
    @error_msg(
        exception_msg="Error in ares-data-interface resample function.",
        log=logger,
    )
    @typechecked
    def _resample(data: list[AresSignal], stepsize: int) -> list[AresSignal]:
        """Resample all signals to a common time vector using linear interpolation.

        After resampling, a hub-normalised accuracy metric is computed by
        back-interpolating each resampled signal onto the original timestamps.
        This quantifies amplitude errors caused by peaks that are missed because
        original samples fall between two resample grid points. Per-signal mean
        and max errors are reported, along with the overall mean error and the
        signal with the highest mean error. The result is emitted at DEBUG log level.

        Args:
            data (list[AresSignal]): List of AresSignal objects to resample
            stepsize (int): Resampling step size in milliseconds

        Returns:
            list[AresSignal]: List of resampled AresSignal objects with common time vector
        """

        latest_start_time = np.float32(0.0)
        earliest_end_time = np.float32(np.inf)

        for signal in data:
            if signal.shape[0] > 0:
                latest_start_time = np.maximum(latest_start_time, signal.timestamps[0])
                earliest_end_time = np.minimum(earliest_end_time, signal.timestamps[-1])

        n_timestamps = (
            int((earliest_end_time - latest_start_time) / (stepsize / 1000.0)) + 1
        )
        timestamps_resampled = np.linspace(
            latest_start_time, earliest_end_time, n_timestamps, dtype=np.float32
        )

        data_resampled: list[AresSignal] = copy.deepcopy(data)

        for signal in data_resampled:
            # force new time vector: unifying a time vector with unevenly distributed samples
            # and reset it hard to float32
            if True:  # TODO: add flag to workflow
                signal.timestamps_uniform()

            signal.resample(timestamps_resampled=timestamps_resampled)

        # calculation of resample accuracy only in logger mode 10 ("debug")
        if logger.isEnabledFor(10):
            AresDataInterface._resample_accuracy(
                data_original=data,
                data_resampled=data_resampled,
                stepsize=stepsize,
            )

        return data_resampled

    @staticmethod
    @typechecked
    def _vstack(
        data: list[AresSignal], vstack_pattern: list[VStackPatternElement]
    ) -> list[AresSignal]:
        """Vertical stack ares-signals matching given VStackPatternElements.
        Supports two stacking modes based on number of regex groups:
        - 1-2 groups: Stack 1D signals to 2D (horizontal concatenation)
        - 3 groups: Stack 1D signals to 3D matrix using row/column indices
                    provided by VStackPatternElement

        The VStackPatternElement consists of the following fields:
            - signal_name: regex pattern used to determine signals for stacking (default: group1)
            - x_axis: pattern to catch x-axis index (default: group2)
            - y_axis: pattern to catch y-axis index (default: group3)

        Args:
            data (list[AresSignal]): List of AresSignal objects
            vstack_pattern (list[VStackPatternElement]): list of VstackPatternElements used for stacking

        Returns:
            list[AresSignal]: Original data list with newly stacked signals appended
        """
        for vstack_element in vstack_pattern:
            pattern = re.compile(vstack_element.pattern)

            # check pattern for groups - at least 1 group necessary for stacking
            if pattern.groups == 0:
                logger.debug(
                    f"Vertical stacking for pattern '{vstack_element.pattern}' is skipped."
                    f"Pattern includes no group."
                )
                continue

            # find all matching signals
            pair_matches = [
                (signal, pattern_result)
                for signal in data
                if (pattern_result := pattern.search(signal.label))
            ]

            # no matching signals found for pattern -> skipping this pattern
            if not pair_matches:
                continue

            # iterate over groups, collect matching signals,pattern to stack in dict
            signal_stack_dict = defaultdict(lambda: {"signals": [], "patterns": []})
            for signal_match, pattern_match in pair_matches:
                if isinstance(vstack_element.signal_name, str):
                    group_key = vstack_element.signal_name
                elif isinstance(vstack_element.signal_name, int):
                    group_key = pattern_match.group(vstack_element.signal_name)
                else:
                    group_key = pattern_match.group(1)

                signal_stack_dict[group_key]["signals"].append(signal_match)
                signal_stack_dict[group_key]["patterns"].append(pattern_match)

            # iterate over collected groups and stack them to combined signal
            for signal_name, data_stack in signal_stack_dict.items():
                signal_matches = data_stack["signals"]
                pattern_matches = data_stack["patterns"]

                # validate that all matching signals have same dimensions
                reference_signal = signal_matches[0]
                if not all(
                    [
                        signal.shape == reference_signal.shape
                        for signal in signal_matches
                    ]
                ):
                    logger.debug(
                        f"Vertical stacking could not be applied. Dimension missmatch in stack: {[signal.label for signal in signal_matches]}."
                    )
                    continue

                # 1D
                if pattern.groups <= 2:
                    logger.debug(
                        f"Vertical stacking applied, stacking 1D signals to 2D: {signal_name} <-- {[signal.label for signal in signal_matches]}."
                    )

                    # check for x-axis index
                    if pattern.groups == 2:
                        x_axis_idx = (
                            vstack_element.x_axis
                            if vstack_element.x_axis is not None
                            else 2
                        )
                        number_columns = len(pattern_matches)
                        stacked_array = np.full(
                            (
                                len(reference_signal.timestamps),
                                number_columns,
                            ),
                            np.nan,
                        )

                        for signal, pattern_result in zip(
                            signal_matches, pattern_matches
                        ):
                            column_idx = int(pattern_result.group(x_axis_idx))
                            if not all(np.isnan(stacked_array[:, column_idx])):
                                logger.warning(
                                    f"Vertical stacking for {signal.label} could not be applied correctly. Given pattern-group for x-axis is not monotonic."
                                )

                            stacked_array[:, column_idx] = signal.value
                        data.append(
                            AresSignal(
                                label=signal_name,
                                timestamps=reference_signal.timestamps,
                                value=stacked_array,
                                description=f"Stacked signal from {[signal.label for signal in signal_matches]}",
                                source=reference_signal.source,
                                unit=reference_signal.unit,
                            )
                        )
                        continue

                    # default: stacking
                    data.append(
                        AresSignal(
                            label=signal_name,
                            timestamps=reference_signal.timestamps,
                            value=np.vstack(
                                [signal.value for signal in signal_matches]
                            ).T,
                            description=f"Stacked signal from {[signal.label for signal in signal_matches]}",
                            source=reference_signal.source,
                            unit=reference_signal.unit,
                        )
                    )

                # 2D
                elif pattern.groups == 3:
                    x_axis_idx = (
                        vstack_element.x_axis
                        if vstack_element.x_axis is not None
                        else 2
                    )
                    y_axis_idx = (
                        vstack_element.y_axis
                        if vstack_element.y_axis is not None
                        else 3
                    )

                    number_columns = 0
                    number_rows = 0
                    for pattern_result in pattern_matches:
                        number_columns = max(
                            number_columns, int(pattern_result.group(x_axis_idx))
                        )
                        number_rows = max(
                            number_rows, int(pattern_result.group(y_axis_idx))
                        )

                    stacked_matrix = np.full(
                        (
                            number_rows + 1,
                            number_columns + 1,
                            len(reference_signal.timestamps),
                        ),
                        np.nan,
                    )

                    for signal, pattern_result in zip(signal_matches, pattern_matches):
                        column_idx = int(pattern_result.group(x_axis_idx))
                        row_idx = int(pattern_result.group(y_axis_idx))

                        if not all(np.isnan(stacked_matrix[row_idx, column_idx, :])):
                            logger.warning(
                                f"Vertical stacking for {signal.label} could not be applied correctly. Given pattern-group for x-axis,y-axis is not monotonic/unique."
                            )
                        stacked_matrix[row_idx, column_idx, :] = signal.value

                    logger.debug(
                        f"Vertical stacking applied,stacking 2D signals to 3D:{signal_name} <-- {[signal.label for signal in signal_matches]}."
                    )
                    data.append(
                        AresSignal(
                            label=signal_name,
                            timestamps=reference_signal.timestamps,
                            value=stacked_matrix.transpose(2, 1, 0),
                            description=f"Stacked signal from {[signal.label for signal in signal_matches]}",
                            source=reference_signal.source,
                            unit=reference_signal.unit,
                        )
                    )

        return data

    @abstractmethod
    def get(
        self,
        label_filter: list[str] | None = None,
        stepsize: int | None = None,
        vstack_pattern: list[VStackPatternElement] | None = None,
        **kwargs,
    ) -> list[AresSignal] | None:
        """Get data from the interface.

        Args:
            label_filter (list[str] | None): List of signal names to retrieve from the interface.
            stepsize (int | None): Step size for resampling signals. If None, no resampling is performed. Defaults to None.
            vstack_pattern (list[VStackPatternElement]| None): Pattern (regex) used to stack AresSignal's
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
