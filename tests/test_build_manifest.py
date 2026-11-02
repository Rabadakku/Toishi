"""scripts/build_manifest.py: the build manifest records the bundled SQLite (DEV-7)."""

import importlib.util
import json
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

import core
from core.health import health_check

ROOT = Path(__file__).resolve().parents[1]


def load() -> Any:
    spec = importlib.util.spec_from_file_location(
        "build_manifest", ROOT / "scripts/build_manifest.py"
    )
    assert spec
    assert spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build_manifest = load()
ManifestError = build_manifest.ManifestError
manifest = build_manifest.manifest


def health_line() -> str:
    return "HEALTH " + json.dumps(health_check().as_dict(), sort_keys=True)


def test_manifest_records_the_sqlite_the_app_reports() -> None:
    data = manifest(health_line(), app_version="9.9.9")
    assert data["sqlite"] == sqlite3.sqlite_version
    assert data["app_version"] == "9.9.9"
    assert data["python"] == sys.version.split()[0]


def test_manifest_refuses_a_failed_health_check() -> None:
    report = health_check().as_dict()
    checks = report["checks"]
    assert isinstance(checks, list)
    checks[1] = {**checks[1], "ok": False, "detail": "UnsafeSQLiteError: SQLite 3.51.2 ..."}
    report["ok"] = False
    with pytest.raises(ManifestError, match=r"3\.51\.2"):
        manifest("HEALTH " + json.dumps(report), app_version="1")
    with pytest.raises(ManifestError):
        manifest("not health", app_version="1")


def test_script_writes_the_manifest_file(tmp_path: Path) -> None:
    out = tmp_path / "dist" / "build-manifest.json"
    proc = subprocess.run(
        [sys.executable, "scripts/build_manifest.py", "--out", str(out)],
        cwd=ROOT,
        input="noise\n" + health_line() + "\n",
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    data = json.loads(out.read_text())
    assert data["sqlite"] == sqlite3.sqlite_version
    assert data["app_version"] == core.version()
    bad = subprocess.run(
        [sys.executable, "scripts/build_manifest.py", "--out", str(tmp_path / "x.json")],
        cwd=ROOT,
        input="",
        capture_output=True,
        text=True,
        check=False,
    )
    assert bad.returncode == 1
    assert not (tmp_path / "x.json").exists()
