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

    https://www.apache.org/licenses/LICENSE-2.0
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, call

from ares.interface.data.ares_data_interface import AresDataInterface
from ares.interface.parameter.ares_parameter_interface import AresParamInterface
from ares.plugins import merge
from ares.pydantic_models.workflow_model import MergeElement


def _progress_factory() -> tuple[MagicMock, list[MagicMock]]:
    """Create a mock progress factory and collect its context-managed tasks."""
    tasks: list[MagicMock] = []

    def create_progress(description: str, total: int) -> MagicMock:
        progress = MagicMock()
        progress.__enter__.return_value = progress
        tasks.append(progress)
        return progress

    return MagicMock(side_effect=create_progress), tasks


def test_parameter_merge_progress_tracks_each_hash_combination(monkeypatch) -> None:
    """Parameter merging reports and advances once for every merged list."""
    monkeypatch.setattr(
        AresParamInterface,
        "cache",
        {name: MagicMock(get=MagicMock(return_value=[])) for name in ("p1", "p2")},
    )
    monkeypatch.setattr(AresParamInterface, "create", MagicMock())
    progress_factory, tasks = _progress_factory()
    monkeypatch.setattr(merge, "AresProgress", progress_factory)

    plugin_input = MergeElement.model_construct(
        hash_lists_parameter=[["p1", "p2"], ["p1", "p2"]],
        hash_lists_data=[],
    )
    merge.ares_plugin(plugin_input)

    assert progress_factory.call_args_list == [
        call("Parameter merge", total=4),
        call("Data merge", total=0),
    ]
    assert tasks[0].advance.call_count == 4
    assert tasks[1].advance.call_count == 0
    assert AresParamInterface.create.call_count == 4


def test_data_merge_progress_tracks_each_hash_combination(monkeypatch) -> None:
    """Data merging reports and advances once for every merged list."""
    monkeypatch.setattr(
        AresDataInterface,
        "cache",
        {
            name: SimpleNamespace(stepsize=None, get=MagicMock(return_value=[]))
            for name in ("d1", "d2")
        },
    )
    monkeypatch.setattr(AresDataInterface, "create", MagicMock())
    progress_factory, tasks = _progress_factory()
    monkeypatch.setattr(merge, "AresProgress", progress_factory)

    plugin_input = MergeElement.model_construct(
        hash_lists_parameter=[],
        hash_lists_data=[["d1", "d2"], ["d1", "d2"]],
    )
    merge.ares_plugin(plugin_input)

    assert progress_factory.call_args_list == [
        call("Parameter merge", total=0),
        call("Data merge", total=4),
    ]
    assert tasks[0].advance.call_count == 0
    assert tasks[1].advance.call_count == 4
    assert AresDataInterface.create.call_count == 4
