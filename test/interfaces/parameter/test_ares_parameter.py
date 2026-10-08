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

from ares.interface.parameter.ares_parameter import AresParameter


class TestAresParameter:
    """Tests for the AresParameter dataclass."""

    def test_post_init_converts_value_to_ndarray(self):
        parameter = AresParameter(label="p", value=[1, 2, 3])
        assert isinstance(parameter.value, np.ndarray)
        np.testing.assert_array_equal(parameter.value, np.array([1, 2, 3]))

    def test_post_init_keeps_existing_ndarray(self):
        value = np.array([1.0, 2.0])
        parameter = AresParameter(label="p", value=value)
        assert parameter.value is value

    def test_dtype_property(self):
        parameter = AresParameter(label="p", value=np.array([1.5, 2.5]))
        assert parameter.dtype == np.dtype("float64")

    def test_shape_property(self):
        parameter = AresParameter(label="p", value=np.array([[1, 2], [3, 4]]))
        assert parameter.shape == (2, 2)

    def test_ndim_property_scalar(self):
        parameter = AresParameter(label="p", value=np.float64(3.0))
        assert parameter.ndim == 0

    def test_ndim_property_2d(self):
        parameter = AresParameter(label="p", value=np.zeros((2, 3)))
        assert parameter.ndim == 2

    def test_dtype_cast_changes_dtype(self):
        parameter = AresParameter(label="p", value=np.array([1, 2], dtype=np.int64))
        parameter.dtype_cast(np.float32)
        assert parameter.dtype == np.dtype("float32")

    def test_dtype_cast_skips_matching_dtype(self):
        parameter = AresParameter(label="p", value=np.array([1, 2], dtype=np.int64))
        parameter.dtype_cast(np.dtype("int64"))
        assert parameter.dtype == np.dtype("int64")
