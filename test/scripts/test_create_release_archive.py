import hashlib
import runpy
import zipfile
from pathlib import Path

import pytest

_SCRIPT = runpy.run_path(
    str(Path(__file__).resolve().parents[2] / "scripts" / "create_release_archive.py")
)
create_release_archive = _SCRIPT["create_release_archive"]
get_release_files = _SCRIPT["get_release_files"]


def test_release_archive_contains_both_platform_executables_and_permissions(
    tmp_path,
):
    dist_dir = tmp_path / "dist"
    docs_dir = tmp_path / "docs"
    dist_dir.mkdir()
    docs_dir.mkdir()
    (dist_dir / "ares-0.1.0-py3-none-any.whl").write_bytes(b"wheel")
    (dist_dir / "ares-0.1.0.tar.gz").write_bytes(b"source")
    windows_executable = dist_dir / "windows" / "ares.exe"
    windows_executable.parent.mkdir()
    windows_executable.write_bytes(b"windows executable")
    linux_executable = dist_dir / "linux" / "ares"
    linux_executable.parent.mkdir()
    linux_executable.write_bytes(b"linux executable")
    linux_executable.chmod(0o755)
    (docs_dir / "index.html").write_text("Documentation", encoding="utf-8")

    archive_path = create_release_archive(dist_dir, docs_dir, "0.1.0")

    with zipfile.ZipFile(archive_path) as archive:
        assert {
            "ares-0.1.0-py3-none-any.whl",
            "ares-0.1.0.tar.gz",
            "windows/ares.exe",
            "linux/ares",
            "docs/index.html",
            "SHA256SUMS.txt",
        }.issubset(archive.namelist())
        linux_mode = archive.getinfo("linux/ares").external_attr >> 16
        assert linux_mode & 0o111
        checksums = archive.read("SHA256SUMS.txt").decode()
        assert (
            f"{hashlib.sha256(b'linux executable').hexdigest()}  linux/ares"
            in checksums
        )
        assert (
            f"{hashlib.sha256(b'windows executable').hexdigest()}  windows/ares.exe"
            in checksums
        )


def test_release_archive_requires_both_platform_executables(tmp_path):
    dist_dir = tmp_path / "dist"
    docs_dir = tmp_path / "docs"
    dist_dir.mkdir()
    docs_dir.mkdir()
    (dist_dir / "ares-0.1.0-py3-none-any.whl").write_bytes(b"wheel")
    (dist_dir / "ares-0.1.0.tar.gz").write_bytes(b"source")
    stale_local_executable = dist_dir / "ares"
    stale_local_executable.write_bytes(b"old local executable")
    windows_executable = dist_dir / "windows" / "ares.exe"
    windows_executable.parent.mkdir()
    windows_executable.write_bytes(b"windows executable")

    with pytest.raises(FileNotFoundError, match="linux/ares"):
        get_release_files(dist_dir, docs_dir)
