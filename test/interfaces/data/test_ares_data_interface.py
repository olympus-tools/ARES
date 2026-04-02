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

import numpy as np
import pytest

from ares.interface.data.ares_data_interface import AresDataInterface
from ares.interface.data.ares_signal import AresSignal
from ares.pydantic_models.workflow_model import DataElement, VStackPatternElement


class ConcreteDataInterface(AresDataInterface):
    """Concrete implementation of AresDataInterface for testing."""

    def __init__(
        self,
        file_path=None,
        data=None,
        dependencies=None,
        vstack_pattern=None,
        stepsize=None,
        label_filter=None,
        **kwargs,
    ):
        super().__init__(
            file_path=file_path,
            dependencies=dependencies,
            vstack_pattern=vstack_pattern,
            stepsize=stepsize,
            label_filter=label_filter,
        )
        self._data = data if data else []

    def get(self, label_filter=None, stepsize=None, vstack_pattern=None, **kwargs):
        result = self._data.copy()
        if label_filter:
            result = [s for s in result if s.label in label_filter]
        if vstack_pattern:
            result = self._vstack(data=result, vstack_pattern=vstack_pattern)
        if stepsize:
            result = self._resample(data=result, stepsize=stepsize)
        return result if result else None

    def add(self, data, **kwargs):
        self._data.extend(data)

    def _save(self, output_path, **kwargs):
        pass


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear the flyweight cache before each test."""
    AresDataInterface.cache.clear()
    AresDataInterface.tmp_hash_list.clear()
    ConcreteDataInterface.cache.clear()
    ConcreteDataInterface.tmp_hash_list.clear()
    yield


class TestAresDataInterfaceNew:
    """Tests for the __new__ method (flyweight pattern)."""

    def test_new_no_args_creates_uncached_instance(self):
        instance = ConcreteDataInterface()
        assert instance.hash == "empty_instance_no_hash"
        assert AresDataInterface.cache["empty_instance_no_hash"] is instance

    def test_new_with_data_creates_new_instance(self):
        signal = AresSignal(
            label="test",
            timestamps=np.array([0.0, 1.0], dtype=np.float32),
            value=np.array([1, 2], dtype=np.int64),
        )
        instance1 = ConcreteDataInterface(data=[signal])
        instance2 = ConcreteDataInterface(data=[signal])
        assert instance1 is instance2

    def test_new_with_file_path_creates_instance(self, tmp_path):
        test_file = tmp_path / "test.bin"
        test_file.write_bytes(b"test content")

        instance = ConcreteDataInterface(file_path=test_file)
        assert instance.hash != "empty_instance_no_hash"
        assert instance.hash in AresDataInterface.cache


class TestAresDataInterfaceInit:
    """Tests for the __init__ method."""

    def test_init_with_defaults(self):
        instance = ConcreteDataInterface()
        assert instance._file_path is None
        assert instance.dependencies == []
        assert instance._stepsize is None
        assert instance._label_filter is None
        assert instance._vstack_pattern is None

    def test_init_with_values(self, tmp_path):
        test_file = tmp_path / "test.mf4"
        test_file.write_bytes(b"test content")
        deps = ["dep1", "dep2"]
        vstack = [VStackPatternElement(pattern="test_(.*)")]
        instance = ConcreteDataInterface(
            file_path=test_file,
            dependencies=deps,
            vstack_pattern=vstack,
            stepsize=100,
            label_filter=["signal1"],
        )
        assert instance._file_path == test_file
        assert instance.dependencies == deps
        assert instance._stepsize == 100
        assert instance._label_filter == ["signal1"]
        assert instance._vstack_pattern == vstack


class TestAresDataInterfaceRegister:
    """Tests for the register class method."""

    def test_register_handler(self):
        ConcreteDataInterface.register(".test", ConcreteDataInterface)
        assert ".test" in ConcreteDataInterface._handlers
        assert ConcreteDataInterface._handlers[".test"] is ConcreteDataInterface


class TestAresDataInterfaceCreate:
    """Tests for the create class method."""

    def test_create_with_none_file_path(self):
        ConcreteDataInterface.register(".mf4", ConcreteDataInterface)
        instance = ConcreteDataInterface.create()
        assert isinstance(instance, ConcreteDataInterface)

    def test_create_with_file_path(self, tmp_path):
        test_file = tmp_path / "test.mf4"
        test_file.touch()
        ConcreteDataInterface.register(".mf4", ConcreteDataInterface)
        instance = ConcreteDataInterface.create(file_path=test_file)
        assert isinstance(instance, ConcreteDataInterface)

    def test_create_with_unregistered_extension(self, tmp_path):
        test_file = tmp_path / "test.xyz"
        test_file.touch()
        with pytest.raises(KeyError):
            ConcreteDataInterface.create(file_path=test_file)


class TestAresDataInterfaceCalculateHash:
    """Tests for the _calculate_hash static method."""

    def test_calculate_hash_from_file(self, tmp_path):
        test_file = tmp_path / "test.bin"
        test_file.write_bytes(b"test content")
        hash_result = AresDataInterface._calculate_hash(file_path=test_file)
        assert isinstance(hash_result, str)
        assert len(hash_result) == 64

    def test_calculate_hash_from_string(self):
        hash_result = AresDataInterface._calculate_hash(input_string="test_string")
        assert isinstance(hash_result, str)
        assert len(hash_result) == 64

    def test_calculate_hash_no_args_raises(self):
        with pytest.raises(Exception):
            AresDataInterface._calculate_hash()

    def test_calculate_hash_consistency(self, tmp_path):
        test_file = tmp_path / "test.bin"
        test_file.write_bytes(b"test content")
        hash1 = AresDataInterface._calculate_hash(file_path=test_file)
        hash2 = AresDataInterface._calculate_hash(file_path=test_file)
        assert hash1 == hash2


class TestAresDataInterfaceFilterDeduplicates:
    """Tests for the _filter_deduplicates static method."""

    def test_filter_no_duplicates(self):
        signals = [
            AresSignal(
                label="sig1",
                timestamps=np.array([0.0, 1.0], dtype=np.float32),
                value=np.array([1, 2], dtype=np.int64),
            ),
            AresSignal(
                label="sig2",
                timestamps=np.array([0.0, 1.0], dtype=np.float32),
                value=np.array([3, 4], dtype=np.int64),
            ),
        ]
        result = AresDataInterface._filter_deduplicates(signals)
        assert len(result) == 2
        assert [s.label for s in result] == ["sig1", "sig2"]

    def test_filter_with_duplicates_keeps_last(self):
        signals = [
            AresSignal(
                label="sig1",
                timestamps=np.array([0.0, 1.0], dtype=np.float32),
                value=np.array([1, 2], dtype=np.int64),
            ),
            AresSignal(
                label="sig1",
                timestamps=np.array([0.0, 1.0], dtype=np.float32),
                value=np.array([99, 100], dtype=np.int64),
            ),
        ]
        result = AresDataInterface._filter_deduplicates(signals)
        assert len(result) == 1
        assert result[0].label == "sig1"
        assert np.array_equal(result[0].value, np.array([99, 100], dtype=np.int64))

    def test_filter_empty_list(self):
        result = AresDataInterface._filter_deduplicates([])
        assert result == []


class TestAresDataInterfaceResample:
    """Tests for the _resample static method."""

    def test_resample_basic(self):
        signals = [
            AresSignal(
                label="sig1",
                timestamps=np.array([0.0, 0.5, 1.0, 1.5, 2.0], dtype=np.float32),
                value=np.array([0.0, 0.5, 1.0, 1.5, 2.0], dtype=np.float32),
            )
        ]
        result = AresDataInterface._resample(signals, stepsize=500)
        assert len(result) == 1
        assert len(result[0].timestamps) > 0

    def test_resample_multiple_signals(self):
        signals = [
            AresSignal(
                label="sig1",
                timestamps=np.array([0.0, 1.0, 2.0], dtype=np.float32),
                value=np.array([1.0, 2.0, 3.0], dtype=np.float32),
            ),
            AresSignal(
                label="sig2",
                timestamps=np.array([0.0, 1.0, 2.0], dtype=np.float32),
                value=np.array([4.0, 5.0, 6.0], dtype=np.float32),
            ),
        ]
        result = AresDataInterface._resample(signals, stepsize=1000)
        assert len(result) == 2
        assert np.array_equal(result[0].timestamps, result[1].timestamps)

    def test_resample_empty_signal_list(self):
        with pytest.raises(ValueError):
            AresDataInterface._resample([], stepsize=100)


class TestAresDataInterfaceVstack:
    """Tests for the _vstack static method."""

    def test_vstack_1d_to_2d_no_groups(self):
        signals = [
            AresSignal(
                label="sig1",
                timestamps=np.array([0.0, 1.0], dtype=np.float32),
                value=np.array([1.0, 2.0], dtype=np.float32),
            )
        ]
        pattern = [VStackPatternElement(pattern="nomatch")]
        result = AresDataInterface._vstack(signals, pattern)
        assert len(result) == 1

    def test_vstack_1d_to_2d_single_group(self):
        signals = [
            AresSignal(
                label="data_0",
                timestamps=np.array([0.0, 1.0], dtype=np.float32),
                value=np.array([1.0, 2.0], dtype=np.float32),
            ),
            AresSignal(
                label="data_1",
                timestamps=np.array([0.0, 1.0], dtype=np.float32),
                value=np.array([3.0, 4.0], dtype=np.float32),
            ),
        ]
        pattern = [VStackPatternElement(pattern="data_(\\d+)", signal_name="data")]
        result = AresDataInterface._vstack(signals, pattern)
        assert len(result) == 3
        stacked_signal = result[-1]
        assert stacked_signal.label == "data"
        assert stacked_signal.value.shape == (2, 2)

    def test_vstack_1d_to_2d_two_groups_with_x_axis(self):
        signals = [
            AresSignal(
                label="matrix_0",
                timestamps=np.array([0.0, 1.0], dtype=np.float32),
                value=np.array([1.0, 2.0], dtype=np.float32),
            ),
            AresSignal(
                label="matrix_1",
                timestamps=np.array([0.0, 1.0], dtype=np.float32),
                value=np.array([3.0, 4.0], dtype=np.float32),
            ),
        ]
        pattern = [
            VStackPatternElement(pattern="(matrix)_(\\d+)", signal_name=1, x_axis=2)
        ]
        result = AresDataInterface._vstack(signals, pattern)
        assert len(result) == 3
        stacked_signal = result[-1]
        assert stacked_signal.value.shape == (2, 2)

    def test_vstack_1d_to_3d_three_groups(self):
        signals = [
            AresSignal(
                label="mat_0_0",
                timestamps=np.array([0.0, 1.0], dtype=np.float32),
                value=np.array([1.0, 2.0], dtype=np.float32),
            ),
            AresSignal(
                label="mat_0_1",
                timestamps=np.array([0.0, 1.0], dtype=np.float32),
                value=np.array([3.0, 4.0], dtype=np.float32),
            ),
            AresSignal(
                label="mat_1_0",
                timestamps=np.array([0.0, 1.0], dtype=np.float32),
                value=np.array([5.0, 6.0], dtype=np.float32),
            ),
            AresSignal(
                label="mat_1_1",
                timestamps=np.array([0.0, 1.0], dtype=np.float32),
                value=np.array([7.0, 8.0], dtype=np.float32),
            ),
        ]
        pattern = [
            VStackPatternElement(
                pattern="(mat)_(\\d+)_(\\d+)", signal_name=1, x_axis=2, y_axis=3
            )
        ]
        result = AresDataInterface._vstack(signals, pattern)
        assert len(result) == 5
        stacked_signal = result[-1]
        assert stacked_signal.value.shape == (2, 2, 2)

    def test_vstack_dimension_mismatch_skipped(self):
        signals = [
            AresSignal(
                label="data_0",
                timestamps=np.array([0.0, 1.0], dtype=np.float32),
                value=np.array([1.0, 2.0], dtype=np.float32),
            ),
            AresSignal(
                label="data_1",
                timestamps=np.array([0.0, 1.0, 2.0], dtype=np.float32),
                value=np.array([3.0, 4.0, 5.0], dtype=np.float32),
            ),
        ]
        pattern = [VStackPatternElement(pattern="data_(\\d+)", signal_name="data")]
        result = AresDataInterface._vstack(signals, pattern)
        assert len(result) == 2

    def test_vstack_no_matching_signals(self):
        signals = [
            AresSignal(
                label="other_signal",
                timestamps=np.array([0.0, 1.0], dtype=np.float32),
                value=np.array([1.0, 2.0], dtype=np.float32),
            )
        ]
        pattern = [VStackPatternElement(pattern="(data_\\d+)")]
        result = AresDataInterface._vstack(signals, pattern)
        assert len(result) == 1


class TestAresDataInterfaceWfElementHandler:
    """Tests for the wf_element_handler class method."""

    def test_wf_element_handler_read_mode(self, tmp_path):
        test_file = tmp_path / "test.mf4"
        test_file.touch()
        ConcreteDataInterface.register(".mf4", ConcreteDataInterface)

        wf_element = DataElement(
            mode="read",
            file_path=[test_file],
            label_filter=None,
            stepsize=None,
            vstack_pattern=None,
        )
        AresDataInterface.wf_element_handler(wf_element)

    def test_wf_element_handler_write_mode_no_input(self):
        wf_element = DataElement(
            mode="write",
            data=["hash1"],
            output_format="mf4",
        )
        result = AresDataInterface.wf_element_handler(
            wf_element, input_hash_list=None, output_dir=None
        )
        assert result is None

    def test_wf_element_handler_write_mode_with_data(self, tmp_path):
        ConcreteDataInterface.register(".mf4", ConcreteDataInterface)
        signal = AresSignal(
            label="test_sig",
            timestamps=np.array([0.0, 1.0], dtype=np.float32),
            value=np.array([1, 2], dtype=np.int64),
        )
        instance = ConcreteDataInterface(data=[signal])
        output_hash = instance.hash

        wf_element = DataElement(
            mode="write",
            data=["test"],
            output_format="mf4",
        )
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        AresDataInterface.wf_element_handler(
            wf_element,
            input_hash_list=[[output_hash]],
            output_dir=output_dir,
        )


class TestAresDataInterfaceAbstractMethods:
    """Tests to verify abstract methods are properly defined."""

    def test_cannot_instantiate_abstract_class(self):
        with pytest.raises(TypeError):
            AresDataInterface()

    def test_concrete_implementation_works(self):
        instance = ConcreteDataInterface()
        assert hasattr(instance, "get")
        assert hasattr(instance, "add")
        assert hasattr(instance, "_save")


class TestAresDataInterfaceIntegration:
    """Integration tests for combined functionality."""

    def test_full_workflow_add_get(self):
        signals = [
            AresSignal(
                label="sig1",
                timestamps=np.array([0.0, 1.0, 2.0], dtype=np.float32),
                value=np.array([1.0, 2.0, 3.0], dtype=np.float32),
            ),
            AresSignal(
                label="sig2",
                timestamps=np.array([0.0, 1.0, 2.0], dtype=np.float32),
                value=np.array([4.0, 5.0, 6.0], dtype=np.float32),
            ),
        ]
        instance = ConcreteDataInterface(data=signals)
        result = instance.get()
        assert len(result) == 2
        assert result[0].label == "sig1"
        assert result[1].label == "sig2"

    def test_flyweight_caching(self):
        signal = AresSignal(
            label="test",
            timestamps=np.array([0.0, 1.0], dtype=np.float32),
            value=np.array([1, 2], dtype=np.int64),
        )
        instance1 = ConcreteDataInterface(data=[signal])
        instance2 = ConcreteDataInterface(data=[signal])
        assert instance1 is instance2
        assert instance1.hash == instance2.hash

    def test_get_with_label_filter(self):
        signals = [
            AresSignal(
                label="sig1",
                timestamps=np.array([0.0, 1.0], dtype=np.float32),
                value=np.array([1.0, 2.0], dtype=np.float32),
            ),
            AresSignal(
                label="sig2",
                timestamps=np.array([0.0, 1.0], dtype=np.float32),
                value=np.array([3.0, 4.0], dtype=np.float32),
            ),
        ]
        instance = ConcreteDataInterface(data=signals)
        result = instance.get(label_filter=["sig1"])
        assert len(result) == 1
        assert result[0].label == "sig1"

    def test_get_with_stepsize(self):
        signals = [
            AresSignal(
                label="sig1",
                timestamps=np.array([0.0, 0.5, 1.0, 1.5, 2.0], dtype=np.float32),
                value=np.array([0.0, 0.5, 1.0, 1.5, 2.0], dtype=np.float32),
            )
        ]
        instance = ConcreteDataInterface(data=signals)
        result = instance.get(stepsize=1000)
        assert result is not None
        assert len(result) == 1
