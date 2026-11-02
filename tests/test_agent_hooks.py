"""The sub-agent loop guard (scripts/agent-hooks/loop_guard.py)."""

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/agent-hooks/loop_guard.py"


def call(
    event: dict[str, object], state_dir: Path, max_calls: int = 400
) -> subprocess.CompletedProcess[str]:
    env = {"TOISHI_AGENT_GUARD_DIR": str(state_dir), "TOISHI_AGENT_MAX_CALLS": str(max_calls)}
    return subprocess.run(
        [sys.executable, "-I", str(SCRIPT)],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def bash(command: str, agent: str | None = "a1") -> dict[str, object]:
    event: dict[str, object] = {"tool_name": "Bash", "tool_input": {"command": command}}
    if agent:
        event["agent_id"] = agent
    return event


def test_main_session_is_never_limited(tmp_path: Path) -> None:
    for _ in range(5):
        assert call(bash("ls", agent=None), tmp_path).returncode == 0


def test_third_identical_call_in_a_row_is_refused(tmp_path: Path) -> None:
    assert call(bash("pytest -q"), tmp_path).returncode == 0
    assert call(bash("pytest -q"), tmp_path).returncode == 0
    refused = call(bash("pytest -q"), tmp_path)
    assert refused.returncode == 2
    assert "Loop guard" in refused.stderr


def test_a_different_call_in_between_resets_the_count(tmp_path: Path) -> None:
    for command in ["pytest -q", "pytest -q", "git diff", "pytest -q", "pytest -q"]:
        assert call(bash(command), tmp_path).returncode == 0


def test_agents_are_counted_separately(tmp_path: Path) -> None:
    for _ in range(2):
        assert call(bash("pytest -q", "a1"), tmp_path).returncode == 0
        assert call(bash("pytest -q", "a2"), tmp_path).returncode == 0


def test_over_the_call_cap_only_git_is_allowed(tmp_path: Path) -> None:
    for i in range(3):
        assert call(bash(f"echo {i}"), tmp_path, max_calls=3).returncode == 0
    assert call(bash("echo 4"), tmp_path, max_calls=3).returncode == 2
    assert call(bash("git commit -m done"), tmp_path, max_calls=3).returncode == 0


def test_malformed_input_never_blocks(tmp_path: Path) -> None:
    proc = subprocess.run(
        [sys.executable, "-I", str(SCRIPT)],
        input="not json",
        capture_output=True,
        text=True,
        env={"TOISHI_AGENT_GUARD_DIR": str(tmp_path)},
        check=False,
    )
    assert proc.returncode == 0
