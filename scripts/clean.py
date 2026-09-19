r"""
________________________________________________________________________
|                                                                      |
|               $$$$$$\  $$$$$$$\  $$$$$$$$\  $$$$$$\                  |
|              $$ __$$\ $$ |  $$ |$$ _____|$$ __$$\                 |
|              $$ /  $$ |$$ |  $$ |$$ |      $$ /  \__|                |
|              $$$$$$$$ |$$$$$$$  |$$$$$\    \$$$$$$\                  |
|              $$ __$$ |$$ __$$< $$ __|    \____$$\                 |
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

import shutil
from pathlib import Path

from typeguard import typechecked


@typechecked
def remove_path(path: Path) -> bool:
    """Remove a file, directory, or symbolic link if it exists."""
    if not path.exists() and not path.is_symlink():
        return False
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()
    return True


@typechecked
def remove_matching_files(root: Path, pattern: str) -> int:
    """Remove files below root matching a glob pattern."""
    paths = [path for path in root.rglob(pattern) if path.is_file()]
    return sum(remove_path(path) for path in paths)


@typechecked
def remove_matching_directories(root: Path, directory_name: str) -> int:
    """Remove directories below root with the given name."""
    paths = [path for path in root.rglob(directory_name) if path.is_dir()]
    return sum(remove_path(path) for path in paths)


@typechecked
def clean_generated_files(root: Path) -> int:
    """Remove generated project files and return the number of removed paths."""
    removed = 0
    for relative_path in (
        "logs",
        "build",
        "dist",
        "examples/output",
        "docs/sphinx/_build",
        "cov_annotate",
        "htmlcov",
    ):
        removed += int(remove_path(root / relative_path))

    for path in root.glob("*.egg-info"):
        removed += int(remove_path(path))

    removed += remove_matching_files(root, "*.pyc")
    removed += remove_matching_files(root, "*.spec")
    removed += remove_matching_files(root / "examples/sim_unit", "*.so")
    removed += remove_matching_directories(root, "__pycache__")
    removed += remove_matching_directories(root, "log")
    removed += remove_matching_directories(root, ".pytest_cache")
    removed += remove_matching_directories(root, ".ruff_cache")

    for path in (root / ".coverage",):
        removed += int(remove_path(path))
    removed += sum(int(remove_path(path)) for path in root.glob(".coverage.*"))
    return removed


@typechecked
def main() -> int:
    """Prompt for confirmation and remove generated project files."""
    answer = input(
        "WARNING: This will permanently delete generated files, caches, and logs. "
        "Continue? [y/n] "
    )
    if answer.strip().lower() != "y":
        print("Clean cancelled.")
        return 0

    root = Path(__file__).resolve().parents[1]
    removed = clean_generated_files(root)
    print(f"Project cleaned successfully. Removed {removed} paths.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
