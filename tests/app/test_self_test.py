"""`python -m app --self-test --no-window`: the bridge and core part of the app's self-test."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]


def test_self_test_studies_through_the_bridge_and_exits_zero(tmp_path: Path) -> None:
    run = subprocess.run(
        [sys.executable, "-m", "app", "--self-test", "--no-window"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=300,
        env={"PATH": "/usr/bin:/bin", "HOME": str(tmp_path), "TOISHI_DATA_DIR": str(tmp_path)},
        check=False,
    )
    lines = [x for x in run.stdout.splitlines() if x.startswith("SELFTEST ")]
    assert len(lines) == 1, run.stdout + run.stderr
    result = json.loads(lines[0].removeprefix("SELFTEST "))
    assert run.returncode == 0, result
    assert result["ok"] is True
    names = [s["name"] for s in result["study"]["steps"]]
    assert names == [
        "profile",
        "pack attached",
        "today",
        "start",
        "correct answer",
        "wrong answer",
        "undo",
        "answered two",
        "summary",
    ]
    assert "page" not in result  # no window in this mode
    assert list(tmp_path.iterdir()) == []  # a temporary data folder, never the real one


def test_self_test_result_needs_the_study_check_too() -> None:
    from app.main import self_test_result

    page = {"ok": True}
    assert self_test_result(page, {"ok": True}, {}, {"ok": True})["ok"] is True
    assert self_test_result(page, {"ok": True}, {}, {"ok": False})["ok"] is False
    assert self_test_result(None, {"ok": True}, {}, {"ok": True}, window=False)["ok"] is True
