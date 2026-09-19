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

import argparse
import hashlib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def get_release_files(dist_dir: Path, docs_dir: Path) -> list[tuple[Path, str]]:
    """Return release files and their paths inside the archive."""
    patterns = ("*.whl", "*.tar.gz", "ares", "ares.exe")
    artifacts = sorted(
        {path for pattern in patterns for path in dist_dir.glob(pattern)}
    )
    if not any(path.suffix in {".whl", ".gz"} for path in artifacts):
        raise FileNotFoundError("No Python package artifacts found in dist.")
    if not docs_dir.is_dir():
        raise FileNotFoundError(f"Documentation directory not found: {docs_dir}")

    release_files = [(path, path.name) for path in artifacts]
    release_files.extend(
        (path, str(Path("docs") / path.relative_to(docs_dir)))
        for path in sorted(path for path in docs_dir.rglob("*") if path.is_file())
    )
    return release_files


def create_release_archive(dist_dir: Path, docs_dir: Path, version: str) -> Path:
    """Create checksums and a ZIP archive for the available release files."""
    release_files = get_release_files(dist_dir, docs_dir)
    checksum_file = dist_dir / "SHA256SUMS.txt"
    archive_file = dist_dir / f"ares-{version}-release.zip"

    with checksum_file.open("w", encoding="utf-8") as checksum_stream:
        for artifact, archive_name in release_files:
            digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
            checksum_stream.write(f"{digest}  {archive_name}\n")

    archive_file.unlink(missing_ok=True)
    with ZipFile(archive_file, "w", compression=ZIP_DEFLATED) as archive:
        for artifact, archive_name in (
            *release_files,
            (checksum_file, checksum_file.name),
        ):
            archive.write(artifact, arcname=archive_name)

    return archive_file


def main() -> None:
    """Parse release options and create the release archive."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument(
        "--docs-dir", type=Path, default=Path("docs/sphinx/_build/html")
    )
    args = parser.parse_args()
    archive_file = create_release_archive(Path("dist"), args.docs_dir, args.version)
    print(f"Created {archive_file}")


if __name__ == "__main__":
    main()
