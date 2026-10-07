import runpy
import zipfile
from pathlib import Path
from urllib.request import Request

import pytest

_SCRIPT = runpy.run_path(
    str(
        Path(__file__).resolve().parents[2]
        / "scripts"
        / "download_release_executables.py"
    )
)
ReleaseArtifactError = _SCRIPT["ReleaseArtifactError"]
_SafeRedirectHandler = _SCRIPT["_SafeRedirectHandler"]
_extract_executable = _SCRIPT["_extract_executable"]
_select_artifact = _SCRIPT["_select_artifact"]
_select_successful_run = _SCRIPT["_select_successful_run"]


def test_cross_host_redirect_does_not_forward_github_token():
    request = Request(
        "https://api.github.com/artifact",
        headers={"Authorization": "Bearer test-token"},
    )

    redirected = _SafeRedirectHandler().redirect_request(
        request,
        None,
        302,
        "Found",
        {},
        "https://artifact-storage.example/download",
    )

    assert "Authorization" not in redirected.headers
    assert "Authorization" not in redirected.unredirected_hdrs


def test_select_successful_run_requires_exact_master_push_sha():
    sha = "release-sha"
    runs = [
        {
            "id": 1,
            "head_sha": "different-sha",
            "branch": "master",
            "event": "push",
            "conclusion": "success",
        },
        {
            "id": 2,
            "head_sha": sha,
            "branch": "feature",
            "event": "push",
            "conclusion": "success",
        },
        {
            "id": 3,
            "head_sha": sha,
            "branch": "master",
            "event": "pull_request",
            "conclusion": "success",
        },
        {
            "id": 4,
            "head_sha": sha,
            "branch": "master",
            "event": "push",
            "conclusion": "failure",
        },
        {
            "id": 5,
            "head_sha": sha,
            "branch": "master",
            "event": "push",
            "conclusion": "success",
            "run_number": 10,
            "run_attempt": 1,
        },
        {
            "id": 6,
            "head_sha": sha,
            "branch": "master",
            "event": "push",
            "conclusion": "success",
            "run_number": 11,
            "run_attempt": 1,
        },
    ]

    assert _select_successful_run(runs, "build.yml", sha)["id"] == 6


def test_select_successful_run_errors_when_exact_commit_run_is_missing():
    with pytest.raises(ReleaseArtifactError, match="No successful master push run"):
        _select_successful_run([], "build.yml", "tag-sha")


def test_select_artifact_errors_when_upload_is_missing_or_expired():
    with pytest.raises(ReleaseArtifactError, match="was not uploaded"):
        _select_artifact([], "ares-linux-executable", "build.yml", 1)
    with pytest.raises(ReleaseArtifactError, match="has expired"):
        _select_artifact(
            [{"name": "ares-linux-executable", "expired": True}],
            "ares-linux-executable",
            "build.yml",
            1,
        )


def test_extract_executable_rejects_unexpected_artifact_contents(tmp_path):
    artifact_zip = tmp_path / "linux.zip"
    with zipfile.ZipFile(artifact_zip, "w") as archive:
        archive.writestr("other-file", "not the executable")

    with pytest.raises(ReleaseArtifactError, match="Expected 'ares'"):
        _extract_executable(artifact_zip, "ares", tmp_path / "ares")


def test_extract_executable_sets_linux_executable_permission(tmp_path):
    artifact_zip = tmp_path / "linux.zip"
    with zipfile.ZipFile(artifact_zip, "w") as archive:
        archive.writestr("ares", "linux executable")
    destination = tmp_path / "ares"

    _extract_executable(artifact_zip, "ares", destination)

    assert destination.read_bytes() == b"linux executable"
    assert destination.stat().st_mode & 0o111
