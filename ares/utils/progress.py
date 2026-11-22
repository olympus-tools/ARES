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

from __future__ import annotations

import sys
import threading
from types import TracebackType

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
)

from ares.utils.typechecked_dev import typechecked_dev as typechecked


class AresProgress:
    """A progress task managed by the application's shared Rich renderer."""

    _renderer: Progress | None = None
    _console: Console | None = None
    _active_tasks = 0
    _lock = threading.RLock()

    @typechecked
    def __init__(self, description: str, total: int):
        """Create a task in the shared renderer.

        Args:
            description: Label shown beside the progress bar.
            total: Number of units the task represents.
        """
        if total < 0:
            raise ValueError("Progress total must be non-negative.")

        with self._lock:
            if self.__class__._renderer is None:
                console = Console(file=sys.stdout)
                self.__class__._console = console
                self.__class__._renderer = Progress(
                    SpinnerColumn(),
                    TextColumn("{task.description}"),
                    BarColumn(),
                    TextColumn("{task.completed:,.0f}/{task.total:,.0f}"),
                    TimeElapsedColumn(),
                    console=console,
                    disable=not console.is_terminal,
                    redirect_stdout=False,
                    redirect_stderr=False,
                )

            self._renderer = self.__class__._renderer
            self._task_id: TaskID = self._renderer.add_task(description, total=total)
            if self.__class__._active_tasks == 0:
                self._renderer.start()
            self.__class__._active_tasks += 1
            self._closed = False

    @typechecked
    def advance(self, amount: int = 1) -> None:
        """Advance this task by the given amount.

        Args:
            amount: Number of units completed.
        """
        if self._closed:
            return
        self._renderer.update(self._task_id, advance=amount)

    @typechecked
    def __enter__(self) -> AresProgress:
        """Return this task for use as a context manager."""
        return self

    @typechecked
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        """Remove successful tasks and preserve failed tasks with a status label.

        Args:
            exc_type: Exception type raised within the context, if any.
            exc_value: Exception raised within the context, if any.
            traceback: Traceback associated with the exception, if any.

        Returns:
            bool: False so exceptions propagate unchanged.
        """
        del exc_value, traceback
        with self._lock:
            if self._closed:
                return False
            if exc_type is None:
                self._renderer.remove_task(self._task_id)
            else:
                task = next(
                    task for task in self._renderer.tasks if task.id == self._task_id
                )
                self._renderer.update(
                    self._task_id, description=f"{task.description} [failed]"
                )

            self._closed = True
            self.__class__._active_tasks -= 1
            if self.__class__._active_tasks == 0:
                self._renderer.stop()

        return False

    @classmethod
    @typechecked
    def is_rendering(cls) -> bool:
        """Return whether an enabled shared renderer currently has active tasks."""
        return bool(
            cls._renderer is not None
            and cls._console is not None
            and cls._console.is_terminal
            and cls._active_tasks
        )

    @classmethod
    @typechecked
    def print(cls, message: str) -> None:
        """Print a log message above the active progress tasks.

        Args:
            message: Already formatted log message.
        """
        if cls._console is not None:
            cls._console.print(message, markup=False, highlight=False, soft_wrap=True)
