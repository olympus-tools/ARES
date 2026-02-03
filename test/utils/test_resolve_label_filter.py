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

import pytest

from ares.utils.resolve_label_filter import resolve_label_filter


class TestResolveLabelFilter:
    @pytest.mark.parametrize(
        "label_filter, available_elements, expected",
        [
            # 1. Exact Matches
            (
                ["voltage", "current"],
                ["voltage", "current", "power"],
                ["voltage", "current"],
            ),
            # 2. Regex: Wildcards
            (
                ["sensor_.*"],
                ["sensor_1", "sensor_2", "actuator_1"],
                ["sensor_1", "sensor_2"],
            ),
            # 3. Regex: Partial Match (re.search matches anywhere in string)
            (
                ["temp"],
                ["engine_temp_high", "outside_temp", "pressure"],
                ["engine_temp_high", "outside_temp"],
            ),
            # 4. No Matches
            (["missing_signal"], ["signal_a", "signal_b"], []),
            # 5. Deduplication (Same element matched by multiple patterns)
            (["signal", "signal_1"], ["signal_1"], ["signal_1"]),
        ],
    )
    def test_resolve_label_filter_scenarios(
        self, label_filter, available_elements, expected
    ):
        """
        Tests various success scenarios including regex and deduplication.
        """
        result = resolve_label_filter(label_filter, available_elements)

        assert set(result) == set(expected)

    def test_empty_label_filter(self):
        """Should return empty list if no filters are provided."""
        available = ["a", "b", "c"]
        result = resolve_label_filter([], available)
        assert result == []

    def test_empty_available_elements(self):
        """Should return empty list if available elements list is empty."""
        result = resolve_label_filter(["pattern"], [])
        assert result == []

    # def test_none_available_elements(self):
    #     """
    #     CRITICAL:
    #     This test checks if the function handles None safely (returns empty list).
    #     """
    #     result = resolve_label_filter(["pattern"], None)
    #     assert result == []

    def test_invalid_regex_pattern(self):
        """Ensures that invalid regex patterns raise a re.error."""
        available = ["data"]
        # '[' is an invalid regex pattern (unclosed bracket)
        with pytest.raises(re.error):
            resolve_label_filter(["["], available)
