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

import datetime
from pathlib import Path

from ares.utils.eval_output_path import eval_output_path


class _FakeDateTime(datetime.datetime):
    """Fixed clock so the timestamp in the filename is deterministic."""

    @classmethod
    def now(cls):
        return datetime.datetime(2026, 9, 23, 12, 34, 56)


def test_eval_output_path_creates_dir_and_returns_expected_path(tmp_path, monkeypatch):
    """
    Test that the output directory is created and the path is assembled
    from element name, truncated hash, timestamp and format.
    """
    monkeypatch.setattr(datetime, "datetime", _FakeDateTime)
    output_dir = tmp_path / "nested" / "output"

    result = eval_output_path(
        output_hash="0123456789abcdef",
        output_dir=output_dir,
        output_format="json",
        wf_element_name="my_element",
    )

    assert output_dir.exists()
    assert output_dir.is_dir()
    assert isinstance(result, Path)
    assert result.parent == output_dir
    assert result == output_dir / "my_element_01234567_20260923123456.json"


def test_eval_output_path_truncates_short_hash_and_empty_name(tmp_path, monkeypatch):
    """
    Test that a short hash is not extended and that an empty element name
    still produces a usable filename.
    """
    monkeypatch.setattr(datetime, "datetime", _FakeDateTime)

    result = eval_output_path(
        output_hash="abc",
        output_dir=tmp_path,
        output_format="dcm",
        wf_element_name="",
    )

    assert result == tmp_path / "_abc_20260923123456.dcm"
