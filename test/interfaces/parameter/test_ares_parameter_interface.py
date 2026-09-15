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

import json
from pathlib import Path

import numpy as np
import pytest

from ares.interface.parameter.ares_parameter import AresParameter
from ares.interface.parameter.ares_parameter_interface import AresParamInterface
from ares.pydantic_models.workflow_model import ParameterElement, ParameterFormat


class ConcreteParamInterface(AresParamInterface):
    """Concrete implementation of AresParamInterface for testing."""

    def __init__(
        self,
        file_path=None,
        parameters=None,
        dependencies=None,
        label_filter=None,
        **kwargs,
    ):
        super().__init__(
            file_path=file_path,
            dependencies=dependencies,
            label_filter=label_filter,
        )
        self._parameters = parameters if parameters else []

    def get(self, label_filter=None, **kwargs):
        result = self._parameters.copy()
        if label_filter:
            result = [p for p in result if p.label in label_filter]
        return result if result else None

    def add(self, parameters, **kwargs):
        self._parameters.extend(parameters)

    def _save(self, output_path, **kwargs):
        pass


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear the flyweight cache before each test."""
    AresParamInterface.cache.clear()
    AresParamInterface.tmp_hash_list.clear()
    ConcreteParamInterface.cache.clear()
    ConcreteParamInterface.tmp_hash_list.clear()
    yield


class TestAresParamInterfaceNew:
    """Tests for the __new__ method (flyweight pattern)."""

    def test_new_no_args_creates_uncached_instance(self):
        instance = ConcreteParamInterface()
        assert instance.hash == "empty_instance_no_hash"
        assert AresParamInterface.cache["empty_instance_no_hash"] is instance

    def test_new_with_parameters_creates_new_instance(self):
        param = AresParameter(label="test", value=np.array([1.0, 2.0]))
        instance1 = ConcreteParamInterface(parameters=[param])
        instance2 = ConcreteParamInterface(parameters=[param])
        assert instance1 is instance2

    def test_new_with_file_path_creates_instance(self, tmp_path):
        test_file = tmp_path / "test.json"
        param_data = {"param1": {"value": 1.0, "description": "", "unit": ""}}
        test_file.write_text(json.dumps(param_data))

        ConcreteParamInterface.register(".json", ConcreteParamInterface)
        instance = ConcreteParamInterface(file_path=test_file)
        assert instance.hash != "empty_instance_no_hash"
        assert instance.hash in AresParamInterface.cache


class TestAresParamInterfaceInit:
    """Tests for the __init__ method."""

    def test_init_with_defaults(self):
        instance = ConcreteParamInterface()
        assert instance._file_path is None
        assert instance.dependencies == []
        assert instance._label_filter is None

    def test_init_with_values(self, tmp_path):
        test_file = tmp_path / "test.json"
        test_file.write_text(json.dumps({"a": {"value": 1}}))
        deps = ["dep1", "dep2"]
        instance = ConcreteParamInterface(
            file_path=test_file,
            dependencies=deps,
            label_filter=["param1"],
        )
        assert instance._file_path == test_file
        assert instance.dependencies == deps
        assert instance._label_filter == ["param1"]


class TestAresParamInterfaceRegister:
    """Tests for the register class method."""

    def test_register_handler(self):
        ConcreteParamInterface.register(".json", ConcreteParamInterface)
        assert ".json" in ConcreteParamInterface._handlers
        assert ConcreteParamInterface._handlers[".json"] is ConcreteParamInterface


class TestAresParamInterfaceCreate:
    """Tests for the create class method."""

    def test_create_with_none_file_path(self):
        ConcreteParamInterface.register(".json", ConcreteParamInterface)
        instance = ConcreteParamInterface.create()
        assert isinstance(instance, ConcreteParamInterface)

    def test_create_with_file_path(self, tmp_path):
        test_file = tmp_path / "test.json"
        test_file.touch()
        ConcreteParamInterface.register(".json", ConcreteParamInterface)
        instance = ConcreteParamInterface.create(file_path=test_file)
        assert isinstance(instance, ConcreteParamInterface)

    def test_create_with_unregistered_extension(self, tmp_path):
        test_file = tmp_path / "test.xyz"
        test_file.touch()
        with pytest.raises(KeyError):
            ConcreteParamInterface.create(file_path=test_file)


class TestAresParamInterfaceCalculateHash:
    """Tests for the _calculate_hash static method."""

    def test_calculate_hash_from_parameters(self):
        params = [
            AresParameter(
                label="param1",
                value=np.array([1.0, 2.0]),
                description="desc",
                unit="m/s",
            ),
        ]
        hash_result = AresParamInterface._calculate_hash(parameters=params)
        assert isinstance(hash_result, str)
        assert len(hash_result) == 64

    def test_calculate_hash_consistency(self):
        params = [
            AresParameter(
                label="param1",
                value=np.array([1.0, 2.0]),
                description="desc",
                unit="m/s",
            ),
        ]
        hash1 = AresParamInterface._calculate_hash(parameters=params)
        hash2 = AresParamInterface._calculate_hash(parameters=params)
        assert hash1 == hash2

    def test_calculate_hash_different_params_different_hash(self):
        params1 = [
            AresParameter(label="param1", value=np.array([1.0, 2.0])),
        ]
        params2 = [
            AresParameter(label="param1", value=np.array([3.0, 4.0])),
        ]
        hash1 = AresParamInterface._calculate_hash(parameters=params1)
        hash2 = AresParamInterface._calculate_hash(parameters=params2)
        assert hash1 != hash2

    def test_calculate_hash_different_labels_different_hash(self):
        params1 = [
            AresParameter(label="param_a", value=np.array([1.0])),
        ]
        params2 = [
            AresParameter(label="param_b", value=np.array([1.0])),
        ]
        hash1 = AresParamInterface._calculate_hash(parameters=params1)
        hash2 = AresParamInterface._calculate_hash(parameters=params2)
        assert hash1 != hash2

    def test_calculate_hash_multiple_parameters(self):
        params = [
            AresParameter(label="param1", value=np.array(1.0)),
            AresParameter(label="param2", value=np.array([1.0, 2.0])),
        ]
        hash_result = AresParamInterface._calculate_hash(parameters=params)
        assert isinstance(hash_result, str)
        assert len(hash_result) == 64

    def test_calculate_hash_empty_parameters_list(self):
        hash_result = AresParamInterface._calculate_hash(parameters=[])
        assert isinstance(hash_result, str)
        assert len(hash_result) == 64


class TestAresParamInterfaceFilterDeduplicates:
    """Tests for the _filter_deduplicates static method."""

    def test_filter_no_duplicates(self):
        params = [
            AresParameter(label="param1", value=np.array(1.0)),
            AresParameter(label="param2", value=np.array(2.0)),
        ]
        result = AresParamInterface._filter_deduplicates(params)
        assert len(result) == 2
        assert [p.label for p in result] == ["param1", "param2"]

    def test_filter_with_duplicates_keeps_last(self):
        params = [
            AresParameter(label="param1", value=np.array(1.0)),
            AresParameter(label="param1", value=np.array(99.0)),
        ]
        result = AresParamInterface._filter_deduplicates(params)
        assert len(result) == 1
        assert result[0].label == "param1"
        assert np.array_equal(result[0].value, np.array(99.0))

    def test_filter_empty_list(self):
        result = AresParamInterface._filter_deduplicates([])
        assert result == []

    def test_filter_multiple_duplicates(self):
        params = [
            AresParameter(label="a", value=np.array(1.0)),
            AresParameter(label="b", value=np.array(2.0)),
            AresParameter(label="a", value=np.array(3.0)),
            AresParameter(label="c", value=np.array(4.0)),
            AresParameter(label="b", value=np.array(5.0)),
        ]
        result = AresParamInterface._filter_deduplicates(params)
        assert len(result) == 3
        assert [p.label for p in result] == ["a", "b", "c"]
        assert np.array_equal(result[0].value, np.array(3.0))
        assert np.array_equal(result[1].value, np.array(5.0))
        assert np.array_equal(result[2].value, np.array(4.0))


class TestAresParamInterfaceWfElementHandler:
    """Tests for the wf_element_handler class method."""

    def test_wf_element_handler_read_mode(self, tmp_path):
        test_file = tmp_path / "test.json"
        test_file.write_text(json.dumps({"param1": {"value": 1.0}}))
        ConcreteParamInterface.register(".json", ConcreteParamInterface)

        wf_element = ParameterElement(
            mode="read",
            file_path=[test_file],
            label_filter=None,
        )
        AresParamInterface.wf_element_handler(wf_element)

    def test_wf_element_handler_write_mode_no_input(self):
        wf_element = ParameterElement(
            mode="write",
            parameter=["hash1"],
            output_format="json",
        )
        result = AresParamInterface.wf_element_handler(
            wf_element, input_hash_list=None, output_dir=None
        )
        assert result is None

    def test_wf_element_handler_write_mode_with_data(self, tmp_path):
        ConcreteParamInterface.register(".json", ConcreteParamInterface)
        param = AresParameter(
            label="test_param",
            value=np.array(42.0),
            description="test",
            unit="m/s",
        )
        instance = ConcreteParamInterface(parameters=[param])
        output_hash = instance.hash

        wf_element = ParameterElement(
            mode="write",
            parameter=["test"],
            output_format="json",
        )
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        AresParamInterface.wf_element_handler(
            wf_element,
            input_hash_list=[[output_hash]],
            output_dir=output_dir,
        )


class TestAresParamInterfaceAbstractMethods:
    """Tests to verify abstract methods are properly defined."""

    def test_cannot_instantiate_abstract_class(self):
        with pytest.raises(TypeError):
            AresParamInterface()

    def test_concrete_implementation_works(self):
        instance = ConcreteParamInterface()
        assert hasattr(instance, "get")
        assert hasattr(instance, "add")
        assert hasattr(instance, "_save")


class TestAresParamInterfaceIntegration:
    """Integration tests for combined functionality."""

    def test_full_workflow_add_get(self):
        params = [
            AresParameter(label="param1", value=np.array(1.0)),
            AresParameter(label="param2", value=np.array(2.0)),
        ]
        instance = ConcreteParamInterface(parameters=params)
        result = instance.get()
        assert len(result) == 2
        assert result[0].label == "param1"
        assert result[1].label == "param2"

    def test_flyweight_caching(self):
        param = AresParameter(label="test", value=np.array([1, 2]))
        instance1 = ConcreteParamInterface(parameters=[param])
        instance2 = ConcreteParamInterface(parameters=[param])
        assert instance1 is instance2
        assert instance1.hash == instance2.hash

    def test_get_with_label_filter(self):
        params = [
            AresParameter(label="param1", value=np.array(1.0)),
            AresParameter(label="param2", value=np.array(2.0)),
        ]
        instance = ConcreteParamInterface(parameters=params)
        result = instance.get(label_filter=["param1"])
        assert len(result) == 1
        assert result[0].label == "param1"
