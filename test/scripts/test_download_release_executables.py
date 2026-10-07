import json
import runpy
from pathlib import Path

import pytest

_SCRIPT = runpy.run_path(
    str(
        Path(__file__).resolve().parents[2]
        / "scripts"
        / "download_release_executables.py"
    )
)
ReleaseArtifactError = _SCRIPT["ReleaseArtifactError"]
_check_gh_auth = _SCRIPT["_check_gh_auth"]
_download_workflow_artifact = _SCRIPT["_download_workflow_artifact"]
_select_successful_run = _SCRIPT["_select_successful_run"]
_workflow_runs = _SCRIPT["_workflow_runs"]
download_release_executables = _SCRIPT["download_release_executables"]
_GLOBALS = download_release_executables.__globals__


def test_check_gh_auth_reports_login_guidance(monkeypatch):
    def fail_auth_check(args):
        raise ReleaseArtifactError("not logged in")

    monkeypatch.setitem(_GLOBALS, "_run_gh", fail_auth_check)

    with pytest.raises(ReleaseArtifactError, match="gh auth login"):
        _check_gh_auth()


def test_workflow_runs_query_exact_sha_and_master_push(monkeypatch):
    calls = []

    def fake_gh(args):
        calls.append(args)
        return json.dumps([{"workflow_runs": []}])

    monkeypatch.setitem(_GLOBALS, "_run_gh", fake_gh)

    assert _workflow_runs("owner/repo", "build_win_executable.yml", "tag-sha") == []
    args = calls[0]
    assert "repos/owner/repo/actions/workflows/build_win_executable.yml/runs" in args
    assert "--paginate" in args
    assert "--slurp" in args
    assert "head_sha=tag-sha" in args
    assert "branch=master" in args
    assert "event=push" in args


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


def test_download_workflow_artifact_uses_gh_and_validates_file(tmp_path, monkeypatch):
    def fake_gh(args):
        assert args[:3] == ["run", "download", "123"]
        assert "--name" in args
        assert args[args.index("--name") + 1] == "ares-linux-executable"
        assert args[args.index("--repo") + 1] == "owner/repo"
        download_dir = Path(args[args.index("--dir") + 1])
        (download_dir / "ares").write_bytes(b"linux executable")
        return ""

    monkeypatch.setitem(_GLOBALS, "_run_gh", fake_gh)
    download_dir = tmp_path / "download"

    executable = _download_workflow_artifact(
        "owner/repo",
        123,
        "ares-linux-executable",
        "ares",
        download_dir,
    )

    assert executable.read_bytes() == b"linux executable"


def test_download_workflow_artifact_errors_when_upload_is_missing(
    tmp_path, monkeypatch
):
    def fail_download(args):
        raise ReleaseArtifactError("no artifact found")

    monkeypatch.setitem(_GLOBALS, "_run_gh", fail_download)

    with pytest.raises(ReleaseArtifactError, match="may be missing or expired"):
        _download_workflow_artifact(
            "owner/repo",
            123,
            "ares-linux-executable",
            "ares",
            tmp_path / "download",
        )


def test_release_download_stores_both_platforms_and_keeps_linux_executable(
    tmp_path, monkeypatch
):
    def create_executable(repo, run_id, artifact_name, executable_name, download_dir):
        download_dir.mkdir(parents=True)
        executable = download_dir / executable_name
        executable.write_bytes(artifact_name.encode())
        return executable

    monkeypatch.setitem(_GLOBALS, "_check_gh_auth", lambda: None)
    monkeypatch.setitem(_GLOBALS, "_repo_slug", lambda: "owner/repo")
    monkeypatch.setitem(_GLOBALS, "_release_tag_commit", lambda version: "tag-sha")
    monkeypatch.setitem(
        _GLOBALS,
        "_run_for_workflow",
        lambda repo, workflow, sha: {"id": 1},
    )
    monkeypatch.setitem(_GLOBALS, "_download_workflow_artifact", create_executable)

    files = download_release_executables("0.1.0", tmp_path / "dist")

    assert [path.relative_to(tmp_path / "dist").as_posix() for path in files] == [
        "windows/ares.exe",
        "linux/ares",
    ]
    assert files[0].read_bytes() == b"ares-windows-executable"
    assert files[1].read_bytes() == b"ares-linux-executable"
    assert files[1].stat().st_mode & 0o111
