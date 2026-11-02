import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]


def load() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "spike_measure", ROOT / "scripts/spike_measure.py"
    )
    assert spec
    assert spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fake_app(tmp_path: Path, ok: bool) -> Path:
    app = tmp_path / "Fake.app"
    macos = app / "Contents" / "MacOS"
    macos.mkdir(parents=True)
    result = {
        "ok": ok,
        "shell": "fake 1.0",
        "page": {"ok": ok},
        "timings": {"launch_to_report_ms": 12.5},
    }
    exe = macos / "Fake"
    exe.write_text(
        f"#!{sys.executable}\nimport json, sys\n"
        f"print('noise')\nprint('SELFTEST ' + json.dumps({result!r}))\nsys.exit({0 if ok else 1})\n"
    )
    exe.chmod(0o755)
    return app


def test_measure_and_report(tmp_path: Path) -> None:
    sm = load()
    good = sm.measure("good", fake_app(tmp_path / "a", ok=True), runs=2)
    bad = sm.measure("bad", fake_app(tmp_path / "b", ok=False), runs=1)
    assert good["passed"]
    assert not bad["passed"]
    assert good["shell"] == "fake 1.0"
    assert good["first_launch_ms"] == 12.5
    assert good["bundle_bytes"] > 0
    report = sm.render([good, bad], sm.machine_info())
    assert "| good | fake 1.0 |" in report
    assert "**FAIL**" in report
    assert "Cmd+Z" in report
    assert "- bad, run 1: exit 1" in report


def test_cli_round_trip(tmp_path: Path) -> None:
    sm = load()
    out = tmp_path / "m.json"
    app = str(fake_app(tmp_path, ok=True))
    assert sm.main(["measure", "--label", "x", "--app", app, "--runs", "1", "--out", str(out)]) == 0
    assert json.loads(out.read_text())["passed"] is True
    report = tmp_path / "r.md"
    assert sm.main(["report", str(out), "--out", str(report)]) == 0
    assert report.read_text().startswith("# M0 shell spike report")


def test_parse_self_test_takes_last_line() -> None:
    sm = load()
    assert sm.parse_self_test('SELFTEST {"ok": false}\nSELFTEST {"ok": true}\n') == {"ok": True}
    assert sm.parse_self_test("nothing here") is None
