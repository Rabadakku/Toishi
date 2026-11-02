"""The bash scripts: strict mode, syntax, Linux behaviour, backup end to end, launchd plist."""

import os
import plistlib
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = sorted([*(ROOT / "scripts").glob("*.sh"), ROOT / "scripts/git-hooks/pre-commit"])
EXECUTABLES = [p for p in SCRIPTS if p.name != "lib.sh"]
ON_MAC = sys.platform == "darwin"


@pytest.mark.parametrize("script", EXECUTABLES, ids=lambda p: p.name)
def test_scripts_are_strict_executable_bash(script: Path) -> None:
    text = script.read_text()
    assert text.startswith("#!/usr/bin/env bash\n")
    assert "set -euo pipefail" in text
    assert os.access(script, os.X_OK)


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda p: p.name)
def test_scripts_parse(script: Path) -> None:
    subprocess.run(["bash", "-n", str(script)], check=True)


def run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, check=False, **kwargs)  # type: ignore[call-overload,no-any-return]


def test_check_rejects_unknown_mode() -> None:
    proc = run([str(ROOT / "scripts/check.sh"), "everything"])
    assert proc.returncode != 0
    assert "unknown mode" in proc.stderr


@pytest.mark.skipif(ON_MAC, reason="checks the non-macOS refusal")
@pytest.mark.parametrize(
    "args",
    [["build.sh"], ["spike.sh"], ["check.sh", "app"], ["mac-runner.sh"], ["install-runner.sh"]],
)
def test_mac_only_scripts_refuse_clearly_elsewhere(args: list[str]) -> None:
    proc = run([str(ROOT / "scripts" / args[0]), *args[1:]])
    assert proc.returncode != 0
    assert "only runs on macOS" in proc.stderr


def make_repo(path: Path) -> Path:
    path.mkdir(parents=True)
    git = ["git", "-C", str(path), "-c", "user.name=t", "-c", "user.email=t@example.invalid"]
    run([*git, "init", "-q", "-b", "main"])
    (path / "scripts").mkdir()
    for name in ("backup.sh", "lib.sh"):
        shutil.copy(ROOT / "scripts" / name, path / "scripts" / name)
    run([*git, "add", "."])
    run([*git, "commit", "-q", "-m", "init"])
    return path


def test_backup_bundles_verifies_and_keeps_newest(tmp_path: Path) -> None:
    repo = make_repo(tmp_path / "code" / "repo")
    dest = tmp_path / "icloud"
    dest.mkdir()
    old = [f"toishi-2020-01-{day:02d}.bundle" for day in range(1, 31)]
    for name in [*old, "unrelated.txt"]:
        (dest / name).write_text("x")

    env = {**os.environ, "HOME": str(tmp_path), "TOISHI_BACKUP_DEST": str(dest)}
    proc = run([str(repo / "scripts/backup.sh")], env=env)
    assert proc.returncode == 0, proc.stderr

    bundles = sorted(p.name for p in dest.glob("toishi-*.bundle"))
    assert len(bundles) == 30
    assert "toishi-2020-01-01.bundle" not in bundles  # oldest pruned
    assert (dest / "unrelated.txt").exists()  # only our bundles are touched
    newest = dest / bundles[-1]
    assert newest.name > "toishi-2020"
    verify = run(["git", "-C", str(repo), "bundle", "verify", str(newest)])
    assert verify.returncode == 0, verify.stderr


@pytest.mark.parametrize("synced", ["Documents", "Library/Mobile Documents/com~apple~CloudDocs"])
def test_backup_refuses_a_repo_in_a_synced_folder(tmp_path: Path, synced: str) -> None:
    repo = make_repo(tmp_path / synced / "repo")
    env = {**os.environ, "HOME": str(tmp_path), "TOISHI_BACKUP_DEST": str(tmp_path / "out")}
    proc = run([str(repo / "scripts/backup.sh")], env=env)
    assert proc.returncode != 0
    assert "Move it to ~/Developer/toishi" in proc.stderr


def test_backup_needs_icloud_or_a_destination(tmp_path: Path) -> None:
    repo = make_repo(tmp_path / "code" / "repo")
    env = {k: v for k, v in os.environ.items() if k != "TOISHI_BACKUP_DEST"} | {
        "HOME": str(tmp_path)
    }
    proc = run([str(repo / "scripts/backup.sh")], env=env)
    assert proc.returncode != 0
    assert "iCloud Drive folder not found" in proc.stderr


def test_launchd_plist_runs_backup_nightly() -> None:
    path = ROOT / "packaging/launchd/com.toishi.backup.plist"
    plist = plistlib.loads(path.read_bytes())
    assert plist["Label"] == path.stem
    assert plist["ProgramArguments"] == ["/bin/bash", "__REPO__/scripts/backup.sh"]
    assert set(plist["StartCalendarInterval"]) == {"Hour", "Minute"}
    assert "__REPO__" in (ROOT / "README.md").read_text()  # install instructions exist


def test_launchd_plist_runs_the_mac_runner_on_requests() -> None:
    path = ROOT / "packaging/launchd/com.toishi.runner.plist"
    plist = plistlib.loads(path.read_bytes())
    assert plist["Label"] == path.stem
    assert plist["ProgramArguments"] == ["/bin/bash", "__REPO__/scripts/mac-runner.sh"]
    assert plist["WatchPaths"] == ["__REPO__/.runner/requests"]
    # Logs stay in the repo's (ignored) logs folder, where the build agents can read them.
    assert plist["StandardOutPath"] == plist["StandardErrorPath"] == "__REPO__/logs/runner.log"
    assert ".runner/" in (ROOT / ".gitignore").read_text().splitlines()


def runner_repo(tmp_path: Path) -> tuple[Path, dict[str, str]]:
    """A copy of the runner with a fake mac-run.sh and a uname that says Darwin."""
    repo = tmp_path / "repo"
    (repo / "scripts").mkdir(parents=True)
    for name in ("mac-runner.sh", "lib.sh"):
        shutil.copy(ROOT / "scripts" / name, repo / "scripts" / name)
    fake = repo / "scripts/mac-run.sh"
    fake.write_text('#!/usr/bin/env bash\necho "$1" >> ran.txt\nexit 3\n')
    fake.chmod(0o755)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    uname = bin_dir / "uname"
    uname.write_text("#!/bin/sh\necho Darwin\n")
    uname.chmod(0o755)
    env = {**os.environ, "PATH": f"{bin_dir}:{os.environ['PATH']}"}
    (repo / ".runner/requests").mkdir(parents=True)
    return repo, env


def read_status(repo: Path) -> dict[str, str]:
    lines = (repo / ".runner/status").read_text().splitlines()
    return dict(line.split("=", 1) for line in lines)


def test_runner_runs_only_allowed_modes_in_order(tmp_path: Path) -> None:
    repo, env = runner_repo(tmp_path)
    requests = repo / ".runner/requests"
    (requests / "r1").write_text("check\n")
    (requests / "r2").write_text("rm -rf / ; echo pwned\n")
    (requests / "r3").write_text("")

    proc = run([str(repo / "scripts/mac-runner.sh")], env=env)

    assert proc.returncode == 0, proc.stderr
    assert (repo / "ran.txt").read_text().splitlines() == ["check", "all"]
    assert not any(requests.iterdir())  # every request is consumed
    assert not (repo / ".runner/lock").exists()
    status = read_status(repo)
    assert status["id"] == "r3"
    assert status["mode"] == "all"
    assert status["state"] == "done"
    assert status["exit"] == "3"  # mac-run.sh's exit code is reported, not hidden


def test_runner_reports_a_rejected_request(tmp_path: Path) -> None:
    repo, env = runner_repo(tmp_path)
    (repo / ".runner/requests/bad").write_text("everything\n")

    proc = run([str(repo / "scripts/mac-runner.sh")], env=env)

    assert proc.returncode == 0, proc.stderr
    assert not (repo / "ran.txt").exists()
    assert read_status(repo)["state"] == "rejected"


def test_runner_leaves_requests_to_a_run_in_progress(tmp_path: Path) -> None:
    repo, env = runner_repo(tmp_path)
    (repo / ".runner/lock").mkdir()
    (repo / ".runner/lock/pid").write_text(str(os.getpid()))  # a live process holds it
    (repo / ".runner/requests/r1").write_text("check\n")

    proc = run([str(repo / "scripts/mac-runner.sh")], env=env)

    assert proc.returncode == 0, proc.stderr
    assert not (repo / "ran.txt").exists()
    assert (repo / ".runner/requests/r1").exists()


def test_runner_takes_over_a_stale_lock(tmp_path: Path) -> None:
    repo, env = runner_repo(tmp_path)
    (repo / ".runner/lock").mkdir()
    (repo / ".runner/lock/pid").write_text("999999999")  # no such process
    (repo / ".runner/requests/r1").write_text("setup\n")

    proc = run([str(repo / "scripts/mac-runner.sh")], env=env)

    assert proc.returncode == 0, proc.stderr
    assert (repo / "ran.txt").read_text().splitlines() == ["setup"]
    assert not (repo / ".runner/lock").exists()
