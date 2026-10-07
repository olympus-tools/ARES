"""Download executable artifacts built from the tagged release commit."""

import argparse
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import quote, urlsplit

WORKFLOWS = (
    ("build_win_executable.yml", "ares-windows-executable", "ares.exe", "windows"),
    ("build_lin_executable.yml", "ares-linux-executable", "ares", "linux"),
)


class ReleaseArtifactError(RuntimeError):
    """Raised when a release executable cannot be retrieved safely."""


def _run_gh(args: list[str]) -> str:
    command = ["gh"]
    command.extend(args)
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as error:
        raise ReleaseArtifactError(
            "GitHub CLI `gh` is required. Install it and authenticate with "
            "`gh auth login`."
        ) from error

    if result.returncode != 0:
        details = result.stderr.strip()
        message = f"GitHub CLI command `gh {' '.join(args[:2])}` failed"
        if details:
            message = f"{message}: {details}"
        raise ReleaseArtifactError(message)
    return result.stdout


def _check_gh_auth() -> None:
    try:
        _run_gh(["auth", "status", "--hostname", "github.com"])
    except ReleaseArtifactError as error:
        raise ReleaseArtifactError(
            "GitHub CLI authentication failed. Run `gh auth login` and ensure "
            "your account can read Actions artifacts for this repository. "
            f"Details: {error}"
        ) from error


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


def _get_json_pages(args: list[str], repo: str) -> list[dict]:
    output = _run_gh(["api", "--paginate", "--slurp", *args])
    try:
        pages = json.loads(output)
    except json.JSONDecodeError as error:
        raise ReleaseArtifactError("GitHub CLI returned invalid JSON.") from error
    if not isinstance(pages, list) or not all(isinstance(page, dict) for page in pages):
        raise ReleaseArtifactError("GitHub CLI returned an unexpected API response.")
    return pages


def _workflow_runs(repo: str, workflow: str, sha: str) -> list[dict]:
    workflow_path = quote(workflow, safe="")
    endpoint = f"repos/{repo}/actions/workflows/{workflow_path}/runs"
    pages = _get_json_pages(
        [
            endpoint,
            "-f",
            f"head_sha={sha}",
            "-f",
            "branch=master",
            "-f",
            "event=push",
            "-f",
            "status=completed",
            "-F",
            "per_page=100",
        ],
        repo,
    )
    runs = []
    for page in pages:
        page_runs = page.get("workflow_runs")
        if not isinstance(page_runs, list):
            raise ReleaseArtifactError(
                f"GitHub returned an unexpected workflow-run response for {workflow}."
            )
        runs.extend(page_runs)
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


def _run_for_workflow(repo: str, workflow: str, sha: str) -> dict:
    return _select_successful_run(_workflow_runs(repo, workflow, sha), workflow, sha)


def _download_workflow_artifact(
    repo: str,
    run_id: int,
    artifact_name: str,
    executable_name: str,
    download_dir: Path,
) -> Path:
    download_dir.mkdir(parents=True)
    try:
        _run_gh(
            [
                "run",
                "download",
                str(run_id),
                "--name",
                artifact_name,
                "--dir",
                str(download_dir),
                "--repo",
                repo,
            ],
        )
    except ReleaseArtifactError as error:
        raise ReleaseArtifactError(
            f"Could not download required artifact {artifact_name!r} from workflow "
            f"run {run_id}; it may be missing or expired. {error}"
        ) from error

    files = sorted(path for path in download_dir.rglob("*") if path.is_file())
    if len(files) != 1 or files[0].name != executable_name:
        raise ReleaseArtifactError(
            f"Expected only {executable_name!r} in artifact {artifact_name!r}, "
            f"but found {[path.name for path in files]}."
        )
    if files[0].stat().st_size == 0:
        raise ReleaseArtifactError(
            f"Downloaded executable {executable_name!r} from {artifact_name!r} is empty."
        )
    return files[0]


def download_release_executables(version: str, dist_dir: Path) -> list[Path]:
    _check_gh_auth()
    repo = _repo_slug()
    sha = _release_tag_commit(version)

    with tempfile.TemporaryDirectory(prefix="ares-release-") as temporary_dir:
        temporary_path = Path(temporary_dir)
        staged_files = []
        for workflow, artifact_name, executable_name, platform in WORKFLOWS:
            run = _run_for_workflow(repo, workflow, sha)
            staged_executable = _download_workflow_artifact(
                repo,
                run["id"],
                artifact_name,
                executable_name,
                temporary_path / platform,
            )
            if platform == "linux":
                staged_executable.chmod(0o755)
            staged_files.append(
                (staged_executable, dist_dir / platform / executable_name)
            )

        downloaded_files = []
        for staged_file, destination in staged_files:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(staged_file, destination)
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
