r"""
________________________________________________________________________
|                                                                      |
|               $$$$$$\  $$$$$$$\  $$$$$$$$\  $$$$$$\                  |
|              $$  __$$\ $$ |  $$ |$$  _____|$$  __$$\                 |
|              $$ /  $$ |$$ |  $$ |$$ |      $$ /  \__|                |
|              $$$$$$$$ |$$$$$$$  |$$$$$\    \$$$$$$\                  |
|              $$  __$$ |$$  __$$< $$  __|    \____$$\                 |
|              $$ |  $$ |$$ |  $$ |$$ |      $$ |  $$ |                |
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
from typing import ClassVar

import pytest
from pydantic import BaseModel, Field

from ares.core.workflow import Workflow
from ares.pydantic_models.workflow_model import (
    BaseElement,
    MergeElement,
    PluginElement,
    SimUnitElement,
)


# TEST: runtime field reset
def test_runtime_fields_are_reset_to_model_defaults():
    """
    Tests that serialized runtime state is replaced by the model defaults.
    """
    element = PluginElement.model_validate(
        {
            "type": "plugin",
            "file_path": "plugin.py",
            "element_workflow": ["serialized_source"],
            "hash_lists_parameter": {
                "serialized_parameter_hash": ["serialized_parameter_source"]
            },
            "hash_lists_data": {"serialized_data_hash": ["serialized_data_source"]},
        }
    )

    assert element.element_workflow == []
    assert element.hash_lists_parameter == {}
    assert element.hash_lists_data == {}


@pytest.mark.parametrize(
    "element_type, data",
    [
        (
            SimUnitElement,
            {
                "type": "sim_unit",
                "file_path": "unit.so",
                "stepsize": 1,
                "data_dictionary": "data.json",
            },
        ),
        (MergeElement, {"type": "merge"}),
    ],
)
def test_runtime_field_registry_is_inherited_by_element_subclasses(
    element_type: type[BaseModel], data: dict[str, object]
):
    """
    Tests that plugin runtime fields are reset for all plugin subclasses.

    Args:
        element_type (type[BaseModel]): Element model under test.
        data (dict): Minimal valid element input.
    """
    data.update(
        {
            "element_workflow": ["serialized_source"],
            "hash_lists_parameter": {
                "serialized_parameter_hash": ["serialized_parameter_source"]
            },
            "hash_lists_data": {"serialized_data_hash": ["serialized_data_source"]},
        }
    )

    element = element_type.model_validate(data)

    assert element.element_workflow == []
    assert element.hash_lists_parameter == {}
    assert element.hash_lists_data == {}


def test_unregistered_hash_lists_named_extra_field_is_preserved():
    """
    Tests that explicit registration replaces substring-based field matching.
    """
    element = PluginElement.model_validate(
        {
            "type": "plugin",
            "file_path": "plugin.py",
            "unrelated_hash_lists_metadata": {"keep": "this"},
        }
    )

    assert element.unrelated_hash_lists_metadata == {"keep": "this"}


def test_reset_uses_default_factory():
    """
    Tests that registered fields use a fresh value from their default factory.
    """

    class FactoryElement(BaseElement):
        _resettable_runtime_fields: ClassVar[tuple[str, ...]] = (
            *BaseElement._resettable_runtime_fields,
            "runtime_state",
        )
        runtime_state: list[str] = Field(default_factory=list)

    first = FactoryElement.model_validate({"runtime_state": ["serialized"]})
    second = FactoryElement.model_validate({})

    assert first.runtime_state == []
    assert second.runtime_state == []
    assert first.runtime_state is not second.runtime_state


def test_workflow_loader_resets_serialized_state_and_recomputes_element_workflow(
    tmp_path: Path,
):
    """
    Tests that loading a workflow discards serialized runtime state.

    Args:
        tmp_path: Pytest temporary directory for the workflow file.
    """
    workflow_path = tmp_path / "workflow.json"
    workflow_data = {
        "source": {
            "type": "data",
            "mode": "read",
            "file_path": ["input.mf4"],
            "element_workflow": ["serialized_source"],
            "hash_lists_parameter": {
                "serialized_parameter_hash": ["serialized_parameter_source"]
            },
            "hash_lists_data": {"serialized_data_hash": ["serialized_data_source"]},
        },
        "sink": {
            "type": "data",
            "mode": "write",
            "data": ["source"],
            "output_format": "mf4",
            "element_workflow": ["serialized_sink"],
            "hash_lists_parameter": {
                "serialized_parameter_hash": ["serialized_parameter_source"]
            },
            "hash_lists_data": {"serialized_data_hash": ["serialized_data_source"]},
        },
    }
    workflow_path.write_text(json.dumps(workflow_data), encoding="utf-8")

    workflow = Workflow(file_path=workflow_path)

    assert workflow.workflow["source"].element_workflow == []
    assert workflow.workflow["source"].hash_lists_parameter == {}
    assert workflow.workflow["source"].hash_lists_data == {}
    assert workflow.workflow["sink"].element_workflow == ["source"]
    assert workflow.workflow["sink"].hash_lists_parameter == {}
    assert workflow.workflow["sink"].hash_lists_data == {}
    assert json.loads(workflow_path.read_text(encoding="utf-8")) == workflow_data
