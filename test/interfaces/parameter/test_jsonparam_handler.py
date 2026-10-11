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

import numpy as np
import pytest

from ares.interface.parameter.ares_parameter import AresParameter
from ares.interface.parameter.ares_parameter_interface import AresParamInterface
from ares.interface.parameter.jsonparam_handler import JSONParamHandler


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear the flyweight cache before each test."""
    AresParamInterface.cache.clear()
    AresParamInterface.tmp_hash_lists.clear()
    JSONParamHandler.cache.clear()
    JSONParamHandler.tmp_hash_lists.clear()
    yield


def _write_json(tmp_path, data):
    parameter_file = tmp_path / "params.json"
    parameter_file.write_text(json.dumps(data))
    return parameter_file


class TestJSONParamHandlerInit:
    """Tests for the JSONParamHandler initialization."""

    def test_init_from_file(self, tmp_path):
        data = {"p1": {"value": [1.0, 2.0], "unit": "m/s"}}
        handler = JSONParamHandler(file_path=_write_json(tmp_path, data))
        assert handler.parameter == data
        assert handler.hash != "empty_instance_no_hash"

    def test_init_from_parameters(self):
        parameter = AresParameter(label="p1", value=np.array([1.0, 2.0]), unit="m/s")
        handler = JSONParamHandler(parameters=[parameter])
        assert handler.parameter == {
            "p1": {
                "description": None,
                "name_breakpoints_1": None,
                "name_breakpoints_2": None,
                "source": "ARES_DEFAULT_SOURCE",
                "unit": "m/s",
                "value": [1.0, 2.0],
            }
        }


class TestJSONParamHandlerGet:
    """Tests for the JSONParamHandler get function."""

    def test_get_all(self, tmp_path):
        data = {"p1": {"value": 1.5}, "p2": {"value": [1, 2]}}
        handler = JSONParamHandler(file_path=_write_json(tmp_path, data))
        result = handler.get()
        assert result is not None
        assert set(p.label for p in result) == {"p1", "p2"}

    def test_get_with_label_filter(self, tmp_path):
        data = {"p1": {"value": 1.5}, "p2": {"value": [1, 2]}}
        handler = JSONParamHandler(file_path=_write_json(tmp_path, data))
        result = handler.get(label_filter=["p2"])
        assert [p.label for p in result] == ["p2"]

    def test_get_no_match_returns_none(self, tmp_path):
        data = {"p1": {"value": 1.5}}
        handler = JSONParamHandler(file_path=_write_json(tmp_path, data))
        assert handler.get(label_filter=["zzz_no_match"]) is None

    def test_get_transpose(self, tmp_path):
        data = {
            "map": {
                "value": [[1.0, 2.0], [3.0, 4.0]],
                "name_breakpoints_1": "bp1",
                "name_breakpoints_2": "bp2",
            }
        }
        handler = JSONParamHandler(file_path=_write_json(tmp_path, data))
        result = handler.get(transpose=True)
        parameter = next(p for p in result if p.label == "map")
        np.testing.assert_array_equal(
            parameter.value, np.array([[1.0, 3.0], [2.0, 4.0]])
        )
        assert parameter.name_breakpoints_1 == "bp2"
        assert parameter.name_breakpoints_2 == "bp1"

    def test_get_uses_init_transpose(self, tmp_path):
        data = {"map": {"value": [[1.0, 2.0], [3.0, 4.0]]}}
        handler = JSONParamHandler(
            file_path=_write_json(tmp_path, data),
            transpose=True,
        )
        result = handler.get()
        parameter = next(p for p in result if p.label == "map")
        np.testing.assert_array_equal(
            parameter.value, np.array([[1.0, 3.0], [2.0, 4.0]])
        )


class TestJSONParamHandlerAdd:
    """Tests for the JSONParamHandler add function."""

    def test_add(self):
        handler = JSONParamHandler()
        handler.add(
            [
                AresParameter(label="a", value=np.array(1.0)),
                AresParameter(label="a", value=np.array(2.0)),
                AresParameter(label="b", value=np.array(3.0), unit="Nm"),
            ]
        )
        assert handler.parameter["a"]["value"] == 2.0
        assert handler.parameter["b"] == {
            "description": None,
            "name_breakpoints_1": None,
            "name_breakpoints_2": None,
            "source": "ARES_DEFAULT_SOURCE",
            "unit": "Nm",
            "value": 3.0,
        }


class TestJSONParamHandlerSave:
    """Tests for the JSONParamHandler save function."""

    def test_save(self, tmp_path):
        parameter = AresParameter(label="p1", value=np.array([1.0, 2.0]), unit="m/s")
        handler = JSONParamHandler(parameters=[parameter])
        output_path = tmp_path / "out.json"
        handler._save(output_path, indent=4, ensure_ascii=True)
        saved = json.loads(output_path.read_text())
        assert saved == {
            "p1": {
                "description": None,
                "name_breakpoints_1": None,
                "name_breakpoints_2": None,
                "source": "ARES_DEFAULT_SOURCE",
                "unit": "m/s",
                "value": [1.0, 2.0],
            }
        }
