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
import subprocess
from pathlib import Path

import numpy as np
import pytest

from ares.interface.data.ares_signal import AresSignal
from ares.plugins.sim_interface import _compiler
from ares.plugins.simunit import SimUnit

C_SIM_UNIT = r"""
#include <stdint.h>

float g_in1 = 0.0f;
float g_in2 = 4.0f;
int32_t g_scalar_in = 0;
uint32_t g_arr_in[3] = {0, 0, 0};
double g_out1 = 0.0;
uint32_t g_arr_out[3] = {0, 0, 0};

void ares_simunit_init_1(void) {
  g_out1 = 0.0;
}

void ares_simunit_cyclical_1(void) {
  g_out1 += (double)g_in1 * (double)g_in2 + (double)g_scalar_in;
  for (int i = 0; i < 3; i++) {
    g_arr_out[i] = g_arr_in[i] + 1u;
  }
}
"""

DD = {
    "execution_order": {
        "initialization": ["ares_simunit_init_1"],
        "cyclical": ["ares_simunit_cyclical_1"],
    },
    "signals": {
        "g_in1": {"type": "in", "datatype": "float", "size": []},
        "g_in2": {
            "type": "in",
            "datatype": "float",
            "size": [],
            "mapping_alternatives": [4.0],
        },
        "g_scalar_in": {"type": "in", "datatype": "int32", "size": []},
        "g_arr_in": {
            "type": "in",
            "datatype": "uint32",
            "size": [3],
            "mapping_alternatives": [[7, 8, 9]],
        },
        "g_out1": {"type": "out", "datatype": "double", "size": []},
        "g_arr_out": {"type": "out", "datatype": "uint32", "size": [3]},
    },
    "parameters": {},
}


@pytest.fixture
def built_sim_unit(tmp_path: Path) -> Path:
    """Compiles a tiny simulation unit next to its Data Dictionary."""
    compiler = _compiler()
    if compiler is None:
        pytest.skip("No C compiler available to build the simulation unit.")

    lib_path = tmp_path / "sim_unit.so"
    src_path = tmp_path / "sim_unit.c"
    src_path.write_text(C_SIM_UNIT)
    subprocess.run(
        [compiler, "-shared", "-fPIC", "-O2", "-o", str(lib_path), str(src_path)],
        check=True,
        capture_output=True,
    )
    dd_path = tmp_path / "sim_unit.dd.json"
    dd_path.write_text(json.dumps(DD))
    return lib_path


def _inputs(n_steps: int) -> list[AresSignal]:
    timestamps = np.arange(n_steps, dtype=np.float32)
    return [
        AresSignal(
            label="g_in1",
            value=np.linspace(0.0, 1.0, n_steps, dtype=np.float32),
            timestamps=timestamps,
        ),
        AresSignal(
            label="g_scalar_in",
            value=np.arange(n_steps, dtype=np.int32) % 3,
            timestamps=timestamps,
        ),
    ]


def _run(
    monkeypatch, tmp_path: Path, lib_path: Path, force: str
) -> dict[str, np.ndarray]:
    monkeypatch.setenv("ARES_SIM_RUNNER", force)
    monkeypatch.setenv("ARES_SIM_RUNNER_CACHE", str(tmp_path / "cache"))
    sim_unit = SimUnit(file_path=lib_path, dd_path=lib_path.with_suffix(".dd.json"))
    results = sim_unit.run(data=_inputs(n_steps=11), parameters=[])
    return {signal.label: signal.value for signal in results}


def test_runner_and_python_loop_are_equivalent(monkeypatch, tmp_path, built_sim_unit):
    python_result = _run(monkeypatch, tmp_path, built_sim_unit, force="python")
    runner_result = _run(monkeypatch, tmp_path, built_sim_unit, force="runner")

    assert python_result.keys() == runner_result.keys()
    for label, python_value in python_result.items():
        np.testing.assert_array_equal(python_value, runner_result[label])
