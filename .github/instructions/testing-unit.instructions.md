---
description: 'Guidelines for writing and running unit tests'
applyTo: 'test/**/*.py'
---

## Unit Testing Instructions

## Running Tests

Tests are executed with `pytest` via `uv` inside the project virtual
environment. Create or sync the environment first with `make setup-venv`
(runs `uv sync --all-extras`, managed through `[tool.uv.sources]` in
`pyproject.toml`):

- Run all unit tests: `make test-requirements` (equivalent to `uv run pytest`).
- Run a single test module: `uv run pytest test/utils/test_logger.py`.
- Run tests with coverage report: `make test-coverage`
  (uses `--cov --cov-report=html --cov-report=term-missing`, configured in `.coveragerc`).
- Workflow example tests are excluded by default (`addopts = ["--ignore=test/examples"]`);
  run them separately via `make test-examples`
  (builds `examples/sim_unit` first) or directly with
  `uv run pytest test/examples`.

## Test Discovery and Layout

- All tests live under the `test/` directory (`testpaths = ["test"]` in `pyproject.toml`).
- Test modules must match the pattern `test_*.py` and mirror the package layout,
  e.g. code in `ares/utils/decorators.py` is tested in `test/utils/test_decorators.py`.
- Shared test data belongs in a `data` subfolder next to the tests that use it
  (see `test/interfaces/data`), never in the package source.
- Do not add new top-level directories under `test/` without updating `testpaths`
  or `addopts` accordingly.

## File Conventions

- Every test file must start with the ARES license header docstring
  (see `python.instructions.md`).
- Group related tests with a section comment above the first test,
  e.g. `# TEST: safely_run`.
- Name test functions descriptively after the behavior under test:
  `test_<function>_<scenario>` (e.g. `test_safely_run_exception`,
  `test_safely_run_exception_msg`).
- Document every test function with a **Google style** docstring describing the
  scenario and expected outcome. Document fixture parameters in an `Args:` section.
- All content, comments, and docstrings must be written in English.

## Writing Good Tests

- Cover positive, negative, and edge cases for critical functions
  (empty inputs, invalid data types, boundary values).
- Follow AAA pattern: Arrange, Act, Assert
- Write descriptive test names that explain the behavior being tested
- Keep tests focused on one specific behavior
- Use built-in pytest fixtures where possible:
  - `tmp_path` for temporary files and output directories.
  - `caplog` to assert on log records emitted by `@safely_run` / `@error_msg`.
- Use `pytest.mark.parametrize` when several inputs share the same assertions.
- Assert exact values where practical; otherwise compare against a reference
  computation with a small tolerance (`pytest.approx` or explicit epsilon).
- Keep tests independent, deterministic, and offline: no network access,
  no reliance on execution order, no absolute user paths.
- Clean up any files created outside `tmp_path`; do not write into the repository
  during tests.
- Mark long-running or environment-dependent tests explicitly so they can be
  deselected, and never let them fail silently.

### Key Testing Practices
- Use pytest fixtures for setup and teardown
- Mock external dependencies (APIs, file operations)
- Use parameterized tests for testing multiple similar scenarios
- Test edge cases and error conditions, not just happy paths
## Coverage

- Coverage measures the `ares` package only (`source = ares` in `.coveragerc`),
  with branch coverage enabled. The goal is for the tests to cover all lines
  of code.
- New features must come with tests that keep overall coverage stable or improving.
- Generate an annotated coverage report with:

  ```bash
  uv run pytest --cov --cov-report=annotate:cov_annotate
  ```

- To check coverage of a specific module, scope the report, optionally limited
  to its test module:

  ```bash
  uv run pytest --cov=ares.utils.decorators --cov-report=annotate:cov_annotate
  uv run pytest test/utils/test_decorators.py --cov=ares.utils.decorators \
      --cov-report=annotate:cov_annotate
  ```

- Open the `cov_annotate/` directory to view the annotated source code: one
  file per source file. Files already at 100% coverage can be skipped; in all
  other files, every line starting with `!` is not covered by tests. Add tests
  to cover the missing lines.
- Keep running the tests and improving coverage until no uncovered lines remain.
- Use `pragma: no cover` sparingly and only for genuinely unreachable code.

## Example Test Pattern

Tests are written as plain functions working on real objects. Test classes
and per-class fixtures are avoided; negative cases use `pytest.raises`, log
output is asserted with the `caplog` fixture, robust functions are exercised
through the project decorators, and `unittest.mock` is reserved for external
systems (see below):

```python
# NOTE: the file must start with the ARES license header docstring
# (see python.instructions.md), omitted here for brevity.

from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pytest
from asammdf.blocks.utils import MdfException

from ares.interface.data.ares_signal import AresSignal
from ares.interface.data.mf4_handler import MF4Handler
from ares.utils.decorators import safely_run


# TEST: AresSignal input validation
@pytest.mark.parametrize(
    "timestamps, value",
    [
        # 2d timestamps are rejected
        (
            np.array([[1, 2], [3, 4]], dtype=np.float32),
            np.array([1, 2, 3, 4], dtype=np.float32),
        ),
        # 2d values are rejected
        (
            np.array([1, 2, 3, 4], dtype=np.float32),
            np.array([[1, 2], [3, 4]], dtype=np.float32),
        ),
    ],
)
def test_ares_signal_wrong_dimension(timestamps, value):
    """
    Tests that ValueError is raised when timestamps and value dimensions
    do not match.

    Args:
        timestamps (np.ndarray): Timestamp array with wrong dimensionality.
        value (np.ndarray): Value array with wrong dimensionality.
    """
    with pytest.raises(ValueError):
        AresSignal(label="test_signal", timestamps=timestamps, value=value)


# TEST: safely_run
def test_safely_run_logs_exception(caplog):
    """
    Tests that the decorated function returns the default return value and
    logs the configured message when it raises an exception.

    Args:
        caplog: pytest fixture capturing log records.
    """

    @safely_run(default_return=float("nan"), exception_msg="SIGNAL LOST")
    def failing_signal_processing():
        raise ValueError("sensor disconnected")

    result = failing_signal_processing()

    assert result != result  # NaN propagates as default return value
    assert "SIGNAL LOST" in caplog.text


# TEST: MF4Handler error handling
@patch("ares.interface.data.mf4_handler.MDF", side_effect=MdfException("corrupted"))
def test_mf4handler_raises_on_corrupted_file(mock_mdf):
    """
    Tests that MF4Handler propagates errors from the external asammdf reader,
    simulated by patching MDF instead of shipping a corrupted binary fixture.

    Args:
        mock_mdf (Mock): Patched asammdf MDF reader.
    """
    with pytest.raises(MdfException):
        MF4Handler(file_path=Path("corrupted.mf4"))
```

Guidelines for when mocking makes sense:

- Use `unittest.mock` for boundaries that cannot be exercised reliably in unit
  tests: external file formats, hardware, network, or expensive third-party
  readers (e.g. patching `ares.interface.data.mf4_handler.MDF`).
- Patch where the dependency is imported (`module.MDF`), not at its origin.
- Never mock the code under test - mock its boundaries only.
- Receive mocks as named test arguments and keep their setup inside the test.
