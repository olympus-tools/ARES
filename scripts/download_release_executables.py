"""Download executable artifacts built from the tagged release commit."""

import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import (
    HTTPRedirectHandler,
    Request,
    build_opener,
)
from zipfile import BadZipFile, ZipFile

API_URL = "https://api.github.com"
WORKFLOWS = (
    ("build_win_executable.yml", "ares-windows-executable", "ares.exe", "windows"),
    ("build_lin_executable.yml", "ares-linux-executable", "ares", "linux"),
)


class ReleaseArtifactError(RuntimeError):
    """Raised when a release executable cannot be retrieved safely."""


class _SafeRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        source_url = urlsplit(req.full_url)
        target_url = urlsplit(newurl)
        if redirected is not None and (
            source_url.scheme != target_url.scheme
            or source_url.netloc != target_url.netloc
        ):
            for header_mapping in (
                redirected.headers,
                redirected.unredirected_hdrs,
            ):
                for header in tuple(header_mapping):
                    if header.lower() == "authorization":
                        del header_mapping[header]
        return redirected


def _repo_slug() -> str:
    remote = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        check=False,
        capture_output=True,
        text=True,
    )
    if remote.returncode != 0:
        raise ReleaseArtifactError(
            "Could not read the origin Git remote to identify the GitHub repository."
        )

    remote_url = remote.stdout.strip()
    if "://" in remote_url:
        parsed = urlsplit(remote_url)
        host = parsed.hostname
        path = parsed.path
    else:
        match = re.fullmatch(r"(?:[^@]+@)?([^:]+):(.+)", remote_url)
        if match is None:
            raise ReleaseArtifactError(
                "The origin remote is not a supported GitHub URL."
            )
        host, path = match.groups()

    if host is None or host.lower() != "github.com":
        raise ReleaseArtifactError("The origin remote must point to github.com.")

    parts = path.strip("/").removesuffix(".git").split("/")
    if len(parts) != 2 or not all(parts):
        raise ReleaseArtifactError(
            "Could not identify the owner and repository in the origin remote."
        )
    return "/".join(parts)


def _release_tag_commit(version: str) -> str:
    tag = f"v{version}"
    result = subprocess.run(
        ["git", "rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise ReleaseArtifactError(
            f"Could not resolve tag {tag!r} to a commit. Fetch the release tag first."
        )
    return result.stdout.strip()


def _open_request(opener, url: str, token: str):
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "ARES-release",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        return opener.open(request, timeout=120)
    except HTTPError as error:
        if error.code in {401, 403}:
            raise ReleaseArtifactError(
                "GitHub denied access. Check that GH_TOKEN or GITHUB_TOKEN is valid "
                "and has Actions: read permission for this repository."
            ) from error
        if error.code == 404:
            raise ReleaseArtifactError(
                "GitHub could not find the requested workflow or artifact. Check "
                "the repository, tag commit, and artifact retention."
            ) from error
        raise ReleaseArtifactError(
            f"GitHub request failed with HTTP {error.code} ({error.reason})."
        ) from error
    except URLError as error:
        raise ReleaseArtifactError(
            f"Could not connect to GitHub: {error.reason}."
        ) from error


def _get_json(opener, url: str, token: str) -> dict:
    with _open_request(opener, url, token) as response:
        try:
            payload = json.load(response)
        except json.JSONDecodeError as error:
            raise ReleaseArtifactError("GitHub returned invalid JSON.") from error
    if not isinstance(payload, dict):
        raise ReleaseArtifactError("GitHub returned an unexpected API response.")
    return payload


def _workflow_runs(opener, repo: str, workflow: str, sha: str, token: str) -> list:
    runs_url = (
        f"{API_URL}/repos/{repo}/actions/workflows/{quote(workflow, safe='')}/runs"
    )
    runs = []
    page = 1
    total_count = None
    while total_count is None or len(runs) < total_count:
        query = urlencode(
            {
                "head_sha": sha,
                "branch": "master",
                "event": "push",
                "status": "completed",
                "per_page": 100,
                "page": page,
            }
        )
        payload = _get_json(opener, f"{runs_url}?{query}", token)
        page_runs = payload.get("workflow_runs")
        total_count = payload.get("total_count")
        if not isinstance(page_runs, list) or not isinstance(total_count, int):
            raise ReleaseArtifactError(
                f"GitHub returned an unexpected workflow-run response for {workflow}."
            )
        runs.extend(page_runs)
        if not page_runs:
            break
        page += 1
    return runs


def _select_successful_run(runs: list, workflow: str, sha: str) -> dict:
    matching_runs = [
        run
        for run in runs
        if run.get("head_sha") == sha
        and run.get("branch") == "master"
        and run.get("event") == "push"
        and run.get("conclusion") == "success"
    ]
    if not matching_runs:
        raise ReleaseArtifactError(
            f"No successful master push run for {workflow} matches release commit "
            f"{sha}."
        )
    return max(
        matching_runs,
        key=lambda run: (
            run.get("run_number", 0),
            run.get("run_attempt", 0),
            run.get("created_at", ""),
        ),
    )


def _run_for_workflow(opener, repo: str, workflow: str, sha: str, token: str) -> dict:
    runs = _workflow_runs(opener, repo, workflow, sha, token)
    return _select_successful_run(runs, workflow, sha)


def _artifacts_for_run(opener, repo: str, run_id: int, token: str) -> list:
    url = f"{API_URL}/repos/{repo}/actions/runs/{run_id}/artifacts"
    artifacts = []
    page = 1
    total_count = None
    while total_count is None or len(artifacts) < total_count:
        query = urlencode({"per_page": 100, "page": page})
        payload = _get_json(opener, f"{url}?{query}", token)
        page_artifacts = payload.get("artifacts")
        total_count = payload.get("total_count")
        if not isinstance(page_artifacts, list) or not isinstance(total_count, int):
            raise ReleaseArtifactError(
                f"GitHub returned an unexpected artifact response for run {run_id}."
            )
        artifacts.extend(page_artifacts)
        if not page_artifacts:
            break
        page += 1
    return artifacts


def _select_artifact(artifacts: list, name: str, workflow: str, run_id: int) -> dict:
    named_artifacts = [
        artifact for artifact in artifacts if artifact.get("name") == name
    ]
    available_artifacts = [
        artifact for artifact in named_artifacts if not artifact.get("expired", False)
    ]
    if not available_artifacts:
        if named_artifacts:
            reason = "has expired"
        else:
            reason = "was not uploaded"
        raise ReleaseArtifactError(
            f"Artifact {name!r} {reason} in the successful {workflow} run {run_id}."
        )
    if len(available_artifacts) != 1:
        raise ReleaseArtifactError(
            f"Expected one {name!r} artifact in {workflow} run {run_id}, found "
            f"{len(available_artifacts)}."
        )
    return available_artifacts[0]


def _download_artifact(
    opener, repo: str, artifact_id: int, token: str, destination: Path
) -> None:
    url = f"{API_URL}/repos/{repo}/actions/artifacts/{artifact_id}/zip"
    with (
        _open_request(opener, url, token) as response,
        destination.open("wb") as output,
    ):
        shutil.copyfileobj(response, output)
    if destination.stat().st_size == 0:
        raise ReleaseArtifactError(f"Downloaded artifact {artifact_id} is empty.")


def _extract_executable(
    artifact_zip: Path, executable_name: str, destination: Path
) -> None:
    try:
        with ZipFile(artifact_zip) as archive:
            if archive.testzip() is not None:
                raise ReleaseArtifactError(
                    f"Artifact archive {artifact_zip.name} failed its CRC check."
                )
            files = [entry for entry in archive.infolist() if not entry.is_dir()]
            if len(files) != 1 or files[0].filename != executable_name:
                raise ReleaseArtifactError(
                    f"Expected {executable_name!r} as the only file in "
                    f"{artifact_zip.name}."
                )
            with archive.open(files[0]) as source, destination.open("wb") as output:
                shutil.copyfileobj(source, output)
    except BadZipFile as error:
        raise ReleaseArtifactError(
            f"Downloaded artifact {artifact_zip.name} is not a valid ZIP archive."
        ) from error

    if destination.stat().st_size == 0:
        raise ReleaseArtifactError(f"Downloaded executable {executable_name} is empty.")
    if executable_name == "ares":
        destination.chmod(0o755)


def download_release_executables(version: str, dist_dir: Path) -> list[Path]:
    token = (
        os.environ.get("GH_TOKEN", "").strip()
        or os.environ.get("GITHUB_TOKEN", "").strip()
    )
    if not token:
        raise ReleaseArtifactError(
            "Set GH_TOKEN or GITHUB_TOKEN with Actions: read permission to download "
            "release executables."
        )

    repo = _repo_slug()
    sha = _release_tag_commit(version)
    opener = build_opener(_SafeRedirectHandler)

    with tempfile.TemporaryDirectory(prefix="ares-release-") as temporary_dir:
        temporary_path = Path(temporary_dir)
        staged_files = []
        for workflow, artifact_name, executable_name, platform in WORKFLOWS:
            run = _run_for_workflow(opener, repo, workflow, sha, token)
            artifact = _select_artifact(
                _artifacts_for_run(opener, repo, run["id"], token),
                artifact_name,
                workflow,
                run["id"],
            )
            artifact_zip = temporary_path / f"{platform}.zip"
            staged_executable = temporary_path / platform / executable_name
            staged_executable.parent.mkdir(parents=True)
            _download_artifact(opener, repo, artifact["id"], token, artifact_zip)
            _extract_executable(artifact_zip, executable_name, staged_executable)
            staged_files.append(
                (staged_executable, dist_dir / platform / executable_name)
            )

        downloaded_files = []
        for staged_file, destination in staged_files:
            destination.parent.mkdir(parents=True, exist_ok=True)
            staged_file.replace(destination)
            downloaded_files.append(destination)
    return downloaded_files


def main() -> None:
    """Download the Windows and Linux release executables."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    downloaded_files = download_release_executables(args.version, Path("dist"))
    for path in downloaded_files:
        print(f"Downloaded {path}")


if __name__ == "__main__":
    try:
        main()
    except ReleaseArtifactError as error:
        raise SystemExit(f"Error: {error}") from error
