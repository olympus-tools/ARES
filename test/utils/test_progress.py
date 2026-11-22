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

import logging
from io import StringIO

import pytest
from rich.progress import TimeElapsedColumn
from rich.text import Text

from ares.utils.logger import AresStreamHandler
from ares.utils.progress import AresProgress


@pytest.fixture(autouse=True)
def reset_progress_renderer(monkeypatch: pytest.MonkeyPatch) -> None:
    """Isolate shared renderer state between progress-bar tests."""
    monkeypatch.setattr(AresProgress, "_renderer", None)
    monkeypatch.setattr(AresProgress, "_console", None)
    monkeypatch.setattr(AresProgress, "_active_tasks", 0)


def test_progress_bars_share_renderer_and_remove_successful_tasks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Nested independently created bars share a renderer and finish cleanly."""
    monkeypatch.setattr("sys.stdout", StringIO())

    with AresProgress("workflow", total=2) as workflow:
        renderer = workflow._renderer
        assert isinstance(renderer.columns[-1], TimeElapsedColumn)
        workflow.advance()
        with AresProgress("references", total=1) as references:
            assert references._renderer is renderer
            references.advance()

        assert [task.description for task in renderer.tasks] == ["workflow"]

    assert renderer.tasks == []


def test_failed_progress_bar_remains_with_failure_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed task stays in the renderer and is labeled as failed."""
    monkeypatch.setattr("sys.stdout", StringIO())

    with pytest.raises(RuntimeError, match="failed run"):
        with AresProgress("simulation", total=3) as progress:
            progress.advance()
            raise RuntimeError("failed run")

    assert len(progress._renderer.tasks) == 1
    assert progress._renderer.tasks[0].description == "simulation [failed]"


def test_progress_is_disabled_for_non_tty_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Non-interactive output disables rendering while task lifecycle still works."""
    monkeypatch.setattr("sys.stdout", StringIO())

    with AresProgress("workflow", total=1) as progress:
        assert progress._renderer.disable
        progress.advance()

    assert progress._renderer.tasks == []


def test_empty_progress_task_can_finish(monkeypatch: pytest.MonkeyPatch) -> None:
    """Zero-item workflows remove their task without attempting any advances."""
    monkeypatch.setattr("sys.stdout", StringIO())

    with AresProgress("empty workflow", total=0) as progress:
        pass

    assert progress._renderer.tasks == []


def test_set_description_updates_label_and_escapes_markup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Variable text is appended to the fixed description and escaped."""
    monkeypatch.setattr("sys.stdout", StringIO())

    with AresProgress("Pipeline:", total=2) as progress:
        progress.set_description("data[raw]")
        task = progress._renderer.tasks[0]
        assert task.description == r"Pipeline: data\[raw]"
        assert Text.from_markup(task.description).plain == "Pipeline: data[raw]"

    progress.set_description("ignored after close")


def test_negative_progress_total_is_rejected() -> None:
    """Negative task totals raise a meaningful value error."""
    with pytest.raises(ValueError, match="non-negative"):
        AresProgress("invalid", total=-1)


def test_log_records_use_shared_console_while_progress_is_active(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Active progress rendering routes log messages through Rich's console."""

    class InteractiveOutput(StringIO):
        def isatty(self) -> bool:
            return True

    output = InteractiveOutput()
    monkeypatch.setattr("sys.stdout", output)

    with AresProgress("workflow", total=1):
        handler = AresStreamHandler(stream=output)
        handler.setFormatter(logging.Formatter("%(message)s"))
        handler.emit(
            logging.LogRecord(
                "test", logging.INFO, "", 0, "visible log message", (), None
            )
        )

    assert "visible log message" in output.getvalue()
