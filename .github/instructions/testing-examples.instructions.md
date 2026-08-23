---
description: 'Guidelines for workflow example tests'
applyTo: 'test/examples/**/*.py'
---

## Workflow Example Test Instructions

These instructions apply to integration-style tests in `test/examples/` that
execute the workflows from the `examples/` directory end to end.

## Running

- Example tests are ignored by the default pytest run
  (`addopts = ["--ignore=test/examples"]`).
- Build prerequisites and run them with `make test-examples`
  (builds `examples/sim_unit` first, then runs `uv run pytest test/examples`).

## Conventions

- Every test file must start with the ARES license header docstring
  (see `python.instructions.md`) and use english for all content.
- Drive examples via their workflow files: keep one parametrized list of
  relative workflow paths (e.g. `workflow/data_interface/data_caching.wf.json`)
  and iterate over it with `pytest.mark.parametrize`.
- Resolve all filesystem paths before use: derive the repository root from the
  test file location (`project_root = Path(__file__).resolve().parent.parent.parent`),
  join relative entries such as the parametrized workflow paths onto it
  (`workflow_path = project_root / "examples" / workflow_file`), and pass fully
  resolved, stringified absolute paths for every subprocess argument
  (interpreter, workflow file, output directory).
- Invoke workflows through the project CLI (`python -m ares pipeline ...`),
  preferably via `uv run --project <repository root> python -m ares ...`.
  If the interpreter from `.venv` is resolved directly instead, select
  `Scripts` vs `bin` based on `os.name` for Windows compatibility.
- Always write outputs into a pytest-provided temporary directory (`tmp_path`);
  never write into `examples/`, the repository root, or user directories.
- Assert on process success (return code), absence of error patterns in output,
  and — where feasible — existence/validity of expected result files.
- Keep each parametrized case self-contained: no ordering dependencies between
  workflows and no shared mutable state.
